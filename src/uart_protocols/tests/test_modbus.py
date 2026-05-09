"""
Testes da Entrega 2 — UART + MODBUS RTU Modificado

Valida conformidade estrita com Entrega_2.md e uart_modbus.md:

    1. CRC-16 MODBUS (polinômio 0xA001, init 0xFFFF, little-endian)
    2. Frame building — todos os 6 comandos MODBUS
    3. Frame sizes — conforme Tabela 2.4 do Entrega_2.md
    4. Posicionamento da matrícula no frame
    5. Exception frame detection (FUNC | 0x80)
    6. Parsing — int32, float, string
    7. Retry logic — comportamento em timeout e CRC inválido

Referência: Entrega_2.md §2 + uart_modbus.md §4-§5
Matrícula:  062240  →  bytes([0, 6, 2, 2, 4, 0])
"""

import struct
import unittest
from unittest.mock import MagicMock, call, patch

from src.uart_protocols.protocols.crc_utils import calculate_crc, validate_crc
from src.uart_protocols.protocols.modbus_protocol import (
    build_modbus_request_frame,
    build_modbus_send_int_frame,
    build_modbus_send_float_frame,
    build_modbus_send_string_frame,
    modbus_request_integer,
    modbus_send_integer,
    ModbusFunctionCodes,
    ModbusSubCodes,
    SlaveAddresses,
)
from src.uart_protocols.protocols.parsers import (
    parse_int32,
    parse_float,
    parse_string_response,
    is_exception_frame,
    parse_modbus_exception,
    parse_modbus_payload,
)
from src.common.config import MATRICULA, MATRICULA_STR
from src.common.exceptions import (
    ModbusCRCError,
    ModbusExceptionResponse,
    InvalidFunctionCode,
    IncompleteResponseError,
    InvalidSizeError,
    UARTTimeoutError,
)

ADDR = SlaveAddresses.DEFAULT  # 0x01


# ─── 1. Matrícula ────────────────────────────────────────────────────────────

class TestMatricula(unittest.TestCase):
    """Verifica que a matrícula está configurada corretamente."""

    def test_matricula_str_is_062240(self):
        self.assertEqual(MATRICULA_STR, "062240")

    def test_matricula_has_6_bytes(self):
        """Entrega_2.md §2.1: matrícula = 6 bytes."""
        self.assertEqual(len(MATRICULA), 6)

    def test_matricula_bytes_are_integer_digits(self):
        """Entrega_2.md §2: bytes são valores inteiros dos dígitos, NÃO ASCII."""
        expected = bytes([0, 6, 2, 2, 4, 0])
        self.assertEqual(MATRICULA, expected)

    def test_matricula_digits_in_range_0_9(self):
        for byte in MATRICULA:
            self.assertLessEqual(byte, 9)


# ─── 2. CRC-16 MODBUS ────────────────────────────────────────────────────────

class TestCRC16(unittest.TestCase):
    """Valida o algoritmo CRC-16 conforme uart_modbus.md §2-D."""

    def test_crc_solicita_int_nossa_matricula(self):
        """
        Frame: 01 23 A1 + matrícula 062240
        Resultado esperado verificado com implementação de referência.
        """
        body = bytes([0x01, 0x23, 0xA1]) + MATRICULA
        crc = calculate_crc(body)
        self.assertEqual(len(crc), 2)
        # Verificar via roundtrip
        self.assertTrue(validate_crc(body + crc))

    def test_crc_returns_2_bytes(self):
        self.assertEqual(len(calculate_crc(b"\x01\x23\xA1")), 2)

    def test_crc_is_little_endian(self):
        """Entrega_2.md §5: [CRC_LO][CRC_HI]."""
        body = bytes([0x01, 0x23, 0xA1]) + MATRICULA
        crc = calculate_crc(body)
        # Recompute manually
        val = 0xFFFF
        for byte in body:
            val ^= byte
            for _ in range(8):
                if val & 0x0001:
                    val >>= 1
                    val ^= 0xA001
                else:
                    val >>= 1
        lo = val & 0xFF
        hi = (val >> 8) & 0xFF
        self.assertEqual(crc[0], lo)
        self.assertEqual(crc[1], hi)

    def test_validate_crc_valid_frame(self):
        body = bytes([0x01, 0x23, 0xA1]) + MATRICULA
        frame = body + calculate_crc(body)
        self.assertTrue(validate_crc(frame))

    def test_validate_crc_corrupted_frame(self):
        body = bytes([0x01, 0x23, 0xA1]) + MATRICULA
        frame = bytearray(body + calculate_crc(body))
        frame[2] ^= 0xFF  # corrompe um byte
        self.assertFalse(validate_crc(bytes(frame)))

    def test_validate_crc_wrong_crc_bytes(self):
        body = bytes([0x01, 0x23, 0xA1]) + MATRICULA
        frame = body + bytes([0x00, 0x00])  # CRC errado
        self.assertFalse(validate_crc(frame))

    def test_validate_crc_too_short(self):
        self.assertFalse(validate_crc(b"\x01\x23"))

    def test_crc_includes_matricula(self):
        """CRC calculado COM matrícula deve diferir de CRC sem matrícula."""
        body_com = bytes([0x01, 0x23, 0xA1]) + MATRICULA
        body_sem = bytes([0x01, 0x23, 0xA1])
        self.assertNotEqual(calculate_crc(body_com), calculate_crc(body_sem))


