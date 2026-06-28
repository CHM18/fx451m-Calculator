import unittest
import math
from decimal import Decimal

from main import (
    _safe_cos,
    _safe_sin,
    _safe_tan,
    append_exponent_digit_to_value,
    append_mantissa_digit_to_value,
    calc_binary_value,
    calc_extra_unary_value,
    convert_standard_text_to_base_word,
    convert_base_text_to_signed_decimal_text,
    evaluate_expression_tokens,
    format_base_value,
    format_decimal_number,
    get_base_display_limit,
    parse_base_value,
    replace_last_operator,
    rounded_decimal_for_display_exponent,
    signed_from_base_word,
    simulate_standard_button_sequence,
    should_keep_current_on_equals,
    split_binary_rows,
    toggle_exponent_mode,
)


class CalculatorHelperTests(unittest.TestCase):
    def test_safe_sin_is_exact_zero_for_integer_pi_multiples(self):
        for k in [0, 1, 2, 7, 1234, -1, -9, -777]:
            self.assertEqual(_safe_sin(k * math.pi), 0.0)

    def test_safe_sin_snaps_display_rounded_two_pi_to_zero(self):
        # 2*pi rounded to 12 significant digits as shown on display.
        self.assertEqual(_safe_sin(6.28318530718), 0.0)

    def test_safe_sin_is_exact_zero_for_display_rounded_n_pi_up_to_50(self):
        for n in range(0, 51):
            rounded_input = float(f"{n * math.pi:.12g}")
            self.assertEqual(_safe_sin(rounded_input), 0.0)

    def test_safe_tan_is_exact_zero_for_integer_pi_multiples(self):
        for k in [0, 1, 2, 7, 1234, -1, -9, -777]:
            self.assertEqual(_safe_tan(k * math.pi), 0.0)

    def test_safe_tan_snaps_display_rounded_two_pi_to_zero(self):
        self.assertEqual(_safe_tan(6.28318530718), 0.0)

    def test_safe_tan_is_exact_zero_for_display_rounded_n_pi_up_to_50(self):
        for n in range(0, 51):
            rounded_input = float(f"{n * math.pi:.12g}")
            self.assertEqual(_safe_tan(rounded_input), 0.0)

    def test_safe_cos_is_exact_zero_for_odd_half_pi_multiples(self):
        for k in [0, 1, 2, 7, 1234, -1, -9, -777]:
            x = (2 * k + 1) * math.pi / 2
            self.assertEqual(_safe_cos(x), 0.0)

    def test_safe_sin_does_not_snap_nearby_nonzero_value(self):
        x = 10 * math.pi + 1e-9
        self.assertNotEqual(_safe_sin(x), 0.0)

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

    def test_large_power_is_finite_decimal(self):
        result = calc_binary_value(Decimal("1e199"), 5, "^")
        self.assertIsInstance(result, Decimal)
        self.assertTrue(result.is_finite())
        self.assertEqual(format_decimal_number(result), "1e995")

    def test_expression_large_power_is_finite_decimal(self):
        # Regression: 1 EXP 199 x^y 5 should remain displayable.
        result = evaluate_expression_tokens(["1e199", "^", 5])
        self.assertIsInstance(result, Decimal)
        self.assertTrue(result.is_finite())
        self.assertEqual(format_decimal_number(result), "1e995")

    def test_large_sqrt_is_finite_decimal(self):
        # Regression: 1 EXP 999 sqrt should not collapse to inf.
        result = calc_extra_unary_value(Decimal("1e999"), "sqrt")
        self.assertIsInstance(result, Decimal)
        self.assertTrue(result.is_finite())
        self.assertEqual(format_decimal_number(result), "3.16227766017e499")

    def test_large_square_is_finite_decimal(self):
        # Regression: 1 EXP 499 x^2 should remain displayable.
        result = calc_extra_unary_value(Decimal("1e499"), "x^2")
        self.assertIsInstance(result, Decimal)
        self.assertTrue(result.is_finite())
        self.assertEqual(format_decimal_number(result), "1e998")

    def test_large_power_with_user_reported_input_is_finite(self):
        # Regression: 1 EXP 199 x^y 5 should stay finite and displayable.
        result = calc_binary_value(Decimal("1e199"), 5, "^")
        self.assertIsInstance(result, Decimal)
        self.assertTrue(result.is_finite())
        self.assertEqual(format_decimal_number(result), "1e995")

    def test_display_caps_exponent_above_999_to_inf(self):
        self.assertEqual(format_decimal_number(Decimal("1e1000")), "inf")
        self.assertEqual(format_decimal_number(Decimal("-1e1000")), "-inf")

    def test_display_caps_exponent_below_minus_999_to_zero(self):
        self.assertEqual(format_decimal_number(Decimal("1e-1000")), "0")

    def test_display_rounding_keeps_negative_boundary_from_falling_to_zero(self):
        boundary_value = calc_extra_unary_value(calc_extra_unary_value(Decimal("1e-999"), "sqrt"), "x^2")
        rounded = rounded_decimal_for_display_exponent(boundary_value)
        self.assertEqual(rounded.adjusted(), -999)
        self.assertEqual(format_decimal_number(boundary_value), "1e-999")

    def test_large_scientific_text_converts_to_base_word_without_float_overflow(self):
        # Regression: switching Std -> Base with 1e310 should not crash.
        result = convert_standard_text_to_base_word("1e310")
        expected = int(Decimal("1e310")) & 0xFFFFFFFF
        self.assertEqual(result, expected)


