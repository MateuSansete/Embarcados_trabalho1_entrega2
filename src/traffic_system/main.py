#!/usr/bin/env python3
"""
Sistema de Semáforos — Entrega 1.

Uso:
    python3 -m src.traffic_system.main           # Ambos os modelos
    python3 -m src.traffic_system.main --modelo 1
    python3 -m src.traffic_system.main --modelo 2
"""

import argparse
import signal
import sys

from src.common.hal import GPIOController
from src.traffic_system.models import TrafficLightModel1, TrafficLightModel2


def main():
    parser = argparse.ArgumentParser(description="Sistema de Semáforos — Entrega 1")
    parser.add_argument(
        "--modelo",
        type=int,
        choices=[1, 2],
        default=None,
        help="Modelo a executar (1 ou 2). Sem argumento executa ambos.",
    )
    args = parser.parse_args()

    gpio = GPIOController()
    threads = []

    if args.modelo in (None, 1):
        threads.append(TrafficLightModel1(gpio))

    if args.modelo in (None, 2):
        threads.append(TrafficLightModel2(gpio))

    def shutdown(signum=None, frame=None):
        print("\nEncerrando semáforos...", flush=True)
        for t in threads:
            t.stop()
        gpio.shutdown()
        print("Sistema encerrado.\n", flush=True)
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print("Iniciando sistema de semáforos... (Ctrl+C para encerrar)", flush=True)
    for t in threads:
        t.start()

    try:
        for t in threads:
            t.join()
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
