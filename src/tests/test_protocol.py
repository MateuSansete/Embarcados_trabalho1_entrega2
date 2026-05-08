"""
Testes unitários do Protocolo Simplificado UART — Entrega 2, Parte 1.

Executa SEM hardware (sem ESP32, sem Raspberry Pi).
Usa mocks para simular o UARTController e validar:
    - Construção correta de pacotes (TX)
    - Decodificação correta de respostas (RX)
    - Tratamento de erros (timeout, tamanho inválido, string truncada)
    - Retry automático

Executar:
    python3 -m pytest src/tests/test_protocol.py -v
"""

import struct
import unittest
from unittest.mock import MagicMock, call

from src.config import (
    MATRICULA,
    CMD_REQUEST_INT,
    CMD_REQUEST_FLOAT,
    CMD_REQUEST_STRING,
    CMD_SEND_INT,
    CMD_SEND_FLOAT,
    CMD_SEND_STRING,
)
from src.protocols.packet_utils import (
    build_request_packet,
    build_send_int_packet,
    build_send_float_packet,
    build_send_string_packet,
)
from src.protocols.parsers import (
    parse_int32,
    parse_float,
    parse_string_response,
)
from src.protocols.simple_protocol import (
    request_integer,
    request_float,
    request_string,
    send_integer,
    send_float,
    send_string,
)
from src.exceptions import (
    UARTTimeoutError,
    IncompleteResponseError,
    InvalidSizeError,
    InvalidPacketError,
)


# ═══════════════════════════════════════════════════════════════════════════════
#  TESTES DE CONSTRUÇÃO DE PACOTES (packet_utils)
# ═══════════════════════════════════════════════════════════════════════════════


class TestBuildRequestPacket(unittest.TestCase):
    """Testa construção de pacotes de solicitação [CMD][MATRÍCULA]."""

    def test_request_int_packet(self):
        """0xA1 + matrícula = 7 bytes."""
        packet = build_request_packet(CMD_REQUEST_INT)
        self.assertEqual(len(packet), 7)
        self.assertEqual(packet[0], 0xA1)
        self.assertEqual(packet[1:], MATRICULA)

    def test_request_float_packet(self):
        """0xA2 + matrícula = 7 bytes."""
        packet = build_request_packet(CMD_REQUEST_FLOAT)
        self.assertEqual(len(packet), 7)
        self.assertEqual(packet[0], 0xA2)
        self.assertEqual(packet[1:], MATRICULA)

    def test_request_string_packet(self):
        """0xA3 + matrícula = 7 bytes."""
        packet = build_request_packet(CMD_REQUEST_STRING)
        self.assertEqual(len(packet), 7)
        self.assertEqual(packet[0], 0xA3)
        self.assertEqual(packet[1:], MATRICULA)

    def test_matricula_bytes_not_ascii(self):
        """Matrícula deve ser bytes crus (0x06), NÃO ASCII (0x36)."""
        packet = build_request_packet(CMD_REQUEST_INT)
        # Dígito 6 → byte 0x06, não 0x36 ('6' em ASCII)
        self.assertEqual(packet[1], 0x06)
        self.assertNotEqual(packet[1], 0x36)
        # Dígito 1 → byte 0x01, não 0x31 ('1' em ASCII)
        self.assertEqual(packet[6], 0x01)
        self.assertNotEqual(packet[6], 0x31)