# ─── 3. Tamanhos de Frame (Tabela 2.4 do Entrega_2.md) ──────────────────────

class TestFrameSizes(unittest.TestCase):
    """
    Tabela 2.4:
      Solicita INT/FLOAT/STRING: 11 bytes (3 + 6 + 2)
      Envia INT/FLOAT:           15 bytes (3 + 4 + 6 + 2)
      Envia STRING "oi" (N=2):   14 bytes (3 + 1 + N + 6 + 2)
    """

    def test_solicita_int_11_bytes(self):
        frame = build_modbus_request_frame(ADDR, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_INT)
        self.assertEqual(len(frame), 11)

    def test_solicita_float_11_bytes(self):
        frame = build_modbus_request_frame(ADDR, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_FLOAT)
        self.assertEqual(len(frame), 11)

    def test_solicita_string_11_bytes(self):
        frame = build_modbus_request_frame(ADDR, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_STRING)
        self.assertEqual(len(frame), 11)

    def test_envia_int_15_bytes(self):
        frame = build_modbus_send_int_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_INT, 3245)
        self.assertEqual(len(frame), 15)

    def test_envia_float_15_bytes(self):
        frame = build_modbus_send_float_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_FLOAT, 3.14)
        self.assertEqual(len(frame), 15)

    def test_envia_string_oi_14_bytes(self):
        """Entrega_2.md exemplo: envia "oi" → 14 bytes."""
        frame = build_modbus_send_string_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_STRING, "oi")
        self.assertEqual(len(frame), 14)

    def test_envia_string_tamanho_variavel(self):
        """Envia string de N bytes → (12 + N) bytes."""
        for n in [1, 5, 10, 20]:
            text = "x" * n
            frame = build_modbus_send_string_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_STRING, text)
            self.assertEqual(len(frame), 12 + n, f"N={n}")


# ─── 4. Estrutura dos Frames ──────────────────────────────────────────────────

class TestFrameStructure(unittest.TestCase):
    """Valida posicionamento de campos dentro do frame."""

    def setUp(self):
        self.req_int = build_modbus_request_frame(ADDR, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_INT)
        self.snd_int = build_modbus_send_int_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_INT, 3245)

    def test_addr_is_first_byte(self):
        self.assertEqual(self.req_int[0], ADDR)
        self.assertEqual(self.snd_int[0], ADDR)

    def test_func_is_second_byte_request(self):
        self.assertEqual(self.req_int[1], ModbusFunctionCodes.READ)

    def test_func_is_second_byte_write(self):
        self.assertEqual(self.snd_int[1], ModbusFunctionCodes.WRITE)

    def test_subcode_is_third_byte_request(self):
        self.assertEqual(self.req_int[2], ModbusSubCodes.REQUEST_INT)

    def test_subcode_is_third_byte_write(self):
        self.assertEqual(self.snd_int[2], ModbusSubCodes.SEND_INT)

    def test_matricula_in_request_frame(self):
        """Matrícula deve estar nos bytes [3:9] do frame de solicitação."""
        self.assertEqual(self.req_int[3:9], MATRICULA)

    def test_matricula_in_send_int_frame(self):
        """Matrícula deve estar nos bytes [7:13] do frame de envio de int."""
        self.assertEqual(self.snd_int[7:13], MATRICULA)

    def test_int_value_3245_little_endian(self):
        """Entrega_2.md exemplo: int 3245 → AD 0C 00 00."""
        expected = struct.pack('<i', 3245)
        self.assertEqual(self.snd_int[3:7], expected)

    def test_crc_is_last_2_bytes(self):
        crc = self.req_int[-2:]
        self.assertTrue(validate_crc(self.req_int))

    def test_all_request_frames_have_valid_crc(self):
        frames = [
            build_modbus_request_frame(ADDR, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_INT),
            build_modbus_request_frame(ADDR, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_FLOAT),
            build_modbus_request_frame(ADDR, ModbusFunctionCodes.READ, ModbusSubCodes.REQUEST_STRING),
        ]
        for frame in frames:
            self.assertTrue(validate_crc(frame))

    def test_all_send_frames_have_valid_crc(self):
        frames = [
            build_modbus_send_int_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_INT, 100),
            build_modbus_send_float_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_FLOAT, 1.5),
            build_modbus_send_string_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_STRING, "teste"),
        ]
        for frame in frames:
            self.assertTrue(validate_crc(frame))

    def test_string_frame_len_byte_correct(self):
        """Byte [3] do frame de string = tamanho da string."""
        text = "hello"
        frame = build_modbus_send_string_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_STRING, text)
        self.assertEqual(frame[3], len(text))

    def test_string_frame_content_correct(self):
        text = "hello"
        frame = build_modbus_send_string_frame(ADDR, ModbusFunctionCodes.WRITE, ModbusSubCodes.SEND_STRING, text)
        self.assertEqual(frame[4:4+len(text)], text.encode('utf-8'))


