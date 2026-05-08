"""
Exceções customizadas para comunicação UART e protocolo serial.

Hierarquia:
    UARTError (base I/O serial)
    ├── UARTConnectionError  — falha ao abrir/fechar porta
    └── UARTTimeoutError     — timeout na leitura

    ProtocolError (base lógica de protocolo)
    ├── InvalidResponseError    — resposta fora do formato esperado
    ├── InvalidPacketError      — pacote mal formado na construção
    ├── IncompleteResponseError — menos bytes que o esperado
    └── InvalidSizeError        — campo de tamanho fora do range válido
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
