"""
Protocolo MODBUS RTU Modificado — Parte 2 da Entrega 2.

Frame TX: [ADDR][FUNC][SUBCODE][PAYLOAD][MATRICULA_6B][CRC_LO][CRC_HI]
Frame RX: [ADDR][FUNC][SUBCODE][DADOS][CRC_LO][CRC_HI]
Exception: [ADDR][FUNC|0x80][EXCEPTION_CODE][CRC_LO][CRC_HI]

Matrícula: bytes([0, 6, 2, 2, 4, 0])  -  062240
CRC-16: polinômio 0xA001, init 0xFFFF, little-endian no frame.

"""

import struct
import time

from src.common.config import (
    MATRICULA,
    MAX_STRING_LENGTH,
    MODBUS_DEFAULT_SLAVE_ADDR,
    MODBUS_FUNC_READ,
    MODBUS_FUNC_WRITE,
    MODBUS_SUB_REQUEST_INT,
    MODBUS_SUB_REQUEST_FLOAT,
    MODBUS_SUB_REQUEST_STRING,
    MODBUS_SUB_SEND_INT,
    MODBUS_SUB_SEND_FLOAT,
    MODBUS_SUB_SEND_STRING,
    MODBUS_RETRY_COUNT,
    MODBUS_RETRY_DELAY,
)
from src.uart_protocols.protocols.crc_utils import calculate_crc, validate_crc
from src.uart_protocols.protocols.parsers import (
    parse_int32,
    parse_float,
    parse_string_response,
)
from src.common.utils.logger import log_tx, log_rx, log_info, log_error, log_warning
from src.common.exceptions import (
    UARTTimeoutError,
    ProtocolError,
    ModbusCRCError,
    ModbusExceptionResponse,
    InvalidFunctionCode,
    InvalidSizeError,
    InvalidPacketError,
)

PROTOCOL_NAME = "MODBUS"


#  Enumerações de endereços, funções e sub-códigos


class SlaveAddresses:
    """
    Endereços de slaves no barramento RS485.

    Para comunicação ponto-a-ponto, DEFAULT (0x01).
    Preparado para múltiplos dispositivos no sistema final.
    """
    DEFAULT   = 0x01
    BROADCAST = 0x00


class ModbusFunctionCodes:
    """
    Códigos de função MODBUS.

    READ/WRITE são os códigos acadêmicos da disciplina.
    READ_HOLDING/WRITE_MULTIPLE são funções MODBUS padrão reservadas.
    """
    READ  = 0x23
    WRITE = 0x16
    READ_HOLDING_REGISTERS   = 0x03
    WRITE_MULTIPLE_REGISTERS = 0x10


class ModbusSubCodes:
    """Sub-códigos que definem o tipo de dado no protocolo acadêmico."""
    REQUEST_INT    = 0xA1
    REQUEST_FLOAT  = 0xA2
    REQUEST_STRING = 0xA3
    SEND_INT       = 0xB1
    SEND_FLOAT     = 0xB2
    SEND_STRING    = 0xB3


#  Construção de frames TX


def _build_frame(addr: int, func: int, subcode: int, payload: bytes = b"") -> bytes:
    """
    Monta frame MODBUS completo com matrícula e CRC.

    Formato: [ADDR][FUNC][SUBCODE][PAYLOAD][MATRICULA_6B][CRC_LO][CRC_HI]
    """
    body = bytes([addr, func, subcode]) + payload + MATRICULA
    crc = calculate_crc(body)
    return body + crc


def build_modbus_request_frame(addr: int, func: int, subcode: int) -> bytes:
    """Frame de solicitação: [ADDR][FUNC][SUB][MAT][CRC] = 11 bytes."""
    return _build_frame(addr, func, subcode)


def build_modbus_send_int_frame(addr: int, func: int, subcode: int, value: int) -> bytes:
    """Frame de envio de inteiro: 15 bytes."""
    return _build_frame(addr, func, subcode, struct.pack('<i', value))


def build_modbus_send_float_frame(addr: int, func: int, subcode: int, value: float) -> bytes:
    """Frame de envio de float: 15 bytes."""
    return _build_frame(addr, func, subcode, struct.pack('<f', value))


def build_modbus_send_string_frame(addr: int, func: int, subcode: int, text: str) -> bytes:
    """
    Frame de envio de string: (12+N) bytes.

    Raises:
        InvalidPacketError: se a string for vazia ou exceder MAX_STRING_LENGTH.
    """
    encoded = text.encode('utf-8')
    if len(encoded) == 0:
        raise InvalidPacketError("String não pode ser vazia")
    if len(encoded) > MAX_STRING_LENGTH:
        raise InvalidPacketError(
            f"String muito longa: {len(encoded)} bytes (máx {MAX_STRING_LENGTH})"
        )
    return _build_frame(addr, func, subcode, bytes([len(encoded)]) + encoded)



