"""
Utilitários de construção de pacotes binários — Protocolo Simplificado.

Centraliza a montagem de pacotes para evitar duplicação entre
os comandos de solicitação (A1/A2/A3) e envio (B1/B2/B3).
"""

import struct

from src.common.config import MATRICULA, MAX_STRING_LENGTH
from src.common.exceptions import InvalidPacketError, IncompleteResponseError


def build_request_packet(cmd: int) -> bytes:
    """
    Monta pacote de solicitação: [CMD][D1][D2][D3][D4][D5][D6] = 7 bytes.
    """
    return bytes([cmd]) + MATRICULA


def build_send_int_packet(cmd: int, value: int) -> bytes:
    """
    Monta pacote de envio de inteiro: [CMD][INT32_LE][MATRICULA] = 11 bytes.
    """
    return bytes([cmd]) + struct.pack('<i', value) + MATRICULA


def build_send_float_packet(cmd: int, value: float) -> bytes:
    """
    Monta pacote de envio de float: [CMD][FLOAT_LE][MATRICULA] = 11 bytes.
    """
    return bytes([cmd]) + struct.pack('<f', value) + MATRICULA


def build_send_string_packet(cmd: int, value: str) -> bytes:
    """
    Monta pacote de envio de string: [CMD][N][STRING][MATRICULA] = (8+N) bytes.

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


def validate_response_length(data: bytes, expected: int) -> None:
    """
    Valida que a resposta tem o tamanho esperado.

    Raises:
        IncompleteResponseError: se len(data) != expected.
    """
    if len(data) != expected:
        raise IncompleteResponseError(
            f"Resposta incompleta: esperava {expected} bytes, recebeu {len(data)}"
        )
