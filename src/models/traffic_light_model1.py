"""
Modelo 1: Semáforo Simples (3 LEDs).
Ciclo: VERDE (10s) -> AMARELO (2s) -> VERMELHO (10s).
Botão: adianta o amarelo se já passou 5s de verde.
"""

import threading
import time
from enum import Enum

from src.config import (
    LOOP_INTERVAL,
    M1_GPIO_BTN_CRUZAMENTO,
    M1_GPIO_BTN_PRINCIPAL,
    M1_GPIO_GREEN,
    M1_GPIO_RED,
    M1_GPIO_YELLOW,
    M1_GREEN_MIN_TIME,
    M1_GREEN_TIME,
    M1_RED_TIME,
    M1_YELLOW_TIME,
)
from src.hal import GPIOController


class Model1State(Enum):
    GREEN = "VERDE"
    YELLOW = "AMARELO"
    RED = "VERMELHO"


class TrafficLightModel1(threading.Thread):
    def __init__(self, gpio: GPIOController):
        super().__init__(daemon=True, name="Model1-Thread")
        self._gpio = gpio
        self._running = threading.Event()
        self._pedestrian_requested = threading.Event()

        self._state = Model1State.GREEN
        self._state_start = 0.0

        # Configura as saídas
        self._gpio.setup_output(M1_GPIO_GREEN)
        self._gpio.setup_output(M1_GPIO_YELLOW)
        self._gpio.setup_output(M1_GPIO_RED)

        # Configura os botões
        self._gpio.setup_input(M1_GPIO_BTN_PRINCIPAL)
        self._gpio.setup_input(M1_GPIO_BTN_CRUZAMENTO)

        # Callbacks para os botões
        self._gpio.register_callback(M1_GPIO_BTN_PRINCIPAL, self._on_button_principal)
        self._gpio.register_callback(M1_GPIO_BTN_CRUZAMENTO, self._on_button_cruzamento)

    def _on_button_principal(self, channel):
        print(f"[Modelo 1] Botão Pedestre principal apertado (GPIO {channel})", flush=True)
        self._pedestrian_requested.set()

    def _on_button_cruzamento(self, channel):
        print(f"[Modelo 1] Botão Pedestre Cruzamento apertado (GPIO {channel})", flush=True)
        self._pedestrian_requested.set()

    def _set_leds(self, green, yellow, red):
        # Atalho pra ligar os LEDs
        self._gpio.write(M1_GPIO_GREEN, green)
        self._gpio.write(M1_GPIO_YELLOW, yellow)
        self._gpio.write(M1_GPIO_RED, red)

    def _apply_state(self):
        # Liga os LEDs certos pro estado atual
        if self._state == Model1State.GREEN:
            self._set_leds(green=True, yellow=False, red=False)
        elif self._state == Model1State.YELLOW:
            self._set_leds(green=False, yellow=True, red=False)
        elif self._state == Model1State.RED:
            self._set_leds(green=False, yellow=False, red=True)

    def _transition_to(self, new_state):
        # Troca de estado e reseta o timer
        print(f"[Modelo 1] {self._state.value} -> {new_state.value}", flush=True)
        self._state = new_state
        self._state_start = time.monotonic()
        self._pedestrian_requested.clear()
        self._apply_state()

    def run(self):
        # Loop da máquina de estados
        self._running.set()
        self._state_start = time.monotonic()
        self._apply_state()
        print(f"[Modelo 1] Começou no VERDE", flush=True)

        while self._running.is_set():
            elapsed = time.monotonic() - self._state_start

            if self._state == Model1State.GREEN:
                # Se apertaram o botão e deu o tempo mínimo, vai pro amarelo
                if self._pedestrian_requested.is_set() and elapsed >= M1_GREEN_MIN_TIME:
                    self._transition_to(Model1State.YELLOW)
                    continue
                # Tempo normal do verde
                if elapsed >= M1_GREEN_TIME:
                    self._transition_to(Model1State.YELLOW)
                    continue

            elif self._state == Model1State.YELLOW:
                if elapsed >= M1_YELLOW_TIME:
                    self._transition_to(Model1State.RED)
                    continue

            elif self._state == Model1State.RED:
                if elapsed >= M1_RED_TIME:
                    self._transition_to(Model1State.GREEN)
                    continue

            time.sleep(LOOP_INTERVAL)

    def stop(self):
        # Para a thread e desliga os LEDs
        self._running.clear()
        self.join(timeout=2.0)
        self._set_leds(False, False, False)
        print("[Modelo 1] Parou.", flush=True)
