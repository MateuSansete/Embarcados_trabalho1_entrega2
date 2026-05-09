"""
Exceções customizadas — Infraestrutura compartilhada.

Hierarquia:
    UARTError (base I/O serial)
    ├── UARTConnectionError  — falha ao abrir/fechar porta
    └── UARTTimeoutError     — timeout na leitura

    ProtocolError (base lógica de protocolo)
    ├── InvalidResponseError
    ├── InvalidPacketError
    ├── IncompleteResponseError
    ├── InvalidSizeError
    └── ModbusError
        ├── ModbusCRCError
        ├── ModbusExceptionResponse
        └── InvalidFunctionCode
"""


# ─── Erros de I/O Serial ────────────────────────────────────────────────────


class UARTError(Exception):
    """Erro base para operações de I/O serial."""
    pass


class UARTConnectionError(UARTError):
    """Falha ao abrir ou fechar a porta serial."""
    pass


class UARTTimeoutError(UARTError):
    """Timeout aguardando resposta da UART."""
    pass


# ─── Erros de Protocolo ─────────────────────────────────────────────────────


class ProtocolError(Exception):
    """Erro base para lógica de protocolo (empacotamento/parsing)."""
    pass


class InvalidResponseError(ProtocolError):
    """Resposta recebida não corresponde ao formato esperado."""
    pass


class InvalidPacketError(ProtocolError):
    """Falha na construção ou validação de um pacote."""
    pass


class IncompleteResponseError(ProtocolError):
    """Número de bytes recebidos é menor que o esperado."""
    pass


class InvalidSizeError(ProtocolError):
    """Campo de tamanho está fora do range válido (0 ou > MAX)."""
    pass


# ─── Erros MODBUS ───────────────────────────────────────────────────────────


class ModbusError(ProtocolError):
    """Erro base para lógica do protocolo MODBUS."""
    pass


class ModbusCRCError(ModbusError):
    """CRC-16 inválido no frame recebido."""
    pass


class ModbusExceptionResponse(ModbusError):
    """Servidor retornou exception frame (FUNC | 0x80)."""

    def __init__(
        self,
        function_code: int,
        exception_code: int,
        message: str = "",
    ):
        self.function_code = function_code
        self.exception_code = exception_code
        super().__init__(
            message
            or f"Exception MODBUS: func=0x{function_code:02X}, "
               f"code=0x{exception_code:02X}"
        )


class InvalidFunctionCode(ModbusError):
    """Código de função recebido não corresponde ao esperado."""
    pass
