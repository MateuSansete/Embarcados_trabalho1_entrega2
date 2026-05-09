"""
Ponto de entrada padrão — executa o CLI UART (Entrega 2).

Uso:
    python3 -m src                            # UART CLI (padrão)
    python3 -m src.uart_protocols.main        # UART CLI (explícito)
    python3 -m src.traffic_system.main        # Semáforos
"""
from src.uart_protocols.main import main

if __name__ == "__main__":
    main()
