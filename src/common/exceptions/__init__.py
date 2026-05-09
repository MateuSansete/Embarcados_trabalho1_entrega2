"""
Exceções do projeto — infraestrutura compartilhada.
"""

from src.common.exceptions.uart_exceptions import (  # noqa: F401
    UARTError,
    UARTConnectionError,
    UARTTimeoutError,
    ProtocolError,
    InvalidResponseError,
    InvalidPacketError,
    IncompleteResponseError,
    InvalidSizeError,
    ModbusError,
    ModbusCRCError,
    ModbusExceptionResponse,
    InvalidFunctionCode,
)
