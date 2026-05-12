"""
Parsers de respostas binárias recebidas da ESP32.

Funções puras que recebem bytes crus e retornam valores decodificados.
Todo o parsing binário fica aqui — main.py e simple_protocol.py
NÃO fazem decodificação direta.
"""

import struct

from src.common.config import MAX_STRING_LENGTH
from src.common.exceptions import IncompleteResponseError, InvalidSizeError


def parse_int32(data: bytes) -> int:
    """
    Decodifica 4 bytes little-endian em int32.

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


#  Parsing MODBUS 


def is_exception_frame(func_byte: int) -> bool:
    """Verifica se o byte de função indica exception frame (MSB = 1)."""
    return bool(func_byte & 0x80)


def parse_modbus_exception(frame: bytes) -> tuple[int, int]:
    """
    Extrai (original_func, exception_code) de um exception frame.

    Formato: [ADDR][FUNC|0x80][EXCEPTION_CODE][CRC_LO][CRC_HI]
    """
    original_func = frame[1] & 0x7F
    exception_code = frame[2]
    return original_func, exception_code


def parse_modbus_payload(frame: bytes, payload_offset: int = 3) -> bytes:
    """
    Extrai o payload de dados de um frame MODBUS (sem header nem CRC).

    Args:
        frame: Frame completo incluindo CRC.
        payload_offset: Índice onde começa o payload (default: 3).
    """
    return frame[payload_offset:-2]
