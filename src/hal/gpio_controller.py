"""
Abstração do GPIO para a Raspberry Pi.
Configura pinos, lê/escreve e cuida das interrupções.
"""

import RPi.GPIO as GPIO
from src.config import DEBOUNCE_MS


class GPIOController:
    # Gerencia o hardware da Raspberry
    def __init__(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        self._output_pins = []
        self._input_pins = []

    def setup_output(self, pin, initial=GPIO.LOW):
        # Configura pino de saída
        GPIO.setup(pin, GPIO.OUT, initial=initial)
        self._output_pins.append(pin)

    def setup_input(self, pin, pull_down=True):
        # Configura pino de entrada (botões)
        pud = GPIO.PUD_DOWN if pull_down else GPIO.PUD_UP
        GPIO.setup(pin, GPIO.IN, pull_up_down=pud)
        self._input_pins.append(pin)

    def write(self, pin, value):
        # Liga ou desliga um pino
        GPIO.output(pin, GPIO.HIGH if value else GPIO.LOW)

    def read(self, pin):
        # Lê o estado de um pino
        return bool(GPIO.input(pin))

    def write_3bit(self, pins, code):
        # Manda um valor de 0 a 7 usando 3 pinos
        if not 0 <= code <= 7:
            raise ValueError(f"Código inválido: {code}")

        for i, pin in enumerate(pins):
            bit_value = bool((code >> i) & 1)
            self.write(pin, bit_value)

    def register_callback(self, pin, callback, debounce_ms=DEBOUNCE_MS):
        # Registra o que fazer quando apertarem um botão
        GPIO.add_event_detect(
            pin,
            GPIO.RISING,
            callback=callback,
            bouncetime=debounce_ms,
        )

    def shutdown(self):
        # Desliga tudo com segurança sem usar o cleanup() geral
        for pin in self._input_pins:
            try:
                GPIO.remove_event_detect(pin)
            except:
                pass

        for pin in self._output_pins:
            try:
                GPIO.output(pin, GPIO.LOW)
            except:
                pass

        self._output_pins.clear()
        self._input_pins.clear()
