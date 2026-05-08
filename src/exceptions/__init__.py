"""
Exceções customizadas do sistema UART.
"""

from src.exceptions.uart_exceptions import (  # noqa: F401
    UARTError,
    UARTConnectionError,
    UARTTimeoutError,
    ProtocolError,
    InvalidResponseError,
    InvalidPacketError,
    IncompleteResponseError,
    InvalidSizeError,
)
