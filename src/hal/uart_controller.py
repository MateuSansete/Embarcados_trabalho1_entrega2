"""
Abstração da comunicação serial UART para a Raspberry Pi.

Responsabilidades EXCLUSIVAS:
    - Abrir / fechar a porta serial
    - Enviar bytes crus
    - Ler bytes crus (exato ou até timeout)
    - Flush de buffers

⚠ Esta classe NÃO conhece comandos, protocolos ou payload.
   A lógica de protocolo fica em protocols/.
"""

import serial

from src.exceptions import UARTConnectionError, UARTTimeoutError
from src.utils.logger import log_info, log_error


class UARTController:
    """
    Controlador de I/O serial UART — agnóstico a protocolo.

    Uso típico:
        uart = UARTController(port="/dev/serial0", baudrate=115200, ...)
        uart.connect()
        uart.send_bytes(b"\\xA1\\x06\\x05\\x04\\x03\\x02\\x01")
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

    # ─── Conexão ─────────────────────────────────────────────────────────

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
            raise UARTConnectionError(
                f"Falha ao abrir {self._port}: {e}"
            ) from e

    def disconnect(self) -> None:
        """Fecha a porta serial de forma segura."""
        if self._serial and self._serial.is_open:
            try:
                self._serial.close()
                log_info("UART desconectada")
            except serial.SerialException as e:
                log_error(f"Erro ao fechar UART: {e}")
        self._serial = None

    # ─── Transmissão ─────────────────────────────────────────────────────

    def send_bytes(self, data: bytes) -> None:
        """
        Envia bytes crus pela UART e faz flush do buffer de saída.

        Raises:
            UARTConnectionError: se a porta não estiver aberta.
        """
        self._ensure_connected()
        self._serial.write(data)
        self._serial.flush()

    # ─── Recepção ────────────────────────────────────────────────────────

    def read_exact(self, size: int) -> bytes:
        """
        Lê exatamente `size` bytes da UART.

        Se o timeout expirar antes de completar a leitura,
        levanta UARTTimeoutError informando quantos bytes chegaram.

        Raises:
            UARTConnectionError: se a porta não estiver aberta.
            UARTTimeoutError: se receber menos bytes que o esperado.
        """
        self._ensure_connected()
        data = self._serial.read(size)
        if len(data) < size:
            raise UARTTimeoutError(
                f"Esperava {size} bytes, recebeu {len(data)}"
            )
        return data

    def read_until_timeout(self) -> bytes:
        """
        Lê todos os bytes disponíveis até o timeout.

        Útil para drenar o buffer ou ler respostas de tamanho desconhecido.

        Returns:
            Bytes lidos (pode ser b'' se nada disponível).
        """
        self._ensure_connected()
        data = b""
        while True:
            chunk = self._serial.read(1)
            if not chunk:
                break
            data += chunk
        return data

    # ─── Buffer ──────────────────────────────────────────────────────────

    def flush(self) -> None:
        """Limpa ambos os buffers (entrada e saída)."""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
            self._serial.reset_output_buffer()

    def flush_input(self) -> None:
        """
        Limpa apenas o buffer de entrada (RX).

        ⚠ Deve ser chamado ANTES de cada transmissão para evitar
          lixo residual de leituras anteriores.
        """
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()

    # ─── Propriedades ────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        """Retorna True se a porta serial estiver aberta."""
        return self._serial is not None and self._serial.is_open

    @property
    def port(self) -> str:
        """Retorna o nome da porta configurada."""
        return self._port

    # ─── Context Manager ─────────────────────────────────────────────────

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()
        return False

    # ─── Internos ────────────────────────────────────────────────────────

    def _ensure_connected(self) -> None:
        """Verifica se a UART está conectada antes de I/O."""
        if not self.is_connected:
            raise UARTConnectionError("UART não está conectada")

    def __repr__(self) -> str:
        status = "conectada" if self.is_connected else "desconectada"
        return (
            f"UARTController(port={self._port!r}, "
            f"baud={self._baudrate}, status={status})"
        )
