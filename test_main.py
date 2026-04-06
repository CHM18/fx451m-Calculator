import unittest

from main import (
    append_exponent_digit_to_value,
    append_mantissa_digit_to_value,
    convert_base_text_to_signed_decimal_text,
    evaluate_expression_tokens,
    format_base_value,
    get_base_display_limit,
    parse_base_value,
    replace_last_operator,
    signed_from_base_word,
    split_binary_rows,
    toggle_exponent_mode,
)


class CalculatorHelperTests(unittest.TestCase):
    def test_signed_from_base_word_uses_twos_complement(self):
        self.assertEqual(signed_from_base_word(0xFFFFFFFF), -1)
        self.assertEqual(signed_from_base_word(0x80000000), -2147483648)
        self.assertEqual(signed_from_base_word(0x7FFFFFFF), 2147483647)

    def test_format_base_value_enforces_16_digit_display_limit(self):
        self.assertEqual(format_base_value(0xFFFF, "BIN", max_digits=16), "1111111111111111")
        self.assertEqual(format_base_value(0xFFFFFFFF, "HEX", max_digits=8), "FFFFFFFF")
        with self.assertRaises(OverflowError):
            format_base_value(0x1FFFF, "BIN", max_digits=16)

    def test_base_limits_match_requested_32_bit_modes(self):
        self.assertEqual(get_base_display_limit("BIN"), 32)
        self.assertEqual(get_base_display_limit("OCT"), 10)
        self.assertEqual(get_base_display_limit("DEC"), 10)
        self.assertEqual(get_base_display_limit("HEX"), 8)

    def test_split_binary_rows_formats_32_bits(self):
        top_row, bottom_row = split_binary_rows("101")
        self.assertEqual(top_row, "0000000000000000")
        self.assertEqual(bottom_row, "0000000000000101")

        top_row, bottom_row = split_binary_rows("1" * 32)
        self.assertEqual(top_row, "1111111111111111")
        self.assertEqual(bottom_row, "1111111111111111")

        with self.assertRaises(OverflowError):
            split_binary_rows("1" * 33)

    def test_all_ones_hex_converts_to_expected_oct_and_bin(self):
        value = parse_base_value("FFFFFFFF", "HEX")
        self.assertEqual(format_base_value(value, "OCT"), "7777777777")
        self.assertEqual(format_base_value(value, "BIN"), "1" * 32)

    def test_exp_toggle_returns_to_mantissa_editing(self):
        current, editing_exponent = toggle_exponent_mode("1", False)
        self.assertEqual(current, "1e0")
        self.assertTrue(editing_exponent)

        current, editing_exponent = toggle_exponent_mode(current, editing_exponent)
        self.assertEqual(current, "1e0")
        self.assertFalse(editing_exponent)

        updated, handled = append_mantissa_digit_to_value(current, "2")
        self.assertTrue(handled)
        self.assertEqual(updated, "12e0")

    def test_exponent_digits_are_limited_to_three(self):
        value = "1e0"
        for digit in "123":
            value = append_exponent_digit_to_value(value, digit)
        self.assertEqual(value, "1e123")
        self.assertEqual(append_exponent_digit_to_value(value, "4"), "1e123")

    def test_repeated_operator_press_keeps_only_last_operator(self):
        updated_tokens, replaced = replace_last_operator([1, "AND"], "XOR")
        self.assertTrue(replaced)
        self.assertEqual(updated_tokens, [1, "XOR"])

        updated_tokens, replaced = replace_last_operator([1], "OR")
        self.assertFalse(replaced)
        self.assertEqual(updated_tokens, [1, "OR"])

    def test_base_expression_uses_casio_style_bitwise_precedence(self):
        result = evaluate_expression_tokens([1, "OR", 2, "AND", 3, "XOR", 4], base_mode=True)
        self.assertEqual(result, 7)

    def test_base_expression_keeps_arithmetic_above_bitwise(self):
        result = evaluate_expression_tokens([2, "+", 3, "AND", 6], base_mode=True)
        self.assertEqual(result, 4)

    def test_overflowed_binary_text_converts_back_to_decimal_text(self):
        self.assertEqual(
            convert_base_text_to_signed_decimal_text("11111111111111111", "BIN"),
            "131071",
        )


if __name__ == "__main__":
    unittest.main()