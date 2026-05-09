"""
CRC-16 MODBUS — implementação manual.

Algoritmo:
    - Polinômio: 0xA001 (reflexão de 0x8005)
    - Valor inicial: 0xFFFF
    - Byte order no frame: little-endian [CRC_LO, CRC_HI]

Escopo do cálculo (frame TX):
    [ADDR][FUNC][SUBCODE][PAYLOAD][MATRICULA_6B]  ← CRC calculado sobre TUDO isso
    [CRC_LO][CRC_HI]                              ← appended ao final

Referência:
    MODBUS over Serial Line — Specification and Implementation Guide V1.02
    Seção 6.2.2 — CRC Generation

⚠ NÃO usa bibliotecas prontas (pymodbus, minimalmodbus).
  Implementação byte-a-byte conforme especificação da disciplina.
"""


def calculate_crc(data: bytes) -> bytes:
    """
    Calcula CRC-16 MODBUS sobre os bytes fornecidos.

    Args:
        data: Todos os bytes antes do CRC
              (endereço + função + subcódigo + payload + matrícula).

    Returns:
        2 bytes do CRC em little-endian [CRC_LO, CRC_HI].
    """
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc >>= 1
                crc ^= 0xA001
            else:
                crc >>= 1
    return crc.to_bytes(2, byteorder="little")


def validate_crc(frame: bytes) -> bool:
    """
    Valida o CRC-16 de um frame MODBUS completo.

    Os últimos 2 bytes do frame são [CRC_LO, CRC_HI].

    Returns:
        True se o CRC calculado coincide com o recebido.
    """
    if len(frame) < 3:
        return False
    return calculate_crc(frame[:-2]) == frame[-2:]