class CalculatorUiSequenceIntegrationTests(unittest.TestCase):
    def test_e2e_large_sqrt_sequence(self):
        result = simulate_standard_button_sequence(["1", "EXP", "999", "sqrt"])
        self.assertNotEqual(result, "inf")
        self.assertTrue(Decimal(result).is_finite())
        self.assertEqual(result, "3.16227766017e499")

    def test_e2e_large_square_sequence(self):
        result = simulate_standard_button_sequence(["1", "EXP", "499", "x^2"])
        self.assertEqual(result, "1e998")

    def test_e2e_large_square_caps_to_inf(self):
        # Regression: 1 EXP 999 x^2 should display inf.
        result = simulate_standard_button_sequence(["1", "EXP", "999", "x^2"])
        self.assertEqual(result, "inf")

    def test_e2e_large_negative_exponent_boundary_stays_visible(self):
        # Regression: 1 EXP +/- 999 sqrt x^2 should remain at 1e-999, not underflow to 0.
        result = simulate_standard_button_sequence(["1", "EXP", "+/-", "999", "sqrt", "x^2"])
        self.assertEqual(result, "1e-999")

    def test_e2e_true_underflow_caps_to_zero(self):
        result = simulate_standard_button_sequence(["1", "EXP", "999", "1/x", "x^2"])
        self.assertEqual(result, "0")

    def test_e2e_large_power_sequence(self):
        result = simulate_standard_button_sequence(["1", "EXP", "199", "x^y", "5", "="])
        self.assertEqual(result, "1e995")

    def test_e2e_large_power_preview_does_not_show_inf(self):
        result = simulate_standard_button_sequence(["1", "EXP", "999", "x^y"])
        self.assertEqual(result, "1e999")

    def test_e2e_divide_by_zero_shows_error(self):
        result = simulate_standard_button_sequence(["1", "/", "0", "="])
        self.assertEqual(result, "Error")

    def test_e2e_incomplete_power_expression_shows_error(self):
        result = simulate_standard_button_sequence(["1", "x^y", "="])
        self.assertEqual(result, "Error")

    def test_e2e_reciprocal_zero_shows_error(self):
        result = simulate_standard_button_sequence(["0", "1/x"])
        self.assertEqual(result, "Error")

    def test_e2e_sqrt_of_negative_result_shows_error(self):
        result = simulate_standard_button_sequence(["1", "-", "2", "=", "sqrt"])
        self.assertEqual(result, "Error")

    def test_e2e_incomplete_addition_expression_shows_error(self):
        result = simulate_standard_button_sequence(["1", "+", "="])
        self.assertEqual(result, "Error")

    def test_e2e_reciprocal_of_computed_zero_shows_error(self):
        result = simulate_standard_button_sequence(["2", "-", "2", "=", "1/x"])
        self.assertEqual(result, "Error")

    def test_equals_without_pending_tokens_keeps_large_scientific_literal(self):
        # Regression: 1 EXP 900 = should keep the literal instead of forcing float conversion.
        self.assertTrue(should_keep_current_on_equals([], "1e900"))
        self.assertFalse(should_keep_current_on_equals(["+"], "1e900"))

    def test_overflowed_binary_text_converts_back_to_decimal_text(self):
        self.assertEqual(
            convert_base_text_to_signed_decimal_text("11111111111111111", "BIN"),
            "131071",
        )


if __name__ == "__main__":
    unittest.main()