# ─── 5. Códigos de Função e Sub-códigos ──────────────────────────────────────

class TestFunctionCodes(unittest.TestCase):
    """Valida os códigos conforme uart_modbus.md Tabela 1."""

    def test_read_function_code(self):
        self.assertEqual(ModbusFunctionCodes.READ, 0x23)

    def test_write_function_code(self):
        self.assertEqual(ModbusFunctionCodes.WRITE, 0x16)

    def test_subcodes_request(self):
        self.assertEqual(ModbusSubCodes.REQUEST_INT, 0xA1)
        self.assertEqual(ModbusSubCodes.REQUEST_FLOAT, 0xA2)
        self.assertEqual(ModbusSubCodes.REQUEST_STRING, 0xA3)

    def test_subcodes_send(self):
        self.assertEqual(ModbusSubCodes.SEND_INT, 0xB1)
        self.assertEqual(ModbusSubCodes.SEND_FLOAT, 0xB2)
        self.assertEqual(ModbusSubCodes.SEND_STRING, 0xB3)

    def test_slave_addr_default(self):
        self.assertEqual(SlaveAddresses.DEFAULT, 0x01)


# ─── 6. Exception Frames ─────────────────────────────────────────────────────

class TestExceptionFrames(unittest.TestCase):
    """uart_modbus.md §2-B: erro = FUNC | 0x80."""

    def test_is_exception_frame_true(self):
        # 0x23 | 0x80 = 0xA3
        self.assertTrue(is_exception_frame(0xA3))
        self.assertTrue(is_exception_frame(0x96))  # 0x16 | 0x80
        self.assertTrue(is_exception_frame(0xFF))

    def test_is_exception_frame_false(self):
        self.assertFalse(is_exception_frame(0x23))
        self.assertFalse(is_exception_frame(0x16))
        self.assertFalse(is_exception_frame(0x00))

    def test_parse_exception_recovers_original_func(self):
        # Frame: [ADDR][FUNC|0x80][EXC_CODE][CRC_LO][CRC_HI]
        frame = bytes([0x01, 0x23 | 0x80, 0x02, 0x00, 0x00])
        orig_func, exc_code = parse_modbus_exception(frame)
        self.assertEqual(orig_func, 0x23)
        self.assertEqual(exc_code, 0x02)

    def test_parse_exception_write_func(self):
        frame = bytes([0x01, 0x16 | 0x80, 0x04, 0x00, 0x00])
        orig_func, exc_code = parse_modbus_exception(frame)
        self.assertEqual(orig_func, 0x16)
        self.assertEqual(exc_code, 0x04)


# ─── 7. Parsing ───────────────────────────────────────────────────────────────

class TestParsers(unittest.TestCase):
    """Valida decodificação de bytes para tipos Python."""

    def test_parse_int32_positive(self):
        data = struct.pack('<i', 3245)
        self.assertEqual(parse_int32(data), 3245)

    def test_parse_int32_negative(self):
        data = struct.pack('<i', -1000)
        self.assertEqual(parse_int32(data), -1000)

    def test_parse_int32_zero(self):
        self.assertEqual(parse_int32(b'\x00\x00\x00\x00'), 0)

    def test_parse_int32_wrong_size_raises(self):
        with self.assertRaises(IncompleteResponseError):
            parse_int32(b'\x01\x02\x03')

    def test_parse_float_value(self):
        value = 3.14
        data = struct.pack('<f', value)
        result = parse_float(data)
        self.assertAlmostEqual(result, value, places=5)

    def test_parse_float_wrong_size_raises(self):
        with self.assertRaises(IncompleteResponseError):
            parse_float(b'\x01\x02')

    def test_parse_string_valid(self):
        text = "hello"
        size_byte = bytes([len(text)])
        string_data = text.encode('utf-8')
        result = parse_string_response(size_byte, string_data)
        self.assertEqual(result, text)

    def test_parse_string_size_zero_raises(self):
        with self.assertRaises(InvalidSizeError):
            parse_string_response(bytes([0]), b'')

    def test_parse_string_size_mismatch_raises(self):
        with self.assertRaises(IncompleteResponseError):
            parse_string_response(bytes([5]), b'hi')

    def test_parse_modbus_payload(self):
        """Extrai bytes 3..-2 do frame (sem header e sem CRC)."""
        data = bytes([0x01, 0x23, 0xA1]) + b'\xAD\x0C\x00\x00' + bytes([0xAB, 0xCD])
        payload = parse_modbus_payload(data, payload_offset=3)
        self.assertEqual(payload, b'\xAD\x0C\x00\x00')


