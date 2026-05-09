"""
Configurações globais do projeto FSE — Entrega 2.

Seções:
    1. UART
    2. Matrícula
    3. Protocolo Simplificado — Comandos
    4. MODBUS RTU Modificado
    5. Limites e Retry

    6. Semáforos — Modelo 1 (3 LEDs)
    7. Semáforos — Modelo 2 (Cruzamento Completo)
    8. Semáforos — Geral
"""

# ─── 1. UART ─────────────────────────────────────────────────────────────────

UART_PORT     = "/dev/serial0"
UART_BAUDRATE = 115200
UART_TIMEOUT  = 0.3        # 300 ms (faixa 200–500 ms)
UART_PARITY   = "N"
UART_STOPBITS = 1
UART_BYTESIZE = 8

# ─── 2. Matrícula ────────────────────────────────────────────────────────────
# 6 últimos dígitos como bytes crus (0–9), NÃO como caracteres ASCII.
# Matrícula 062240 → bytes([0, 6, 2, 2, 4, 0])

MATRICULA     = bytes([0, 6, 2, 2, 4, 0])
MATRICULA_STR = "062240"

# ─── 3. Protocolo Simplificado — Comandos ────────────────────────────────────

CMD_REQUEST_INT    = 0xA1
CMD_REQUEST_FLOAT  = 0xA2
CMD_REQUEST_STRING = 0xA3
CMD_SEND_INT       = 0xB1
CMD_SEND_FLOAT     = 0xB2
CMD_SEND_STRING    = 0xB3

# ─── 4. MODBUS RTU Modificado ────────────────────────────────────────────────

MODBUS_DEFAULT_SLAVE_ADDR = 0x01

MODBUS_FUNC_READ  = 0x23    # Solicitação / leitura
MODBUS_FUNC_WRITE = 0x16    # Envio / escrita

MODBUS_SUB_REQUEST_INT    = 0xA1
MODBUS_SUB_REQUEST_FLOAT  = 0xA2
MODBUS_SUB_REQUEST_STRING = 0xA3
MODBUS_SUB_SEND_INT       = 0xB1
MODBUS_SUB_SEND_FLOAT     = 0xB2
MODBUS_SUB_SEND_STRING    = 0xB3

# ─── 5. Limites e Retry ──────────────────────────────────────────────────────

MAX_STRING_LENGTH  = 255
RETRY_COUNT        = 3
RETRY_DELAY        = 0.1    # segundos

MODBUS_RETRY_COUNT = 3
MODBUS_RETRY_DELAY = 0.15   # segundos

# ─── 6. Semáforos — Modelo 1 (Semáforo Simples, 3 LEDs) ─────────────────────

M1_GPIO_GREEN  = 17
M1_GPIO_YELLOW = 18
M1_GPIO_RED    = 23

M1_GPIO_BTN_PRINCIPAL  = 1
M1_GPIO_BTN_CRUZAMENTO = 12

M1_GREEN_TIME     = 10   # segundos
M1_YELLOW_TIME    = 2
M1_RED_TIME       = 10
M1_GREEN_MIN_TIME = 5    # tempo mínimo no verde antes do botão funcionar

# ─── 7. Semáforos — Modelo 2 (Cruzamento Completo, 3 bits) ──────────────────

M2_GPIO_BIT0 = 24
M2_GPIO_BIT1 = 8
M2_GPIO_BIT2 = 7

M2_GPIO_BTN_PRINCIPAL  = 25
M2_GPIO_BTN_CRUZAMENTO = 22

M2_MAIN_GREEN_MIN  = 10
M2_MAIN_GREEN_MAX  = 20
M2_CROSS_GREEN_MIN = 5
M2_CROSS_GREEN_MAX = 10
M2_YELLOW_TIME     = 2
M2_ALL_RED_TIME    = 2

# ─── 8. Semáforos — Geral ────────────────────────────────────────────────────

DEBOUNCE_MS   = 200
LOOP_INTERVAL = 0.05
