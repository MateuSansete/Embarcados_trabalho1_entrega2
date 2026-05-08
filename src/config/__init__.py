"""
Exporta as configurações para facilitar o import.
"""

from src.config.settings import (  # noqa: F401
    # Modelo 1
    M1_GPIO_GREEN,
    M1_GPIO_YELLOW,
    M1_GPIO_RED,
    M1_GPIO_BTN_PRINCIPAL,
    M1_GPIO_BTN_CRUZAMENTO,
    M1_GREEN_TIME,
    M1_YELLOW_TIME,
    M1_RED_TIME,
    M1_GREEN_MIN_TIME,
    # Modelo 2
    M2_GPIO_BIT0,
    M2_GPIO_BIT1,
    M2_GPIO_BIT2,
    M2_GPIO_BTN_PRINCIPAL,
    M2_GPIO_BTN_CRUZAMENTO,
    M2_MAIN_GREEN_MIN,
    M2_MAIN_GREEN_MAX,
    M2_CROSS_GREEN_MIN,
    M2_CROSS_GREEN_MAX,
    M2_YELLOW_TIME,
    M2_ALL_RED_TIME,
    # Parâmetros gerais
    DEBOUNCE_MS,
    LOOP_INTERVAL,
    # UART (Entrega 2)
    UART_PORT,
    UART_BAUDRATE,
    UART_TIMEOUT,
    UART_PARITY,
    UART_STOPBITS,
    UART_BYTESIZE,
    # Matrícula
    MATRICULA,
    MATRICULA_STR,
    # Comandos do protocolo simplificado
    CMD_REQUEST_INT,
    CMD_REQUEST_FLOAT,
    CMD_REQUEST_STRING,
    CMD_SEND_INT,
    CMD_SEND_FLOAT,
    CMD_SEND_STRING,
    # Limites e retry
    MAX_STRING_LENGTH,
    RETRY_COUNT,
    RETRY_DELAY,
)