# ─── 8. Retry Logic ──────────────────────────────────────────────────────────

class TestRetryLogic(unittest.TestCase):
    """Valida comportamento de retry em caso de timeout e CRC inválido."""

    def _make_uart_mock(self, side_effects):
        """Cria mock de UARTController com side_effects para read_exact."""
        uart = MagicMock()
        uart.is_connected = True
        uart.read_exact = MagicMock(side_effect=side_effects)
        return uart

    def test_timeout_retries_3_times(self):
        """Em caso de UARTTimeoutError, deve tentar exatamente 3 vezes."""
        uart = self._make_uart_mock(
            [UARTTimeoutError("timeout")] * 3
        )
        with self.assertRaises(UARTTimeoutError):
            modbus_request_integer(uart)
        self.assertEqual(uart.read_exact.call_count, 3)

    def test_success_on_second_attempt(self):
        """Se primeira tentativa falha e segunda sucede, retorna valor."""
        # Resposta válida: [ADDR][FUNC][SUBCODE][INT32_LE][CRC_LO][CRC_HI]
        # Construir resposta válida para 0x23/0xA1, valor 42
        val = 42
        body = bytes([0x01, 0x23, 0xA1]) + struct.pack('<i', val)
        crc = calculate_crc(body)
        valid_response = body + crc  # 9 bytes

        uart = self._make_uart_mock([
            UARTTimeoutError("timeout"),
            valid_response,
        ])
        result = modbus_request_integer(uart)
        self.assertEqual(result, val)
        self.assertEqual(uart.read_exact.call_count, 2)

    def test_send_bytes_called_on_each_retry(self):
        """send_bytes deve ser chamado uma vez por tentativa."""
        uart = self._make_uart_mock(
            [UARTTimeoutError("timeout")] * 3
        )
        with self.assertRaises(UARTTimeoutError):
            modbus_request_integer(uart)
        self.assertEqual(uart.send_bytes.call_count, 3)

    def test_crc_error_triggers_retry(self):
        """Resposta com CRC inválido → ModbusCRCError → retry."""
        bad_response = bytes([0x01, 0x23, 0xA1, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xFF])  # CRC errado
        uart = self._make_uart_mock([bad_response] * 3)
        with self.assertRaises(ModbusCRCError):
            modbus_request_integer(uart)
        self.assertEqual(uart.read_exact.call_count, 3)


# ─── 9. Conformidade Protocolo Simplificado ──────────────────────────────────

class TestSimpleProtocolFrames(unittest.TestCase):
    """Valida os frames da Parte 1 (sem MODBUS, sem CRC)."""

    def test_request_packet_7_bytes(self):
        """Entrega_2.md §1.1: [CMD][D1..D6] = 7 bytes."""
        from src.uart_protocols.protocols.packet_utils import build_request_packet
        packet = build_request_packet(0xA1)
        self.assertEqual(len(packet), 7)

    def test_request_packet_starts_with_cmd(self):
        from src.uart_protocols.protocols.packet_utils import build_request_packet
        packet = build_request_packet(0xA2)
        self.assertEqual(packet[0], 0xA2)

    def test_request_packet_contains_matricula(self):
        from src.uart_protocols.protocols.packet_utils import build_request_packet
        packet = build_request_packet(0xA1)
        self.assertEqual(packet[1:7], MATRICULA)

    def test_send_int_packet_11_bytes(self):
        """Entrega_2.md §1.2: [0xB1][int32 LE][matricula] = 11 bytes."""
        from src.uart_protocols.protocols.packet_utils import build_send_int_packet
        packet = build_send_int_packet(0xB1, 100)
        self.assertEqual(len(packet), 11)

    def test_send_float_packet_11_bytes(self):
        from src.uart_protocols.protocols.packet_utils import build_send_float_packet
        packet = build_send_float_packet(0xB2, 3.14)
        self.assertEqual(len(packet), 11)

    def test_send_string_packet_size(self):
        """Entrega_2.md §1.2: [0xB3][N][string][matricula] = 8+N bytes."""
        from src.uart_protocols.protocols.packet_utils import build_send_string_packet
        for n in [1, 3, 10]:
            text = "x" * n
            packet = build_send_string_packet(0xB3, text)
            self.assertEqual(len(packet), 8 + n, f"N={n}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