#  Parsing de frames RX


def _validate_modbus_response(frame: bytes, expected_func: int) -> None:
    """
    Valida um frame de resposta MODBUS completo.

    Verificações: 1. CRC-16 | 2. Exception frame | 3. Código de função.

    Raises:
        ModbusCRCError, ModbusExceptionResponse, InvalidFunctionCode
    """
    if not validate_crc(frame):
        raise ModbusCRCError(
            f"CRC inválido no frame de {len(frame)} bytes: "
            f"{' '.join(f'{b:02X}' for b in frame)}"
        )
    func_byte = frame[1]
    if func_byte & 0x80:
        original_func = func_byte & 0x7F
        exception_code = frame[2] if len(frame) > 2 else 0x00
        raise ModbusExceptionResponse(original_func, exception_code)
    if func_byte != expected_func:
        raise InvalidFunctionCode(
            f"Função esperada: 0x{expected_func:02X}, "
            f"recebida: 0x{func_byte:02X}"
        )


def _read_fixed_response(uart, expected_size: int) -> bytes:
    """Lê resposta MODBUS de tamanho fixo."""
    return uart.read_exact(expected_size)


def _read_string_response(uart) -> bytes:
    """
    Lê resposta MODBUS de string em estágios:
        1. Header [ADDR][FUNC][SUB] = 3 bytes
        2. Comprimento [LEN] = 1 byte
        3. String + CRC = N+2 bytes
    """
    header = uart.read_exact(3)
    func_byte = header[1]
    if func_byte & 0x80:
        return header + uart.read_exact(2)
    len_byte = uart.read_exact(1)
    str_len = len_byte[0]
    if str_len == 0 or str_len > MAX_STRING_LENGTH:
        raise InvalidSizeError(
            f"Tamanho da string inválido na resposta MODBUS: {str_len}"
        )
    remaining = uart.read_exact(str_len + 2)
    return header + len_byte + remaining



#  Retry


def _execute_with_retry(
    func,
    retry_count: int = MODBUS_RETRY_COUNT,
    retry_delay: float = MODBUS_RETRY_DELAY,
):
    """
    Executa operação MODBUS com retry automático.

    Re-tenta em caso de UARTTimeoutError, ModbusCRCError ou ProtocolError.
    """
    last_error = None
    for attempt in range(1, retry_count + 1):
        try:
            return func()
        except (UARTTimeoutError, ModbusCRCError, ProtocolError) as e:
            last_error = e
            if attempt < retry_count:
                log_warning(
                    f"[MODBUS] Tentativa {attempt}/{retry_count} falhou: {e} "
                    f"— retentando em {retry_delay}s..."
                )
                time.sleep(retry_delay)
            else:
                log_error(
                    f"[MODBUS] Todas as {retry_count} tentativas falharam: {e}"
                )
    raise last_error


#  Comandos de Solicitação (0x23)


def modbus_request_integer(uart, addr: int = MODBUS_DEFAULT_SLAVE_ADDR) -> int:
    """
    0x23/0xA1 — Solicita inteiro via MODBUS.

    TX: [ADDR][0x23][0xA1][MAT_6B][CRC] = 11 bytes
    RX: [ADDR][0x23][0xA1][INT32_LE][CRC] = 9 bytes
    """
    def _do():
        frame = build_modbus_request_frame(
            addr, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_INT,
        )
        uart.flush_input()
        log_tx(frame, PROTOCOL_NAME)
        uart.send_bytes(frame)
        response = _read_fixed_response(uart, 9)
        log_rx(response, PROTOCOL_NAME)
        _validate_modbus_response(response, ModbusFunctionCodes.READ)
        value = parse_int32(response[3:7])
        log_info(f"[MODBUS] Inteiro recebido: {value}")
        log_info(f"[MODBUS] CRC válido ✓")
        return value
    return _execute_with_retry(_do)


