"""
Utilitários de construção e validação de pacotes binários.

Centraliza a montagem de pacotes para evitar duplicação entre
os comandos de solicitação (A1/A2/A3) e envio (B1/B2/B3).

Na Parte 2 (MODBUS), este módulo será estendido com funções
para adicionar endereço, código de função e CRC-16.
"""

import struct

from src.config import MATRICULA, MAX_STRING_LENGTH
from src.exceptions import InvalidPacketError


# ─── Pacotes de Solicitação (Request) ────────────────────────────────────────


def build_request_packet(cmd: int) -> bytes:
    """
    Monta pacote de solicitação: [CMD][D1][D2][D3][D4][D5][D6]

    Todos os comandos 0xA1, 0xA2 e 0xA3 usam o mesmo formato.

    Args:
        cmd: Byte de comando (0xA1, 0xA2 ou 0xA3).

    Returns:
        Pacote de 7 bytes pronto para envio.
    """
    return bytes([cmd]) + MATRICULA


# ─── Pacotes de Envio (Send) ────────────────────────────────────────────────


def build_send_int_packet(cmd: int, value: int) -> bytes:
    """
    Monta pacote de envio de inteiro: [CMD][INT32_LE][MATRICULA]

    Args:
        cmd: Byte de comando (0xB1).
        value: Inteiro a enviar (int32).

    Returns:
        Pacote de 11 bytes pronto para envio.
    """
    payload = struct.pack('<i', value)
    return bytes([cmd]) + payload + MATRICULA


def build_send_float_packet(cmd: int, value: float) -> bytes:
    """
    Monta pacote de envio de float: [CMD][FLOAT_LE][MATRICULA]

    Args:
        cmd: Byte de comando (0xB2).
        value: Float a enviar.

    Returns:
        Pacote de 11 bytes pronto para envio.
    """
    payload = struct.pack('<f', value)
    return bytes([cmd]) + payload + MATRICULA


def build_send_string_packet(cmd: int, value: str) -> bytes:
    """
    Monta pacote de envio de string: [CMD][N][STRING][MATRICULA]

    Args:
        cmd: Byte de comando (0xB3).
        value: String a enviar (UTF-8).

    Returns:
        Pacote de (8 + N) bytes pronto para envio.

    Raises:
        InvalidPacketError: se a string for vazia ou exceder MAX_STRING_LENGTH.
    """
    encoded = value.encode('utf-8')

    if len(encoded) == 0:
        raise InvalidPacketError("String não pode ser vazia")

    if len(encoded) > MAX_STRING_LENGTH:
        raise InvalidPacketError(
            f"String muito longa: {len(encoded)} bytes (máx {MAX_STRING_LENGTH})"
        )

    return bytes([cmd, len(encoded)]) + encoded + MATRICULA


# ─── Validação ───────────────────────────────────────────────────────────────


def validate_response_length(data: bytes, expected: int) -> None:
    """
    Valida que a resposta tem o tamanho esperado.

    Raises:
        IncompleteResponseError: se len(data) != expected.
    """
    from src.exceptions import IncompleteResponseError

    if len(data) != expected:
        raise IncompleteResponseError(
            f"Resposta incompleta: esperava {expected} bytes, recebeu {len(data)}"
        )
