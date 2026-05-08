"""
Configurações do sistema.
Define pinos, tempos, debounce e parâmetros UART.
"""

# ─── Modelo 1: 3 LEDs individuais (Cruzamento 1) ────────────────────────────

# LEDs
M1_GPIO_GREEN = 17
M1_GPIO_YELLOW = 18
M1_GPIO_RED = 23

# Botões
M1_GPIO_BTN_PRINCIPAL = 1
M1_GPIO_BTN_CRUZAMENTO = 12

# Tempos (segundos)
M1_GREEN_TIME = 10
M1_YELLOW_TIME = 2
M1_RED_TIME = 10
M1_GREEN_MIN_TIME = 5  # Tempo mínimo no verde antes do botão funcionar

# ─── Modelo 2: Cruzamento Completo (3 bits, Cruzamento 2) ───────────────────

# Saídas (código de 3 bits)
M2_GPIO_BIT0 = 24
M2_GPIO_BIT1 = 8
M2_GPIO_BIT2 = 7

# Botões
M2_GPIO_BTN_PRINCIPAL = 25
M2_GPIO_BTN_CRUZAMENTO = 22

# Tempos (segundos)
M2_MAIN_GREEN_MIN = 10
M2_MAIN_GREEN_MAX = 20
M2_CROSS_GREEN_MIN = 5
M2_CROSS_GREEN_MAX = 10
M2_YELLOW_TIME = 2
M2_ALL_RED_TIME = 2

# ─── Geral ───────────────────────────────────────────────────────────────────

DEBOUNCE_MS = 200
LOOP_INTERVAL = 0.05

# ─── UART (Entrega 2) ───────────────────────────────────────────────────────

UART_PORT = "/dev/serial0"
UART_BAUDRATE = 115200
UART_TIMEOUT = 0.3          # 300ms (dentro da faixa 200–500ms)
UART_PARITY = "N"           # Nenhuma paridade
UART_STOPBITS = 1
UART_BYTESIZE = 8

# ─── Matrícula ───────────────────────────────────────────────────────────────
# 6 últimos dígitos como bytes crus (0–9), NÃO como caracteres ASCII.
# Matrícula 654321 → bytes([6, 5, 4, 3, 2, 1])

MATRICULA = bytes([6, 5, 4, 3, 2, 1])
MATRICULA_STR = "654321"

# ─── Protocolo Simplificado — Comandos ───────────────────────────────────────

# Comandos de solicitação (request)
CMD_REQUEST_INT    = 0xA1
CMD_REQUEST_FLOAT  = 0xA2
CMD_REQUEST_STRING = 0xA3

# Comandos de envio (send)
CMD_SEND_INT       = 0xB1
CMD_SEND_FLOAT     = 0xB2
CMD_SEND_STRING    = 0xB3

# ─── Limites e Retry ────────────────────────────────────────────────────────

MAX_STRING_LENGTH = 255      # Tamanho máximo de string (cabe em 1 byte)
RETRY_COUNT = 3              # Tentativas em caso de timeout/erro
RETRY_DELAY = 0.1            # Delay entre retries (segundos)
