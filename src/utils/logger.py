"""
Logger hexadecimal para comunicação UART.

Formata bytes TX/RX com timestamps e identificação do protocolo,
facilitando debug visual no terminal e na gravação do vídeo de entrega.

Formato de saída:
    [HH:MM:SS.mmm][TX][SIMPLE] A1 06 05 04 03 02 01
    [HH:MM:SS.mmm][RX][SIMPLE] 03 A4 00 00
    [HH:MM:SS.mmm][INFO] Inteiro recebido: 41987
"""

import datetime


def _timestamp() -> str:
    """Retorna timestamp formatado com milissegundos."""
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


def _hex_format(data: bytes) -> str:
    """Converte bytes para string HEX espaçada (ex: 'A1 06 05')."""
    return " ".join(f"{b:02X}" for b in data)


def log_tx(data: bytes, protocol: str = "SIMPLE") -> None:
    """Loga bytes transmitidos (TX) com protocolo e timestamp."""
    ts = _timestamp()
    hex_str = _hex_format(data)
    print(f"[{ts}][TX][{protocol}] {hex_str}", flush=True)


def log_rx(data: bytes, protocol: str = "SIMPLE") -> None:
    """Loga bytes recebidos (RX) com protocolo e timestamp."""
    ts = _timestamp()
    hex_str = _hex_format(data)
    print(f"[{ts}][RX][{protocol}] {hex_str}", flush=True)


def log_info(msg: str) -> None:
    """Loga mensagem informativa."""
    ts = _timestamp()
    print(f"[{ts}][INFO] {msg}", flush=True)


def log_error(msg: str) -> None:
    """Loga mensagem de erro."""
    ts = _timestamp()
    print(f"[{ts}][ERROR] {msg}", flush=True)


def log_warning(msg: str) -> None:
    """Loga mensagem de aviso."""
    ts = _timestamp()
    print(f"[{ts}][WARN] {msg}", flush=True)
