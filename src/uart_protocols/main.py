#!/usr/bin/env python3
"""
CLI UART — Entrega 2 (Protocolo Simplificado + MODBUS RTU Modificado).

Uso:
    python3 -m src.uart_protocols.main
"""

import signal
import sys

from src.common.config import (
    UART_PORT, UART_BAUDRATE, UART_TIMEOUT,
    UART_PARITY, UART_STOPBITS, UART_BYTESIZE,
    MATRICULA_STR,
)
from src.common.hal import UARTController
from src.uart_protocols.protocols.simple_protocol import (
    request_integer, request_float, request_string,
    send_integer, send_float, send_string,
)
from src.uart_protocols.protocols.modbus_protocol import (
    modbus_request_integer, modbus_request_float, modbus_request_string,
    modbus_send_integer, modbus_send_float, modbus_send_string,
)
from src.common.utils.logger import log_info, log_error
from src.common.exceptions import UARTError, ProtocolError, ModbusError


# ─── Banner e Menu ───────────────────────────────────────────────────────────

BANNER = f"""\
{'═' * 60}
  UART — Entrega 2  (Simplificado + MODBUS RTU Modificado)
  Fundamentos de Sistemas Embarcados (2026/1)
  Matrícula: {MATRICULA_STR}
{'═' * 60}"""

MENU = """
  ┌─────────────────────────────────────────────────────┐
  │  ══ Protocolo Simplificado (Parte 1) ══            │
  │  1  — Solicitar inteiro           (0xA1)           │
  │  2  — Solicitar float             (0xA2)           │
  │  3  — Solicitar string            (0xA3)           │
  │  4  — Enviar inteiro              (0xB1)           │
  │  5  — Enviar float                (0xB2)           │
  │  6  — Enviar string               (0xB3)           │
  │                                                     │
  │  ══ Protocolo MODBUS (Parte 2) ══                  │
  │  7  — [MODBUS] Solicitar inteiro  (0x23/0xA1)      │
  │  8  — [MODBUS] Solicitar float    (0x23/0xA2)      │
  │  9  — [MODBUS] Solicitar string   (0x23/0xA3)      │
  │  10 — [MODBUS] Enviar inteiro     (0x16/0xB1)      │
  │  11 — [MODBUS] Enviar float       (0x16/0xB2)      │
  │  12 — [MODBUS] Enviar string      (0x16/0xB3)      │
  │                                                     │
  │  0  — Sair                                          │
  └─────────────────────────────────────────────────────┘"""


# ─── Dispatcher ──────────────────────────────────────────────────────────────

def handle_option(option: str, uart: UARTController) -> None:
    try:
        if option == "1":
            print(f"\n  ➜ Inteiro recebido: {request_integer(uart)}", flush=True)
        elif option == "2":
            print(f"\n  ➜ Float recebido: {request_float(uart):.6f}", flush=True)
        elif option == "3":
            print(f"\n  ➜ String recebida: \"{request_string(uart)}\"", flush=True)
        elif option == "4":
            val = int(input("  Valor inteiro: "))
            print(f"\n  ➜ Resposta: {send_integer(uart, val)}", flush=True)
        elif option == "5":
            val = float(input("  Valor float: "))
            print(f"\n  ➜ Resposta: {send_float(uart, val):.6f}", flush=True)
        elif option == "6":
            val = input("  String: ")
            print(f"\n  ➜ Resposta: \"{send_string(uart, val)}\"", flush=True)
        elif option == "7":
            print(f"\n  ➜ [MODBUS] Inteiro: {modbus_request_integer(uart)}", flush=True)
        elif option == "8":
            print(f"\n  ➜ [MODBUS] Float: {modbus_request_float(uart):.6f}", flush=True)
        elif option == "9":
            print(f"\n  ➜ [MODBUS] String: \"{modbus_request_string(uart)}\"", flush=True)
        elif option == "10":
            val = int(input("  Valor inteiro: "))
            print(f"\n  ➜ [MODBUS] Resposta: {modbus_send_integer(uart, val)}", flush=True)
        elif option == "11":
            val = float(input("  Valor float: "))
            print(f"\n  ➜ [MODBUS] Resposta: {modbus_send_float(uart, val):.6f}", flush=True)
        elif option == "12":
            val = input("  String: ")
            print(f"\n  ➜ [MODBUS] Resposta: \"{modbus_send_string(uart, val)}\"", flush=True)
        else:
            print("  ⚠ Opção inválida.", flush=True)

    except (UARTError, ProtocolError, ModbusError) as e:
        log_error(str(e))
        print(f"\n  ✗ Erro: {e}", flush=True)
    except ValueError as e:
        print(f"\n  ✗ Valor inválido: {e}", flush=True)


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    print(BANNER, flush=True)

    uart = UARTController(
        port=UART_PORT, baudrate=UART_BAUDRATE, timeout=UART_TIMEOUT,
        parity=UART_PARITY, stopbits=UART_STOPBITS, bytesize=UART_BYTESIZE,
    )

    try:
        uart.connect()
    except UARTError as e:
        log_error(f"Falha na conexão: {e}")
        sys.exit(1)

    def shutdown(signum=None, frame=None):
        print("\n\n  Desconectando...", flush=True)
        uart.disconnect()
        print("  Até logo!\n", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while True:
            print(MENU, flush=True)
            option = input("\n  Opção: ").strip()
            if option == "0":
                shutdown()
            handle_option(option, uart)
    except (EOFError, KeyboardInterrupt):
        shutdown()


if __name__ == "__main__":
    main()
