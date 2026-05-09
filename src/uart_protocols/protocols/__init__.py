"""
Protocolos de comunicação UART — Entrega 2.
"""

from src.uart_protocols.protocols.simple_protocol import (  # noqa: F401
    request_integer, request_float, request_string,
    send_integer, send_float, send_string,
)
from src.uart_protocols.protocols.modbus_protocol import (  # noqa: F401
    modbus_request_integer, modbus_request_float, modbus_request_string,
    modbus_send_integer, modbus_send_float, modbus_send_string,
    SlaveAddresses, ModbusFunctionCodes, ModbusSubCodes,
    build_modbus_request_frame, build_modbus_send_int_frame,
    build_modbus_send_float_frame, build_modbus_send_string_frame,
    _validate_modbus_response,
)
from src.uart_protocols.protocols.crc_utils import (  # noqa: F401
    calculate_crc, validate_crc,
)