def modbus_request_float(uart, addr: int = MODBUS_DEFAULT_SLAVE_ADDR) -> float:
    """
    0x23/0xA2 — Solicita float via MODBUS.

    TX: 11 bytes | RX: 9 bytes
    """
    def _do():
        frame = build_modbus_request_frame(
            addr, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_FLOAT,
        )
        uart.flush_input()
        log_tx(frame, PROTOCOL_NAME)
        uart.send_bytes(frame)
        response = _read_fixed_response(uart, 9)
        log_rx(response, PROTOCOL_NAME)
        _validate_modbus_response(response, ModbusFunctionCodes.READ)
        value = parse_float(response[3:7])
        log_info(f"[MODBUS] Float recebido: {value:.6f}")
        log_info(f"[MODBUS] CRC válido ✓")
        return value
    return _execute_with_retry(_do)


def modbus_request_string(uart, addr: int = MODBUS_DEFAULT_SLAVE_ADDR) -> str:
    """
    0x23/0xA3 — Solicita string via MODBUS.

    TX: 11 bytes | RX: [ADDR][FUNC][SUB][LEN][STRING][CRC] = (6+N) bytes
    """
    def _do():
        frame = build_modbus_request_frame(
            addr, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_STRING,
        )
        uart.flush_input()
        log_tx(frame, PROTOCOL_NAME)
        uart.send_bytes(frame)
        response = _read_string_response(uart)
        log_rx(response, PROTOCOL_NAME)
        _validate_modbus_response(response, ModbusFunctionCodes.READ)
        size_byte = response[3:4]
        size = size_byte[0]
        string_data = response[4:4 + size]
        value = parse_string_response(size_byte, string_data)
        log_info(f"[MODBUS] String recebida ({size} bytes): \"{value}\"")
        log_info(f"[MODBUS] CRC válido ✓")
        return value
    return _execute_with_retry(_do)


#  Comandos de Envio (0x16)


def modbus_send_integer(uart, value: int, addr: int = MODBUS_DEFAULT_SLAVE_ADDR) -> int:
    """
    0x16/0xB1 — Envia inteiro via MODBUS.

    TX: [ADDR][0x16][0xB1][INT32_LE][MAT_6B][CRC] = 15 bytes
    RX: [ADDR][0x16][0xB1][INT32_LE][CRC] = 9 bytes
    """
    def _do():
        frame = build_modbus_send_int_frame(
            addr, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_INT, value,
        )
        uart.flush_input()
        log_tx(frame, PROTOCOL_NAME)
        uart.send_bytes(frame)
        response = _read_fixed_response(uart, 9)
        log_rx(response, PROTOCOL_NAME)
        _validate_modbus_response(response, ModbusFunctionCodes.WRITE)
        result = parse_int32(response[3:7])
        log_info(f"[MODBUS] Inteiro enviado: {value} → Resposta: {result}")
        log_info(f"[MODBUS] CRC válido ✓")
        return result
    return _execute_with_retry(_do)


def modbus_send_float(uart, value: float, addr: int = MODBUS_DEFAULT_SLAVE_ADDR) -> float:
    """
    0x16/0xB2 — Envia float via MODBUS.

    TX: 15 bytes | RX: 9 bytes
    """
    def _do():
        frame = build_modbus_send_float_frame(
            addr, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_FLOAT, value,
        )
        uart.flush_input()
        log_tx(frame, PROTOCOL_NAME)
        uart.send_bytes(frame)
        response = _read_fixed_response(uart, 9)
        log_rx(response, PROTOCOL_NAME)
        _validate_modbus_response(response, ModbusFunctionCodes.WRITE)
        result = parse_float(response[3:7])
        log_info(f"[MODBUS] Float enviado: {value:.6f} → Resposta: {result:.6f}")
        log_info(f"[MODBUS] CRC válido ✓")
        return result
    return _execute_with_retry(_do)


def modbus_send_string(uart, value: str, addr: int = MODBUS_DEFAULT_SLAVE_ADDR) -> str:
    """
    0x16/0xB3 — Envia string via MODBUS.

    TX: (12+N) bytes | RX: (6+M) bytes
    """
    def _do():
        frame = build_modbus_send_string_frame(
            addr, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_STRING, value,
        )
        uart.flush_input()
        log_tx(frame, PROTOCOL_NAME)
        uart.send_bytes(frame)
        response = _read_string_response(uart)
        log_rx(response, PROTOCOL_NAME)
        _validate_modbus_response(response, ModbusFunctionCodes.WRITE)
        size_byte = response[3:4]
        size = size_byte[0]
        string_data = response[4:4 + size]
        result = parse_string_response(size_byte, string_data)
        log_info(
            f"[MODBUS] String enviada: \"{value}\" → "
            f"Resposta ({size} bytes): \"{result}\""
        )
        log_info(f"[MODBUS] CRC válido ✓")
        return result
    return _execute_with_retry(_do)
