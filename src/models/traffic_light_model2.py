"""
Modelo 2: Cruzamento Completo (3 bits).
Controla o cruzamento via códigos binários.
Sequência: 1 (Principal Verde) -> 2 (Amarelo) -> 4 (Tudo Vermelho) -> 
           5 (Cruzamento Verde) -> 6 (Amarelo) -> 4 (Tudo Vermelho).
"""

import threading
import time
from enum import Enum

from src.config import (
    LOOP_INTERVAL,
    M2_ALL_RED_TIME,
    M2_CROSS_GREEN_MAX,
    M2_CROSS_GREEN_MIN,
    M2_GPIO_BIT0,
    M2_GPIO_BIT1,
    M2_GPIO_BIT2,
    M2_GPIO_BTN_CRUZAMENTO,
    M2_GPIO_BTN_PRINCIPAL,
    M2_MAIN_GREEN_MAX,
    M2_MAIN_GREEN_MIN,
    M2_YELLOW_TIME,
)
from src.hal import GPIOController


class Model2State(Enum):
    S1_MAIN_GREEN = "S1_PRINCIPAL_VERDE"
    S2_MAIN_YELLOW = "S2_PRINCIPAL_AMARELO"
    S4_ALL_RED_A = "S4_TUDO_VERMELHO_A"
    S5_CROSS_GREEN = "S5_CRUZAMENTO_VERDE"
    S6_CROSS_YELLOW = "S6_CRUZAMENTO_AMARELO"
    S4_ALL_RED_B = "S4_TUDO_VERMELHO_B"


# Mapeia estado pro código binário
_STATE_TO_GPIO_CODE = {
    Model2State.S1_MAIN_GREEN: 1,
    Model2State.S2_MAIN_YELLOW: 2,
    Model2State.S4_ALL_RED_A: 4,
    Model2State.S5_CROSS_GREEN: 5,
    Model2State.S6_CROSS_YELLOW: 6,
    Model2State.S4_ALL_RED_B: 4,
}

# Nomes pra exibir no terminal
_STATE_DISPLAY_NAME = {
    Model2State.S1_MAIN_GREEN: "Principal VERDE",
    Model2State.S2_MAIN_YELLOW: "Principal AMARELO",
    Model2State.S4_ALL_RED_A: "TUDO VERMELHO",
    Model2State.S5_CROSS_GREEN: "Cruzamento VERDE",
    Model2State.S6_CROSS_YELLOW: "Cruzamento AMARELO",
    Model2State.S4_ALL_RED_B: "TUDO VERMELHO",
}


class TrafficLightModel2(threading.Thread):
    def __init__(self, gpio: GPIOController):
        super().__init__(daemon=True, name="Model2-Thread")
        self._gpio = gpio
        self._running = threading.Event()

        # Pedidos de travessia
        self._ped_main_requested = threading.Event()
        self._ped_cross_requested = threading.Event()

        self._state = Model2State.S1_MAIN_GREEN
        self._state_start = 0.0

        # Configura as 3 saídas
        self._output_pins = (M2_GPIO_BIT0, M2_GPIO_BIT1, M2_GPIO_BIT2)
        for pin in self._output_pins:
            self._gpio.setup_output(pin)

        # Configura os botões
        self._gpio.setup_input(M2_GPIO_BTN_PRINCIPAL)
        self._gpio.setup_input(M2_GPIO_BTN_CRUZAMENTO)

        # Callbacks pros botões
        self._gpio.register_callback(M2_GPIO_BTN_PRINCIPAL, self._on_button_main)
        self._gpio.register_callback(M2_GPIO_BTN_CRUZAMENTO, self._on_button_cross)

    def _on_button_main(self, channel):
        print(f"[Modelo 2] Botão Principal apertado (GPIO {channel})", flush=True)
        self._ped_main_requested.set()

    def _on_button_cross(self, channel):
        print(f"[Modelo 2] Botão Cruzamento apertado (GPIO {channel})", flush=True)
        self._ped_cross_requested.set()

    def _apply_state(self):
        # Manda o código pro GPIO
        code = _STATE_TO_GPIO_CODE[self._state]
        self._gpio.write_3bit(self._output_pins, code)

    def _transition_to(self, new_state):
        # Troca de estado
        print(f"[Modelo 2] {_STATE_DISPLAY_NAME[self._state]} -> {_STATE_DISPLAY_NAME[new_state]}", flush=True)
        self._state = new_state
        self._state_start = time.monotonic()
        self._apply_state()

    def run(self):
        # Loop principal
        self._running.set()
        self._state_start = time.monotonic()
        self._apply_state()
        print(f"[Modelo 2] Começou no Principal VERDE", flush=True)

        while self._running.is_set():
            elapsed = time.monotonic() - self._state_start

            if self._state == Model2State.S1_MAIN_GREEN:
                # Se pedirem pedestre e deu o tempo mínimo, ou se deu o tempo máximo
                if (self._ped_main_requested.is_set() and elapsed >= M2_MAIN_GREEN_MIN) or elapsed >= M2_MAIN_GREEN_MAX:
                    self._ped_main_requested.clear()
                    self._transition_to(Model2State.S2_MAIN_YELLOW)
                    continue

            elif self._state == Model2State.S2_MAIN_YELLOW:
                if elapsed >= M2_YELLOW_TIME:
                    self._transition_to(Model2State.S4_ALL_RED_A)
                    continue

            elif self._state == Model2State.S4_ALL_RED_A:
                if elapsed >= M2_ALL_RED_TIME:
                    self._transition_to(Model2State.S5_CROSS_GREEN)
                    continue

            elif self._state == Model2State.S5_CROSS_GREEN:
                # Se pedirem pedestre e deu o tempo mínimo, ou se deu o tempo máximo
                if (self._ped_cross_requested.is_set() and elapsed >= M2_CROSS_GREEN_MIN) or elapsed >= M2_CROSS_GREEN_MAX:
                    self._ped_cross_requested.clear()
                    self._transition_to(Model2State.S6_CROSS_YELLOW)
                    continue

            elif self._state == Model2State.S6_CROSS_YELLOW:
                if elapsed >= M2_YELLOW_TIME:
                    self._transition_to(Model2State.S4_ALL_RED_B)
                    continue

            elif self._state == Model2State.S4_ALL_RED_B:
                if elapsed >= M2_ALL_RED_TIME:
                    self._transition_to(Model2State.S1_MAIN_GREEN)
                    continue

            time.sleep(LOOP_INTERVAL)

    def stop(self):
        # Para tudo e deixa no vermelho por segurança
        self._running.clear()
        self.join(timeout=2.0)
        self._gpio.write_3bit(self._output_pins, 4)
        print("[Modelo 2] Parou.", flush=True)