class TestBuildSendPacket(unittest.TestCase):
    """Testa construção de pacotes de envio."""

    def test_send_int_packet(self):
        """0xB1 + int32_LE + matrícula = 11 bytes."""
        packet = build_send_int_packet(CMD_SEND_INT, 42)
        self.assertEqual(len(packet), 11)
        self.assertEqual(packet[0], 0xB1)
        # int32 LE de 42
        self.assertEqual(packet[1:5], struct.pack('<i', 42))
        self.assertEqual(packet[5:], MATRICULA)

    def test_send_int_negative(self):
        """Int32 negativo deve empacotar corretamente."""
        packet = build_send_int_packet(CMD_SEND_INT, -1)
        self.assertEqual(packet[1:5], struct.pack('<i', -1))
        self.assertEqual(packet[1:5], b'\xff\xff\xff\xff')

    def test_send_float_packet(self):
        """0xB2 + float_LE + matrícula = 11 bytes."""
        packet = build_send_float_packet(CMD_SEND_FLOAT, 3.14)
        self.assertEqual(len(packet), 11)
        self.assertEqual(packet[0], 0xB2)
        self.assertEqual(packet[1:5], struct.pack('<f', 3.14))
        self.assertEqual(packet[5:], MATRICULA)

    def test_send_string_packet(self):
        """0xB3 + N + string + matrícula = (8 + N) bytes."""
        packet = build_send_string_packet(CMD_SEND_STRING, "hello")
        encoded = "hello".encode('utf-8')
        expected_len = 1 + 1 + len(encoded) + len(MATRICULA)  # cmd + N + str + mat
        self.assertEqual(len(packet), expected_len)
        self.assertEqual(packet[0], 0xB3)
        self.assertEqual(packet[1], len(encoded))
        self.assertEqual(packet[2:2 + len(encoded)], encoded)
        self.assertEqual(packet[2 + len(encoded):], MATRICULA)

    def test_send_string_utf8(self):
        """Strings com caracteres multibyte devem ter tamanho correto."""
        packet = build_send_string_packet(CMD_SEND_STRING, "café")
        encoded = "café".encode('utf-8')
        self.assertEqual(packet[1], len(encoded))  # 5 bytes (é = 2 bytes UTF-8)

    def test_send_empty_string_raises(self):
        """String vazia deve levantar InvalidPacketError."""
        with self.assertRaises(InvalidPacketError):
            build_send_string_packet(CMD_SEND_STRING, "")

    def test_send_string_too_long_raises(self):
        """String > 255 bytes deve levantar InvalidPacketError."""
        with self.assertRaises(InvalidPacketError):
            build_send_string_packet(CMD_SEND_STRING, "A" * 256)


# ═══════════════════════════════════════════════════════════════════════════════
#  TESTES DE PARSING DE RESPOSTAS (parsers)
# ═══════════════════════════════════════════════════════════════════════════════


class TestParseInt32(unittest.TestCase):
    """Testa decodificação de int32 little-endian."""

    def test_positive_int(self):
        data = struct.pack('<i', 41987)
        self.assertEqual(parse_int32(data), 41987)

    def test_negative_int(self):
        data = struct.pack('<i', -12345)
        self.assertEqual(parse_int32(data), -12345)

    def test_zero(self):
        data = struct.pack('<i', 0)
        self.assertEqual(parse_int32(data), 0)

    def test_incomplete_raises(self):
        with self.assertRaises(IncompleteResponseError):
            parse_int32(b'\x00\x00')

    def test_empty_raises(self):
        with self.assertRaises(IncompleteResponseError):
            parse_int32(b'')


class TestParseFloat(unittest.TestCase):
    """Testa decodificação de float little-endian (IEEE 754)."""

    def test_positive_float(self):
        data = struct.pack('<f', 3.14)
        result = parse_float(data)
        self.assertAlmostEqual(result, 3.14, places=2)

    def test_negative_float(self):
        data = struct.pack('<f', -2.5)
        result = parse_float(data)
        self.assertAlmostEqual(result, -2.5, places=2)

    def test_zero_float(self):
        data = struct.pack('<f', 0.0)
        self.assertEqual(parse_float(data), 0.0)

    def test_incomplete_raises(self):
        with self.assertRaises(IncompleteResponseError):
            parse_float(b'\x00\x00\x00')


