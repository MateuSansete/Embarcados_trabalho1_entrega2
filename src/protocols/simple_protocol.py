"""
Protocolo Simplificado UART — Parte 1 da Entrega 2.

Implementa os 6 comandos de comunicação com a ESP32:

    Solicitação:
        0xA1 — request_integer()   → int32
        0xA2 — request_float()     → float
        0xA3 — request_string()    → str

    Envio:
        0xB1 — send_integer(value) → int32 (resposta)
        0xB2 — send_float(value)   → float (resposta)
        0xB3 — send_string(value)  → str   (resposta)

Cada função:
    1. Monta o pacote via packet_utils
    2. Faz flush_input() para limpar lixo residual
    3. Loga TX
    4. Envia via UARTController
    5. Lê resposta (read_exact para tamanho fixo; dois reads para string)
    6. Loga RX
    7. Decodifica via parsers
    8. Retorna valor tipado

Todas as funções possuem retry automático configurável.
"""

import time

from src.config import (
    CMD_REQUEST_INT,
    CMD_REQUEST_FLOAT,
    CMD_REQUEST_STRING,
    CMD_SEND_INT,
    CMD_SEND_FLOAT,
    CMD_SEND_STRING,
    MAX_STRING_LENGTH,
    RETRY_COUNT,
    RETRY_DELAY,
)
from src.protocols.packet_utils import (
    build_request_packet,
    build_send_int_packet,
    build_send_float_packet,
    build_send_string_packet,
)
from src.protocols.parsers import parse_int32, parse_float, parse_string_response
from src.utils.logger import log_tx, log_rx, log_info, log_error, log_warning
from src.exceptions import (
    UARTTimeoutError,
    ProtocolError,
    InvalidSizeError,
)

PROTOCOL_NAME = "SIMPLE"


# ─── Retry ───────────────────────────────────────────────────────────────────


def _execute_with_retry(func, retry_count: int = RETRY_COUNT):
    """
    Executa uma operação UART com retry automático.

    Re-tenta em caso de UARTTimeoutError ou ProtocolError.
    Outros erros (ex: UARTConnectionError) propagam imediatamente.

    Args:
        func: Callable sem argumentos que executa o comando.
        retry_count: Número máximo de tentativas.

    Returns:
        Resultado da função em caso de sucesso.

    Raises:
        A última exceção capturada se todas as tentativas falharem.
    """
    last_error = None
    for attempt in range(1, retry_count + 1):
        try:
            return func()
        except (UARTTimeoutError, ProtocolError) as e:
            last_error = e
            if attempt < retry_count:
                log_warning(
                    f"Tentativa {attempt}/{retry_count} falhou: {e} — "
                    f"retentando em {RETRY_DELAY}s..."
                )
                time.sleep(RETRY_DELAY)
            else:
                log_error(f"Todas as {retry_count} tentativas falharam: {e}")
    raise last_error


# ─── Comandos de Solicitação ─────────────────────────────────────────────────


def request_integer(uart) -> int:
    """
    0xA1 — Solicita inteiro da ESP32.

    TX: [0xA1][matrícula 6 bytes] = 7 bytes
    RX: [int32 LE] = 4 bytes

    Returns:
        Valor inteiro de 32 bits recebido.
    """
    def _do():
        packet = build_request_packet(CMD_REQUEST_INT)
        uart.flush_input()
        log_tx(packet, PROTOCOL_NAME)
        uart.send_bytes(packet)

        response = uart.read_exact(4)
        log_rx(response, PROTOCOL_NAME)

        value = parse_int32(response)
        log_info(f"Inteiro recebido: {value}")
        return value

    return _execute_with_retry(_do)


def request_float(uart) -> float:
    """
    0xA2 — Solicita float da ESP32.

    TX: [0xA2][matrícula 6 bytes] = 7 bytes
    RX: [float LE] = 4 bytes

    Returns:
        Valor float recebido.
    """
    def _do():
        packet = build_request_packet(CMD_REQUEST_FLOAT)
        uart.flush_input()
        log_tx(packet, PROTOCOL_NAME)
        uart.send_bytes(packet)

        response = uart.read_exact(4)
        log_rx(response, PROTOCOL_NAME)

        value = parse_float(response)
        log_info(f"Float recebido: {value:.6f}")
        return value

    return _execute_with_retry(_do)


