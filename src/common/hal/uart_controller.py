"""
Abstração da comunicação serial UART — HAL compartilhado.

 Esta classe NÃO conhece comandos, protocolos ou payload.
  A lógica de protocolo fica em uart_protocols/protocols/.
"""

import serial

from src.common.exceptions import UARTConnectionError, UARTTimeoutError
from src.common.utils.logger import log_info, log_error


class UARTController:
    """
    Controlador de I/O serial UART — agnóstico a protocolo.

    Uso típico:
        uart = UARTController(port="/dev/serial0", baudrate=115200)
        uart.connect()
        uart.send_bytes(b"\\xA1\\x00\\x06\\x02\\x02\\x04\\x00")
        response = uart.read_exact(4)
        uart.disconnect()

    Ou como context manager:
        with UARTController(...) as uart:
            uart.send_bytes(data)
            response = uart.read_exact(4)
    """

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        timeout: float = 0.3,
        parity: str = "N",
        stopbits: int = 1,
        bytesize: int = 8,
    ):
        self._port = port
        self._baudrate = baudrate
        self._timeout = timeout
        self._parity = parity
        self._stopbits = stopbits
        self._bytesize = bytesize
        self._serial: serial.Serial | None = None

    #  Conexão 

    def connect(self) -> None:
        """Abre a porta serial com os parâmetros configurados."""
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                timeout=self._timeout,
                parity=self._parity,
                stopbits=self._stopbits,
                bytesize=self._bytesize,
            )
            self.flush()
            log_info(
                f"UART conectada: {self._port} @ {self._baudrate} baud "
                f"({self._bytesize}{self._parity}{self._stopbits})"
            )
        except serial.SerialException as e:
            raise UARTConnectionError(f"Falha ao abrir {self._port}: {e}") from e

    def disconnect(self) -> None:
        """Fecha a porta serial de forma segura."""
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
                log_info("UART desconectada")
            except serial.SerialException as e:
                log_error(f"Erro ao fechar UART: {e}")
        self._serial = None

    #  Transmissão 

    def send_bytes(self, data: bytes) -> None:
        """Envia bytes crus pela UART e faz flush do buffer de saída."""
        self._ensure_connected()
        self._serial.write(data)
        self._serial.flush()

    #  Recepção 

    def read_exact(self, size: int) -> bytes:
        """
        Lê exatamente `size` bytes da UART.

        Raises:
            UARTTimeoutError: se receber menos bytes que o esperado.
        """
        self._ensure_connected()
        data = self._serial.read(size)
        if len(data) < size:
            raise UARTTimeoutError(f"Esperava {size} bytes, recebeu {len(data)}")
        return data

    def read_until_timeout(self) -> bytes:
        """Lê todos os bytes disponíveis até o timeout."""
        self._ensure_connected()
        data = b""
        while True:
            chunk = self._serial.read(1)
            if not chunk:
                break
            data += chunk
        return data

    #  Buffer 

    def flush(self) -> None:
        """Limpa ambos os buffers (entrada e saída)."""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

    def flush_input(self) -> None:
        """Limpa apenas o buffer de entrada (RX). Chamar antes de cada TX."""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()

    #   Propriedades 

    @property
    def is_connected(self) -> bool:
        return self._serial is not None and self._serial.is_open

    @property
    def port(self) -> str:
        return self._port

    #  Context Manager 

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False

    #  Internos 

    def _ensure_connected(self) -> None:
        if not self.is_connected:
            raise UARTConnectionError("UART não está conectada")

    def __repr__(self) -> str:
        status = "conectada" if self.is_connected else "desconectada"
        return (
            f"UARTController(port={self._port!r}, "
            f"baud={self._baudrate}, status={status})"
        )