class TestParseString(unittest.TestCase):
    """Testa decodificação de resposta string."""

    def test_normal_string(self):
        text = "Hello UART"
        string_bytes = text.encode('utf-8')
        size_byte = bytes([len(string_bytes)])
        result = parse_string_response(size_byte, string_bytes)
        self.assertEqual(result, text)

    def test_utf8_string(self):
        text = "café"
        string_bytes = text.encode('utf-8')
        size_byte = bytes([len(string_bytes)])
        result = parse_string_response(size_byte, string_bytes)
        self.assertEqual(result, text)

    def test_size_zero_raises(self):
        with self.assertRaises(InvalidSizeError):
            parse_string_response(bytes([0]), b'')

    def test_size_mismatch_raises(self):
        with self.assertRaises(IncompleteResponseError):
            parse_string_response(bytes([5]), b'abc')  # Esperava 5, recebeu 3


# ═══════════════════════════════════════════════════════════════════════════════
#  TESTES DE PROTOCOLO INTEGRADO (simple_protocol)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequestInteger(unittest.TestCase):
    """Testa request_integer com UARTController mockado."""

    def _mock_uart(self, response_bytes: bytes) -> MagicMock:
        uart = MagicMock()
        uart.read_exact.return_value = response_bytes
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        return uart

    def test_request_integer_success(self):
        """Deve enviar pacote correto e decodificar resposta."""
        expected_value = 41987
        response = struct.pack('<i', expected_value)
        uart = self._mock_uart(response)

        result = request_integer(uart)

        self.assertEqual(result, expected_value)
        uart.flush_input.assert_called()
        uart.send_bytes.assert_called_once()

        # Verifica pacote enviado
        sent_packet = uart.send_bytes.call_args[0][0]
        self.assertEqual(sent_packet[0], CMD_REQUEST_INT)
        self.assertEqual(sent_packet[1:], MATRICULA)

    def test_request_integer_timeout_retry(self):
        """Deve retentar em caso de timeout."""
        expected_value = 100
        response = struct.pack('<i', expected_value)
        uart = MagicMock()
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        # Primeira tentativa falha, segunda sucede
        uart.read_exact.side_effect = [
            UARTTimeoutError("timeout"),
            response,
        ]

        result = request_integer(uart)

        self.assertEqual(result, expected_value)
        self.assertEqual(uart.send_bytes.call_count, 2)


class TestRequestFloat(unittest.TestCase):
    """Testa request_float com UARTController mockado."""

    def test_request_float_success(self):
        expected_value = 3.14
        response = struct.pack('<f', expected_value)
        uart = MagicMock()
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        uart.read_exact.return_value = response

        result = request_float(uart)

        self.assertAlmostEqual(result, expected_value, places=2)
        sent_packet = uart.send_bytes.call_args[0][0]
        self.assertEqual(sent_packet[0], CMD_REQUEST_FLOAT)


class TestRequestString(unittest.TestCase):
    """Testa request_string com UARTController mockado."""

    def test_request_string_success(self):
        text = "Hello UART"
        encoded = text.encode('utf-8')
        uart = MagicMock()
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        # Dois read_exact: 1 byte de tamanho + N bytes de string
        uart.read_exact.side_effect = [
            bytes([len(encoded)]),
            encoded,
        ]

        result = request_string(uart)

        self.assertEqual(result, text)
        sent_packet = uart.send_bytes.call_args[0][0]
        self.assertEqual(sent_packet[0], CMD_REQUEST_STRING)

    def test_request_string_invalid_size_raises(self):
        uart = MagicMock()
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        # Tamanho 0 → InvalidSizeError
        uart.read_exact.return_value = bytes([0])

        with self.assertRaises(InvalidSizeError):
            request_string(uart)