def request_string(uart) -> str:
    """
    0xA3 — Solicita string da ESP32.

    TX: [0xA3][matrícula 6 bytes] = 7 bytes
    RX: [N: 1 byte][string: N bytes]

    Leitura em dois estágios para evitar race condition:
        1. read_exact(1) — tamanho N
        2. read_exact(N) — conteúdo da string

    Returns:
        String UTF-8 recebida.
    """
    def _do():
        packet = build_request_packet(CMD_REQUEST_STRING)
        uart.flush_input()
        log_tx(packet, PROTOCOL_NAME)
        uart.send_bytes(packet)

        # Leitura em dois estágios (tamanho + conteúdo)
        size_data = uart.read_exact(1)
        size = size_data[0]

        if size == 0 or size > MAX_STRING_LENGTH:
            raise InvalidSizeError(
                f"Tamanho da string inválido: {size}"
            )

        string_data = uart.read_exact(size)
        full_response = size_data + string_data
        log_rx(full_response, PROTOCOL_NAME)

        value = parse_string_response(size_data, string_data)
        log_info(f"String recebida ({size} bytes): \"{value}\"")
        return value

    return _execute_with_retry(_do)


# ─── Comandos de Envio ───────────────────────────────────────────────────────


def send_integer(uart, value: int) -> int:
    """
    0xB1 — Envia inteiro para a ESP32.

    TX: [0xB1][int32 LE: 4 bytes][matrícula: 6 bytes] = 11 bytes
    RX: [int32 LE] = 4 bytes (valor * último dígito da matrícula)

    Args:
        uart: Instância de UARTController.
        value: Inteiro a enviar.

    Returns:
        Inteiro recebido como resposta.
    """
    def _do():
        packet = build_send_int_packet(CMD_SEND_INT, value)
        uart.flush_input()
        log_tx(packet, PROTOCOL_NAME)
        uart.send_bytes(packet)

        response = uart.read_exact(4)
        log_rx(response, PROTOCOL_NAME)

        result = parse_int32(response)
        log_info(f"Inteiro enviado: {value} → Resposta: {result}")
        return result

    return _execute_with_retry(_do)


def send_float(uart, value: float) -> float:
    """
    0xB2 — Envia float para a ESP32.

    TX: [0xB2][float LE: 4 bytes][matrícula: 6 bytes] = 11 bytes
    RX: [float LE] = 4 bytes (valor * último dígito da matrícula)

    Args:
        uart: Instância de UARTController.
        value: Float a enviar.

    Returns:
        Float recebido como resposta.
    """
    def _do():
        packet = build_send_float_packet(CMD_SEND_FLOAT, value)
        uart.flush_input()
        log_tx(packet, PROTOCOL_NAME)
        uart.send_bytes(packet)

        response = uart.read_exact(4)
        log_rx(response, PROTOCOL_NAME)

        result = parse_float(response)
        log_info(f"Float enviado: {value:.6f} → Resposta: {result:.6f}")
        return result

    return _execute_with_retry(_do)


def send_string(uart, value: str) -> str:
    """
    0xB3 — Envia string para a ESP32.

    TX: [0xB3][N: 1 byte][string: N bytes][matrícula: 6 bytes] = (8+N) bytes
    RX: [N: 1 byte][string: N bytes] ("Resposta da UART: " + string_enviada)

    Leitura da resposta em dois estágios (tamanho + conteúdo).

    Args:
        uart: Instância de UARTController.
        value: String a enviar (UTF-8).

    Returns:
        String recebida como resposta.
    """
    def _do():
        packet = build_send_string_packet(CMD_SEND_STRING, value)
        uart.flush_input()
        log_tx(packet, PROTOCOL_NAME)
        uart.send_bytes(packet)

        # Leitura em dois estágios (tamanho + conteúdo)
        size_data = uart.read_exact(1)
        size = size_data[0]

        if size == 0 or size > MAX_STRING_LENGTH:
            raise InvalidSizeError(
                f"Tamanho da resposta inválido: {size}"
            )

        string_data = uart.read_exact(size)
        full_response = size_data + string_data
        log_rx(full_response, PROTOCOL_NAME)

        result = parse_string_response(size_data, string_data)
        log_info(f"String enviada: \"{value}\" → Resposta ({size} bytes): \"{result}\"")
        return result

    return _execute_with_retry(_do)
