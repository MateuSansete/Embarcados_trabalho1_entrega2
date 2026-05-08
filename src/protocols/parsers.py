"""
Parsers de respostas binárias recebidas da ESP32.

Funções puras que recebem bytes crus e retornam valores decodificados.
Todo o parsing binário fica aqui — main.py e simple_protocol.py
NÃO fazem decodificação direta.

Na Parte 2 (MODBUS), este módulo será estendido com funções
para extrair campos do frame MODBUS (endereço, função, CRC).
"""

import struct

from src.config import MAX_STRING_LENGTH
from src.exceptions import IncompleteResponseError, InvalidSizeError


def parse_int32(data: bytes) -> int:
    """
    Decodifica 4 bytes little-endian em int32.

    Args:
        data: Exatamente 4 bytes.

    Returns:
        Valor inteiro de 32 bits com sinal.

    Raises:
        IncompleteResponseError: se len(data) != 4.
    """
    if len(data) != 4:
        raise IncompleteResponseError(
            f"Int32 requer 4 bytes, recebeu {len(data)}"
        )
    return struct.unpack('<i', data)[0]


def parse_float(data: bytes) -> float:
    """
    Decodifica 4 bytes little-endian em float (IEEE 754).

    Args:
        data: Exatamente 4 bytes.

    Returns:
        Valor float de precisão simples.

    Raises:
        IncompleteResponseError: se len(data) != 4.
    """
    if len(data) != 4:
        raise IncompleteResponseError(
            f"Float requer 4 bytes, recebeu {len(data)}"
        )
    return struct.unpack('<f', data)[0]


def parse_string_response(size_byte: bytes, string_data: bytes) -> str:
    """
    Decodifica resposta de string: valida tamanho e decodifica UTF-8.

    Args:
        size_byte: 1 byte contendo o tamanho N.
        string_data: N bytes da string.

    Returns:
        String decodificada em UTF-8.

    Raises:
        InvalidSizeError: se tamanho for 0 ou > MAX_STRING_LENGTH.
        IncompleteResponseError: se len(string_data) != N.
    """
    size = size_byte[0]

    if size == 0 or size > MAX_STRING_LENGTH:
        raise InvalidSizeError(
            f"Tamanho da string inválido: {size} (esperado 1–{MAX_STRING_LENGTH})"
        )

    if len(string_data) != size:
        raise IncompleteResponseError(
            f"String incompleta: esperava {size} bytes, recebeu {len(string_data)}"
        )

    return string_data.decode('utf-8')
