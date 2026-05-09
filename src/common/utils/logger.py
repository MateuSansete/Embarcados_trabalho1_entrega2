"""
Logger hexadecimal — infraestrutura compartilhada.

Formato:
    [HH:MM:SS.mmm][TX][SIMPLE] A1 06 05 04 03 02 01
    [HH:MM:SS.mmm][RX][MODBUS] 01 23 A1 ...
    [HH:MM:SS.mmm][INFO] Inteiro recebido: 41987
"""

import datetime


def _timestamp() -> str:
    now = datetime.datetime.now()
    return now.strftime("%H:%M:%S.") + f"{now.microsecond // 1000:03d}"


def _hex_format(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def log_tx(data: bytes, protocol: str = "SIMPLE") -> None:
    """Loga bytes transmitidos (TX) com protocolo e timestamp."""
    print(f"[{_timestamp()}][TX][{protocol}] {_hex_format(data)}", flush=True)


def log_rx(data: bytes, protocol: str = "SIMPLE") -> None:
    """Loga bytes recebidos (RX) com protocolo e timestamp."""
    print(f"[{_timestamp()}][RX][{protocol}] {_hex_format(data)}", flush=True)


def log_info(msg: str) -> None:
    """Loga mensagem informativa."""
    print(f"[{_timestamp()}][INFO] {msg}", flush=True)


def log_error(msg: str) -> None:
    """Loga mensagem de erro."""
    print(f"[{_timestamp()}][ERROR] {msg}", flush=True)


def log_warning(msg: str) -> None:
    """Loga mensagem de aviso."""
    print(f"[{_timestamp()}][WARN] {msg}", flush=True)
