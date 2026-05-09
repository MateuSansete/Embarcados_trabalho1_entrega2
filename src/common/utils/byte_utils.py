"""
Utilitários de bytes — infraestrutura compartilhada.
"""

import struct


def int32_to_bytes(value: int) -> bytes:
    """Empacota int32 em 4 bytes little-endian."""
    return struct.pack('<i', value)


def bytes_to_int32(data: bytes) -> int:
    """Desempacota 4 bytes little-endian em int32."""
    return struct.unpack('<i', data)[0]


def float_to_bytes(value: float) -> bytes:
    """Empacota float em 4 bytes little-endian (IEEE 754)."""
    return struct.pack('<f', value)


def bytes_to_float(data: bytes) -> float:
    """Desempacota 4 bytes little-endian em float (IEEE 754)."""
    return struct.unpack('<f', data)[0]


def hex_dump(data: bytes) -> str:
    """Retorna string HEX espaçada para visualização."""
    return " ".join(f"{b:02X}" for b in data)