class TestSendInteger(unittest.TestCase):
    """Testa send_integer com UARTController mockado."""

    def test_send_integer_success(self):
        value = 7
        # ESP32 responde com value * último_dígito (1) = 7
        response = struct.pack('<i', 7)
        uart = MagicMock()
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        uart.read_exact.return_value = response

        result = send_integer(uart, value)

        self.assertEqual(result, 7)
        sent_packet = uart.send_bytes.call_args[0][0]
        self.assertEqual(len(sent_packet), 11)
        self.assertEqual(sent_packet[0], CMD_SEND_INT)
        self.assertEqual(sent_packet[1:5], struct.pack('<i', value))
        self.assertEqual(sent_packet[5:], MATRICULA)


class TestSendFloat(unittest.TestCase):
    """Testa send_float com UARTController mockado."""

    def test_send_float_success(self):
        value = 2.5
        response = struct.pack('<f', 2.5)
        uart = MagicMock()
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        uart.read_exact.return_value = response

        result = send_float(uart, value)

        self.assertAlmostEqual(result, 2.5, places=2)
        sent_packet = uart.send_bytes.call_args[0][0]
        self.assertEqual(len(sent_packet), 11)
        self.assertEqual(sent_packet[0], CMD_SEND_FLOAT)


class TestSendString(unittest.TestCase):
    """Testa send_string com UARTController mockado."""

    def test_send_string_success(self):
        value = "hello"
        response_text = "Resposta da UART: hello"
        encoded_response = response_text.encode('utf-8')
        uart = MagicMock()
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        uart.read_exact.side_effect = [
            bytes([len(encoded_response)]),
            encoded_response,
        ]

        result = send_string(uart, value)

        self.assertEqual(result, response_text)
        sent_packet = uart.send_bytes.call_args[0][0]
        self.assertEqual(sent_packet[0], CMD_SEND_STRING)


# ═══════════════════════════════════════════════════════════════════════════════
#  TESTES DE RETRY
# ═══════════════════════════════════════════════════════════════════════════════


class TestRetryMechanism(unittest.TestCase):
    """Testa que o retry funciona em todos os comandos."""

    def test_all_retries_exhausted(self):
        """Se todas as tentativas falharem, deve propagar o erro."""
        uart = MagicMock()
        uart.flush_input.return_value = None
        uart.send_bytes.return_value = None
        uart.read_exact.side_effect = UARTTimeoutError("timeout")

        with self.assertRaises(UARTTimeoutError):
            request_integer(uart)

        # Deve ter tentado RETRY_COUNT vezes
        from src.config import RETRY_COUNT
        self.assertEqual(uart.send_bytes.call_count, RETRY_COUNT)


# ═══════════════════════════════════════════════════════════════════════════════
#  TESTES DO DASHBOARD (validação visual da matrícula no ThingsBoard)
# ═══════════════════════════════════════════════════════════════════════════════


class TestDashboardCompliance(unittest.TestCase):
    """Verifica que os pacotes enviados estão no formato que o dashboard espera."""

    def test_request_packet_matches_dashboard_example(self):
        """
        Dashboard mostra: 0xA1 0x06 0x05 0x04 0x03 0x02 0x01
        para matrícula 654321.
        """
        packet = build_request_packet(CMD_REQUEST_INT)
        expected = bytes([0xA1, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01])
        self.assertEqual(packet, expected)

    def test_send_int_packet_size(self):
        """Pacote B1 deve ter exatamente 11 bytes."""
        packet = build_send_int_packet(CMD_SEND_INT, 3245)
        self.assertEqual(len(packet), 11)

    def test_send_string_packet_size(self):
        """Pacote B3 'hello' deve ter 8 + 5 = 13 bytes."""
        # [0xB3][N=5][h][e][l][l][o][mat 6 bytes] = 1+1+5+6 = 13
        # Actually: cmd(1) + N(1) + string(5) + mat(6) = 13
        # But spec says 8+N where N is string length. 8+5=13. ✓
        packet = build_send_string_packet(CMD_SEND_STRING, "hello")
        self.assertEqual(len(packet), 8 + 5)


if __name__ == "__main__":
    unittest.main()
