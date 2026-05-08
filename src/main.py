#!/usr/bin/env python3
"""
CLI UART — Protocolo Simplificado (Entrega 2 — Parte 1)

Menu interativo para comunicação serial com a ESP32.
Todo o parsing binário fica em protocols/ — este módulo
apenas orquestra, chama funções, trata exceções e exibe menus.
"""

import signal
import sys

from src.config import (
    UART_PORT,
    UART_BAUDRATE,
    UART_TIMEOUT,
    UART_PARITY,
    UART_STOPBITS,
    UART_BYTESIZE,
    MATRICULA_STR,
)
from src.hal import UARTController
from src.protocols.simple_protocol import (
    request_integer,
    request_float,
    request_string,
    send_integer,
    send_float,
    send_string,
)
from src.utils.logger import log_info, log_error
from src.exceptions import UARTError, ProtocolError


# ─── Banner e Menu ───────────────────────────────────────────────────────────


BANNER = f"""\
{'═' * 58}
  UART — Protocolo Simplificado (Entrega 2 — Parte 1)
  Fundamentos de Sistemas Embarcados (2026/1)
  Matrícula: {MATRICULA_STR}
{'═' * 58}"""

MENU = """
  ┌─────────────────────────────────────────┐
  │  1 — Solicitar inteiro          (0xA1)  │
  │  2 — Solicitar float            (0xA2)  │
  │  3 — Solicitar string           (0xA3)  │
  │  4 — Enviar inteiro             (0xB1)  │
  │  5 — Enviar float               (0xB2)  │
  │  6 — Enviar string              (0xB3)  │
  │  0 — Sair                               │
  └─────────────────────────────────────────┘"""


# ─── Handlers de Comando ─────────────────────────────────────────────────────


def handle_option(option: str, uart: UARTController) -> None:
    """
    Despacha a opção do menu para a função de protocolo correspondente.

    Responsável APENAS por:
        - Ler input do usuário (se necessário)
        - Chamar a função do protocolo
        - Exibir resultado formatado
        - Tratar exceções
    """
    try:
        if option == "1":
            value = request_integer(uart)
            print(f"\n  ➜ Inteiro recebido: {value}", flush=True)

        elif option == "2":
            value = request_float(uart)
            print(f"\n  ➜ Float recebido: {value:.6f}", flush=True)

        elif option == "3":
            value = request_string(uart)
            print(f"\n  ➜ String recebida: \"{value}\"", flush=True)

        elif option == "4":
            raw = input("  Valor inteiro: ")
            val = int(raw)
            result = send_integer(uart, val)
            print(f"\n  ➜ Inteiro enviado: {val} → Resposta: {result}", flush=True)

        elif option == "5":
            raw = input("  Valor float: ")
            val = float(raw)
            result = send_float(uart, val)
            print(f"\n  ➜ Float enviado: {val} → Resposta: {result:.6f}", flush=True)

        elif option == "6":
            val = input("  String: ")
            result = send_string(uart, val)
            print(f"\n  ➜ String enviada: \"{val}\" → Resposta: \"{result}\"", flush=True)

        else:
            print("  ⚠ Opção inválida.", flush=True)

    except (UARTError, ProtocolError) as e:
        log_error(str(e))
        print(f"\n  ✗ Erro de comunicação: {e}", flush=True)

    except ValueError as e:
        print(f"\n  ✗ Valor inválido: {e}", flush=True)


# ─── Main ────────────────────────────────────────────────────────────────────


def main():
    print(BANNER, flush=True)

    # Inicializa UART
    uart = UARTController(
        port=UART_PORT,
        baudrate=UART_BAUDRATE,
        timeout=UART_TIMEOUT,
        parity=UART_PARITY,
        stopbits=UART_STOPBITS,
        bytesize=UART_BYTESIZE,
    )

    try:
        uart.connect()
    except UARTError as e:
        log_error(f"Não foi possível conectar à UART: {e}")
        print(f"\n  ✗ Falha na conexão UART: {e}", flush=True)
        print("  Verifique a porta e as conexões físicas.", flush=True)
        sys.exit(1)

    # Shutdown seguro
    def shutdown(signum=None, frame=None):
        print("\n\n  Desconectando UART...", flush=True)
        uart.disconnect()
        print("  Até logo!\n", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    # Loop principal do menu
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
