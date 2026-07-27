"""
fx451m Calculator
A calculator with basic arithmetic and trigonometric/hyperbolic functions using Flet.
Works on desktop (Windows/Mac/Linux) and can be built for Android with: flet build apk
"""

import math
from decimal import Decimal, DivisionByZero, InvalidOperation, Overflow as DecimalOverflow, localcontext
import flet as ft


BASE_SYSTEMS = {"DEC": 10, "BIN": 2, "OCT": 8, "HEX": 16}
BASE_BINARY_OPS = {"AND", "OR", "XOR", "XNOR"}
BINARY_OPS = {"+", "-", "*", "/", "^", *BASE_BINARY_OPS}
OP_PRECEDENCE = {
    "OR": 1,
    "XOR": 2,
    "XNOR": 2,
    "AND": 3,
    "+": 4,
    "-": 4,
    "*": 5,
    "/": 5,
    "^": 6,
}
BASE_WORD_BITS = 32
BASE_WORD_MASK = (1 << BASE_WORD_BITS) - 1
MAX_DIGITS = 12
BASE_DISPLAY_LIMITS = {"BIN": 32, "OCT": 10, "DEC": 10, "HEX": 8}
BASE_FORMAT_BITS = {"BIN": 32, "OCT": 30, "DEC": 32, "HEX": 32}
MAX_EXPONENT_DIGITS = 3
DISPLAY_SIGNIFICANT_DIGITS = 12
ZERO_SNAP_FACTOR = 4096.0
TRIG_ZERO_ABS_TOL = 5e-13
TRIG_ZERO_REL_TOL = 5e-12


def count_digits(value):
    return sum(1 for char in value if char.isdigit())


def split_sign_prefix(value):
    text = value or ""
    if text.startswith("-"):
        return "-", text[1:]
    return "", text


def group_digits_for_display(value, separator="\u200A"):
    text = value or ""
    if text in {"", "Error"}:
        return text

    integer_part, dot, fractional_part = text.partition(".")

    if integer_part.isdigit():
        integer_groups = []
        remaining = integer_part
        while remaining:
            integer_groups.append(remaining[-3:])
            remaining = remaining[:-3]
        integer_part = separator.join(reversed(integer_groups))

    if not dot:
        return integer_part

    if not fractional_part:
        return f"{integer_part}."

    if not fractional_part.isdigit():
        return text

    fractional_groups = [
        fractional_part[index:index + 3]
        for index in range(0, len(fractional_part), 3)
    ]
    return f"{integer_part}.{separator.join(fractional_groups)}"


def _plain_decimal_text(value):
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in {"", "-0", "+0"}:
        return "0"
    return text


def _snap_near_zero(value, scale=1.0):
    tolerance = ZERO_SNAP_FACTOR * math.ulp(1.0) * max(1.0, abs(scale))
    return 0.0 if abs(value) <= tolerance else value


def _trig_zero_tolerance(x):
    return max(TRIG_ZERO_ABS_TOL, TRIG_ZERO_REL_TOL * max(1.0, abs(x)))


def _near_periodic_zero(x, period, offset=0.0):
    delta = math.remainder(x - offset, period)
    return abs(delta) <= _trig_zero_tolerance(x)


def _safe_sin(x):
    """sin(x) with exact zeros at integer multiples of π."""
    if _near_periodic_zero(x, math.pi):
        return 0.0

    n = round(2 * x / math.pi)
    r = x - n * (math.pi / 2)
    n_mod = int(n) % 4
    if n_mod == 0:
        return _snap_near_zero(math.sin(r), scale=x)
    elif n_mod == 1:
        return math.cos(r)
    elif n_mod == 2:
        return _snap_near_zero(-math.sin(r), scale=x)
    else:
        return -math.cos(r)


def _safe_cos(x):
    """cos(x) with exact zeros at odd multiples of π/2."""
    if _near_periodic_zero(x, math.pi, offset=(math.pi / 2)):
        return 0.0

    n = round(2 * x / math.pi)
    r = x - n * (math.pi / 2)
    n_mod = int(n) % 4
    if n_mod == 0:
        return math.cos(r)
    elif n_mod == 1:
        return _snap_near_zero(-math.sin(r), scale=x)
    elif n_mod == 2:
        return -math.cos(r)
    else:
        return _snap_near_zero(math.sin(r), scale=x)


def _safe_tan(x):
    """tan(x) with exact zeros at integer multiples of π."""
    if _near_periodic_zero(x, math.pi):
        return 0.0

    n = round(x / math.pi)
    r = x - n * math.pi
    return _snap_near_zero(math.tan(r), scale=x)


def rounded_decimal_for_display_exponent(value, significant_digits=DISPLAY_SIGNIFICANT_DIGITS):
    """Round Decimal to display precision before exponent limit checks."""
    if value.is_zero() or not value.is_finite():
        return value
    with localcontext() as ctx:
        ctx.prec = max(50, significant_digits + 5)
        rounded_text = format(value, f".{significant_digits}g")
    return Decimal(rounded_text)


def format_decimal_number(value):
    if isinstance(value, Decimal):
        if value.is_zero():
            return "0"
        if not value.is_finite():
            return "-inf" if value.is_signed() else "inf"

        # Keep calculator-style display limits for scientific exponents.
        rounded_value = rounded_decimal_for_display_exponent(value)
        adjusted_exponent = rounded_value.adjusted()
        if adjusted_exponent > 999:
            return "-inf" if value.is_signed() else "inf"
        if adjusted_exponent < -999:
            return "0"

        # Prefer plain decimal when the rounded value fits the 12-digit display.
        plain_text = _plain_decimal_text(rounded_value)
        if count_digits(plain_text.lstrip("-")) <= DISPLAY_SIGNIFICANT_DIGITS:
            return plain_text

        normalized = rounded_value.normalize()
        text = format(normalized, "g")
        if "e" in text.lower():
            mantissa, exponent = text.lower().split("e", 1)
            text = f"{mantissa}e{int(exponent)}"
        return text
    if value == 0:
        return "0"
    return f"{value:.17g}"


def to_decimal(value):
    if isinstance(value, Decimal):
        return value
    return Decimal(str(value))


def normalize_base_value(value):
    return int(value) & BASE_WORD_MASK


def get_base_format_bits(base_name):
    return BASE_FORMAT_BITS[base_name]


def normalize_base_value_for_format(value, base_name):
    bit_count = get_base_format_bits(base_name)
    mask = (1 << bit_count) - 1
    return int(value) & mask


def signed_from_base_word(value):
    normalized = normalize_base_value(value)
    sign_bit = 1 << (BASE_WORD_BITS - 1)
    if normalized & sign_bit:
        return normalized - (1 << BASE_WORD_BITS)
    return normalized


def format_base_value(value, base_name, max_digits=None):
    base_value = BASE_SYSTEMS[base_name]
    unsigned_value = normalize_base_value_for_format(value, base_name)
    if unsigned_value == 0:
        result = "0"
    else:
        digits = "0123456789ABCDEF"
        parts = []
        while unsigned_value > 0:
            unsigned_value, remainder = divmod(unsigned_value, base_value)
            parts.append(digits[remainder])
        result = "".join(reversed(parts))

    if max_digits is not None and len(result) > max_digits:
        raise OverflowError("Base display overflow")
    return result


def get_base_display_limit(base_name):
    return BASE_DISPLAY_LIMITS[base_name]


def parse_base_value(text, base_name):
    cleaned = (text or "").strip().upper()
    if cleaned == "":
        raise ValueError("Incomplete base input")
    raw_value = int(cleaned, BASE_SYSTEMS[base_name])
    bit_count = get_base_format_bits(base_name)
    mask = (1 << bit_count) - 1
    normalized = raw_value & mask

    if base_name == "OCT":
        sign_bit = 1 << (bit_count - 1)
        if normalized & sign_bit:
            extension_mask = BASE_WORD_MASK ^ mask
            normalized |= extension_mask

    return normalize_base_value(normalized)


def split_binary_rows(text):
    if text == "Error":
        return "", "Error"
    padded = (text or "0").rjust(get_base_display_limit("BIN"), "0")
    if len(padded) > get_base_display_limit("BIN"):
        raise OverflowError("Binary display overflow")
    return padded[:16], padded[16:]


def parse_scientific_parts(value):
    if not value or value == "Error":
        return value, ""
    if "e" not in value.lower():
        return value, ""
    mantissa, exponent = value.lower().split("e", 1)
    return mantissa, exponent


def compose_scientific_parts(mantissa, exponent):
    if exponent in ("", None):
        return mantissa
    return f"{mantissa}e{exponent}"


def should_keep_current_on_equals(tokens, current):
    if tokens:
        return False
    return bool(current and current not in {"Error", "-"})


def toggle_exponent_mode(current, editing_exponent):
    if not current or current == "Error":
        return current, editing_exponent
    if editing_exponent:
        return current, False
    mantissa, exponent = parse_scientific_parts(current)
    return compose_scientific_parts(mantissa, exponent or "0"), True


def append_exponent_digit_to_value(current, digit):
    mantissa, exponent = parse_scientific_parts(current)
    sign = "-" if exponent.startswith("-") else ""
    digits = exponent.lstrip("-")
    if digits == "0":
        digits = ""
    if len(digits) >= MAX_EXPONENT_DIGITS:
        return current
    digits += digit
    return compose_scientific_parts(mantissa, f"{sign}{digits or '0'}")


def append_mantissa_digit_to_value(current, char, max_digits=MAX_DIGITS):
    if not current or current == "Error" or "e" not in current.lower():
        return current, False

    mantissa, exponent = parse_scientific_parts(current)

    if char == ".":
        if "." in mantissa:
            return current, True
        if mantissa == "":
            mantissa = "0"
        elif mantissa == "-":
            mantissa = "-0"
    else:
        if mantissa == "0":
            mantissa = ""
        elif mantissa == "-0":
            mantissa = "-"
        if count_digits(mantissa) >= max_digits:
            return current, True

    mantissa += char
    return compose_scientific_parts(mantissa, exponent), True


def replace_last_operator(tokens, op):
    updated_tokens = list(tokens)
    replaced = bool(updated_tokens and updated_tokens[-1] in BINARY_OPS)
    if replaced:
        updated_tokens[-1] = op
    else:
        updated_tokens.append(op)
    return updated_tokens, replaced


def calc_binary_value(a, b, op, base_mode=False):
    if op == "+":
        if base_mode:
            return normalize_base_value(int(a) + int(b))
        return to_decimal(a) + to_decimal(b)
    if op == "-":
        if base_mode:
            return normalize_base_value(int(a) - int(b))
        return to_decimal(a) - to_decimal(b)
    if op == "*":
        if base_mode:
            return normalize_base_value(int(a) * int(b))
        return to_decimal(a) * to_decimal(b)
    if op == "/":
        if b == 0:
            raise ValueError("Division by zero")
        if base_mode:
            return normalize_base_value(int(int(a) / int(b)))
        with localcontext() as ctx:
            ctx.prec = 80
            return to_decimal(a) / to_decimal(b)
    if op == "^":
        if base_mode:
            return normalize_base_value(int(a) ** int(b))
        decimal_a = to_decimal(a)
        decimal_b = to_decimal(b)
        integral_b = decimal_b == decimal_b.to_integral_value()
        if integral_b:
            exponent_int = int(decimal_b)
            try:
                with localcontext() as ctx:
                    ctx.prec = 80
                    return decimal_a ** exponent_int
            except (DecimalOverflow, InvalidOperation):
                if exponent_int < 0:
                    return Decimal("0")
                if decimal_a.is_signed() and exponent_int % 2 != 0:
                    return Decimal("-Infinity")
                return Decimal("Infinity")
        try:
            return a ** b
        except OverflowError:
            if a < 0 and float(b).is_integer() and int(b) % 2 != 0:
                return -math.inf
            return math.inf
    if op == "AND":
        return normalize_base_value(int(a) & int(b))
    if op == "OR":
        return normalize_base_value(int(a) | int(b))
    if op == "XOR":
        return normalize_base_value(int(a) ^ int(b))
    if op == "XNOR":
        return normalize_base_value(~(int(a) ^ int(b)))
    raise ValueError(f"Unknown operator: {op}")


def calc_extra_unary_value(x, func):
    is_decimal = isinstance(x, Decimal)
    if func == "1/x":
        if x == 0:
            raise ValueError("Division by zero")
        if is_decimal:
            with localcontext() as ctx:
                ctx.prec = 80
                return Decimal("1") / x
        return 1 / x
    if func == "sqrt":
        if x < 0:
            raise ValueError("Domain error")
        if is_decimal:
            with localcontext() as ctx:
                ctx.prec = 80
                return x.sqrt(context=ctx)
        return math.sqrt(x)
    if func == "x^2":
        return x * x
    if func == "log":
        if x <= 0:
            raise ValueError("Domain error")
        return math.log10(x)
    if func == "ln":
        if x <= 0:
            raise ValueError("Domain error")
        return math.log(x)
    if func == "e^x":
        return math.exp(x)
    if func == "x!":
        if x < 0 or x != int(x):
            raise ValueError("Domain error")
        return math.factorial(int(x))
    raise ValueError(f"Unknown function: {func}")


def evaluate_expression_tokens(tokens, base_mode=False):
    values = []
    operators = []

    def apply_top_operator():
        if len(values) < 2 or not operators:
            raise ValueError("Invalid expression")
        op = operators.pop()
        right = values.pop()
        left = values.pop()
        values.append(calc_binary_value(left, right, op, base_mode=base_mode))

    for token in tokens:
        if token == "(":
            operators.append(token)
        elif token == ")":
            while operators and operators[-1] != "(":
                apply_top_operator()
            if not operators or operators[-1] != "(":
                raise ValueError("Mismatched brackets")
            operators.pop()
        elif token in BINARY_OPS:
            while operators and operators[-1] in BINARY_OPS:
                top = operators[-1]
                if OP_PRECEDENCE[top] > OP_PRECEDENCE[token] or (
                    OP_PRECEDENCE[top] == OP_PRECEDENCE[token] and token != "^"
                ):
                    apply_top_operator()
                else:
                    break
            operators.append(token)
        else:
            if isinstance(token, (int, float)):
                values.append(token)
            elif isinstance(token, Decimal):
                values.append(token)
            else:
                values.append(Decimal(str(token)))

    while operators:
        if operators[-1] == "(":
            raise ValueError("Mismatched brackets")
        apply_top_operator()

    if len(values) != 1:
        raise ValueError("Invalid expression")
    return values[0]


def convert_base_text_to_signed_decimal_text(text, base_name):
    return format_decimal_number(signed_from_base_word(parse_base_value(text, base_name)))


def convert_standard_text_to_base_word(text):
    cleaned = (text or "").strip()
    if cleaned in {"", "Error"}:
        return 0

    try:
        numeric_value = to_decimal(cleaned)
        if not numeric_value.is_finite():
            return 0
        return normalize_base_value(int(numeric_value))
    except (InvalidOperation, ValueError, OverflowError):
        return 0


def simulate_standard_button_sequence(buttons):
    """Simulate normal-mode button presses for integration testing of core calculator flows."""
    state = {
        "current": "",
        "display_value": "",
        "tokens": [],
        "editing_exponent": False,
        "replace_on_next_input": False,
        "last_was_equals": False,
    }

    def clear_like_ac():
        state["current"] = "0"
        state["display_value"] = ""
        state["tokens"] = []
        state["editing_exponent"] = False
        state["replace_on_next_input"] = False
        state["last_was_equals"] = False

    def can_push_current():
        return bool(state["current"] and state["current"] not in {"Error", "-"})

    for raw_button in buttons:
        char = str(raw_button)

        if char in {"EXP", "exp"}:
            updated_current, editing_exponent = toggle_exponent_mode(
                state["current"], state["editing_exponent"]
            )
            state["current"] = updated_current
            state["display_value"] = ""
            state["editing_exponent"] = editing_exponent
            state["replace_on_next_input"] = False
            if editing_exponent:
                state["last_was_equals"] = False
            continue

        if char == "+/-":
            current = state["current"]
            if not current or current == "Error":
                continue

            if state["editing_exponent"]:
                mantissa, exponent = parse_scientific_parts(current)
                digits = exponent.lstrip("-") or "0"
                new_exponent = digits if exponent.startswith("-") else f"-{digits}"
                state["current"] = compose_scientific_parts(mantissa, new_exponent)
                state["display_value"] = ""
                continue

            if current.startswith("-"):
                state["current"] = current[1:]
            elif current != "0":
                state["current"] = f"-{current}"
            state["display_value"] = ""
            continue

        if char.isdigit() or char == ".":
            if state["editing_exponent"]:
                if char.isdigit():
                    state["current"] = append_exponent_digit_to_value(state["current"], char)
                    state["display_value"] = ""
                continue

            if state["replace_on_next_input"]:
                state["current"] = ""
                state["display_value"] = ""
                state["replace_on_next_input"] = False

            if state["last_was_equals"] and char.isdigit():
                clear_like_ac()
            state["last_was_equals"] = False

            if state["current"] == "Error":
                state["current"] = ""

            if char.isdigit() and state["current"] == "0":
                state["current"] = ""

            if char == "." and "." in state["current"]:
                continue
            if char == "." and state["current"] == "":
                state["current"] = "0"

            updated_current, handled = append_mantissa_digit_to_value(
                state["current"], char, max_digits=MAX_DIGITS
            )
            if handled:
                state["current"] = updated_current
                state["display_value"] = ""
                continue

            if char.isdigit() and count_digits(state["current"]) >= MAX_DIGITS:
                continue

            state["current"] += char
            state["display_value"] = ""
            continue

        if char in {"x^y", "^", "+", "-", "*", "/"}:
            op = "^" if char == "x^y" else char
            if state["current"] == "Error":
                continue

            if state["editing_exponent"]:
                state["editing_exponent"] = False

            preview_value = state["display_value"] or state["current"] or "0"
            if can_push_current():
                preview_value = state["current"]
                state["tokens"].append(to_decimal(state["current"]))
                state["current"] = ""

            if state["tokens"] and state["tokens"][-1] in BINARY_OPS:
                state["tokens"][-1] = op
                state["display_value"] = preview_value
                state["replace_on_next_input"] = True
                state["last_was_equals"] = False
            elif state["tokens"]:
                state["tokens"].append(op)
                state["display_value"] = preview_value
                state["replace_on_next_input"] = True
                state["last_was_equals"] = False
            continue

        if char in {"1/x", "sqrt", "x^2"}:
            if state["current"] and state["current"] != "Error":
                try:
                    result = calc_extra_unary_value(to_decimal(state["current"]), char)
                    state["current"] = format_decimal_number(result)
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                except (ValueError, ZeroDivisionError, OverflowError, InvalidOperation, DivisionByZero):
                    state["current"] = "Error"
                    state["display_value"] = ""
                    state["editing_exponent"] = False
            continue

        if char == "=":
            try:
                tokens = list(state["tokens"])
                if should_keep_current_on_equals(tokens, state["current"]):
                    state["display_value"] = ""
                    state["tokens"] = []
                    state["editing_exponent"] = False
                    state["replace_on_next_input"] = True
                    state["last_was_equals"] = True
                    continue

                if can_push_current():
                    tokens.append(to_decimal(state["current"]))
                if not tokens:
                    continue
                if tokens[-1] in BINARY_OPS or tokens[-1] == "(":
                    raise ValueError("Incomplete expression")

                result = evaluate_expression_tokens(tokens, base_mode=False)
                state["current"] = format_decimal_number(result)
                state["display_value"] = ""
                state["tokens"] = []
                state["editing_exponent"] = False
                state["replace_on_next_input"] = True
                state["last_was_equals"] = True
            except (ValueError, ZeroDivisionError, OverflowError, InvalidOperation, DivisionByZero):
                state["current"] = "Error"
                state["display_value"] = ""
                state["tokens"] = []
                state["editing_exponent"] = False
                state["replace_on_next_input"] = False
                state["last_was_equals"] = False
            continue

    return state["display_value"] or state["current"] or "0"


def main(page: ft.Page):
    page.title = "fx451m Calculator"
    page.padding = 0
    page.bgcolor = ft.Colors.BLACK

    windows_landscape_width = 720
    windows_landscape_height = 380
    windows_portrait_width = 420
    windows_portrait_height = 755

    if page.platform == ft.PagePlatform.WINDOWS:
        # Start desktop in landscape and keep a fixed size.
        page.window.width = windows_landscape_width
        page.window.height = windows_landscape_height
        page.window.resizable = False
    else:
        page.window.width = windows_portrait_width
        page.window.height = windows_portrait_height

    # Try to set a native window icon on Windows desktop builds.
    try:
        import sys, os

        def _resource_path(name: str) -> str:
            if getattr(sys, "frozen", False):
                base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            else:
                base = os.path.dirname(__file__)
            return os.path.join(base, name)

        if page.platform == ft.PagePlatform.WINDOWS:
            ico_path = _resource_path("icon.ico")
            if os.path.exists(ico_path):
                page.window.icon = ico_path
    except Exception:
        # Non-critical; continue if setting icon fails
        pass

    is_android = page.platform == ft.PagePlatform.ANDROID
    is_windows = page.platform == ft.PagePlatform.WINDOWS
    haptic_feedback = ft.HapticFeedback() if is_android else None
    clipboard_service = ft.Clipboard()

    async def trigger_key_haptic_feedback():
        if haptic_feedback is None:
            return
        try:
            await haptic_feedback.selection_click()
        except Exception:
            # Keep key processing uninterrupted if haptic feedback is unavailable.
            return

    def trigger_key_feedback():
        if is_android:
            page.run_task(trigger_key_haptic_feedback)

    def get_pressed_button_bg(base_bg):
        if base_bg == ft.Colors.GREY_200:
            return ft.Colors.GREY_300
        if base_bg == ft.Colors.ORANGE_200:
            return ft.Colors.ORANGE_300
        if base_bg == ft.Colors.BLUE_200:
            return ft.Colors.BLUE_300
        if base_bg == ft.Colors.RED_200:
            return ft.Colors.RED_300
        return base_bg

    # --- Calculator state ---
    state = {
        "current": "",
        "display_value": "",
        "op": "",
        "first": 0.0,
        "tokens": [],
        "memory": Decimal("0"),
        "has_memory": False,
        "mode": "Rad",
        "base_mode": "Normal",
        "base_format": "DEC",
        "editing_exponent": False,
        "replace_on_next_input": False,
        "last_was_equals": False,
    }

    TRIG_FUNCS = {
        "sin", "cos", "tan", "cot",
        "asin", "acos", "atan", "acot",
        "sinh", "cosh", "tanh", "coth",
        "asinh", "acosh", "atanh", "acoth",
    }
    EXTRA_UNARY_FUNCS = {"1/x", "sqrt", "x^2", "log", "ln", "e^x", "x!"}
    CONSTANTS = {
        "CONST_PI": math.pi,
        "CONST_C": 299792458,
        "CONST_H": 6.62607015e-34,
        "CONST_G": 6.67430e-11,
    }
    NORMAL_FUNCTION_LAYOUT = [
        ["sin", "cos", "tan", "cot"],
        ["asin", "acos", "atan", "acot"],
        ["sinh", "cosh", "tanh", "coth"],
        ["asinh", "acosh", "atanh", "acoth"],
    ]
    BASE_FUNCTION_LAYOUT = [
        ["DEC", "BIN", "OCT", "HEX"],
        ["NEG", "A", "B", "C"],
        ["NOT", "D", "E", "F"],
        ["AND", "OR", "XOR", "XNOR"],
    ]
    def digit_count(value):
        return count_digits(value)

    def format_number(value):
        return format_decimal_number(value)

    def is_base_mode_active():
        return state["base_mode"] == "Base"

    def normalize_base_word(value):
        return normalize_base_value(value)

    def base_word_to_signed(value):
        return signed_from_base_word(value)

    def get_active_base_name():
        return state["base_format"]

    def get_active_base_value():
        return BASE_SYSTEMS[get_active_base_name()]

    def format_result_value(value):
        if is_base_mode_active():
            return format_base_integer(normalize_base_word(value))
        return format_number(value)

    def format_base_integer(value, base_name=None):
        base_name = base_name or get_active_base_name()
        return format_base_value(value, base_name)

    def parse_base_integer(text, base_name=None):
        base_name = base_name or get_active_base_name()
        return parse_base_value(text, base_name)

    def convert_base_display(text, from_base, to_base):
        if not text or text == "Error":
            return text
        return format_base_integer(parse_base_integer(text, from_base), to_base)

    def current_numeric_value():
        if is_base_mode_active():
            return parse_base_integer(state["current"] or "0")
        return to_decimal(state["current"])

    def set_current_from_numeric(value):
        if is_base_mode_active():
            state["current"] = format_base_integer(normalize_base_word(value))
        else:
            state["current"] = format_number(value)

    def can_use_current_display_value():
        if not state["display_value"] or state["display_value"] == "Error":
            return False
        return True

    def adopt_display_value_as_current():
        if can_use_current_display_value() and not can_push_current():
            state["current"] = state["display_value"]
            state["display_value"] = ""
            state["replace_on_next_input"] = False

    def is_allowed_base_digit(char):
        base_name = get_active_base_name()
        if base_name == "BIN":
            return char in "01"
        if base_name == "OCT":
            return char in "01234567"
        if base_name == "DEC":
            return char in "0123456789"
        return char in "0123456789ABCDEF"

    def base_input_count(value):
        return sum(1 for char in value if char.isalnum())

    def handle_base_digit_input(char):
        char = char.upper()
        if char == "." or not is_allowed_base_digit(char):
            return

        if state["replace_on_next_input"]:
            state["current"] = ""
            state["display_value"] = ""
            state["replace_on_next_input"] = False

        if state["last_was_equals"]:
            clear()

        if state["current"] == "Error":
            state["current"] = ""

        if state["current"] == "0":
            state["current"] = ""
        elif state["current"] == "-0":
            state["current"] = "-"

        if base_input_count(state["current"]) >= get_base_display_limit(get_active_base_name()):
            return

        state["current"] += char
        state["display_value"] = ""
        state["last_was_equals"] = False
        update_display()

    def change_base_format(new_base_name):
        old_base_name = state["base_format"]
        if old_base_name == new_base_name:
            return

        if state["current"] and state["current"] != "Error":
            state["current"] = convert_base_display(state["current"], old_base_name, new_base_name)
        if state["display_value"] and state["display_value"] != "Error":
            state["display_value"] = convert_base_display(state["display_value"], old_base_name, new_base_name)

        state["base_format"] = new_base_name
        update_function_buttons()
        update_display()

    def parse_scientific_value(value):
        return parse_scientific_parts(value)

    def compose_scientific_value(mantissa, exponent):
        return compose_scientific_parts(mantissa, exponent)

    def split_display_value(value):
        if not value or value == "0":
            return "0", ""
        if value == "Error":
            return "Error", ""
        lower_value = value.lower()
        if "e" not in lower_value:
            # Preserve explicit input exactly as typed for full 12-digit visibility.
            return value, ""

        mantissa, exponent = lower_value.split("e", 1)
        if not mantissa.endswith("."):
            try:
                mantissa = f"{float(mantissa):.12g}"
            except ValueError:
                pass
        exponent_value = int(exponent)
        if exponent_value < 0:
            exponent_text = f"-{abs(exponent_value):03d}"
        else:
            exponent_text = f"{exponent_value:03d}"
        return mantissa, exponent_text

    # --- Display ---
    memory_indicator = ft.Text(
        value="M",
        size=12,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
        visible=False,
    )

    sign_indicator = ft.Text(
        value="",
        size=34,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
        visible=False,
    )

    mantissa_display = ft.Text(
        value="0",
        text_align=ft.TextAlign.CENTER,
        size=34,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
        no_wrap=True,
    )

    binary_display_text = ft.Text(
        value="00000000000000000000000000000000",
        text_align=ft.TextAlign.RIGHT,
        size=16,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
        no_wrap=True,
        visible=True,
    )

    exponent_sign_display = ft.Text(
        value="",
        text_align=ft.TextAlign.LEFT,
        size=16,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
        no_wrap=True,
    )

    exponent_digits_display = ft.Text(
        value="",
        text_align=ft.TextAlign.LEFT,
        size=16,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
        no_wrap=True,
    )

    exponent_row = ft.Row(
        [
            ft.Container(content=exponent_sign_display, width=6, alignment=ft.Alignment(-1, 0)),
            ft.Container(content=exponent_digits_display, alignment=ft.Alignment(-1, 0)),
        ],
        spacing=0,
    )

    # Fixed pixel geometry for the display content area. Using absolute
    # positioning (top/left/right) instead of nested expand/alignment
    # containers keeps the mantissa, exponent, and memory/sign indicators
    # in a stable, predictable position regardless of digit count.
    DISPLAY_CONTENT_WIDTH = 320
    DISPLAY_CONTENT_HEIGHT = 54
    LEFT_LANE_RESERVED = 2
    EXPONENT_ZONE_RESERVED = 34

    # NOTE: `expand=True` only works for flex children of Row/Column; Stack
    # children must be stretched explicitly via left/top/right/bottom=0
    # (Positioned.fill equivalent). Without this, these containers were
    # auto-sizing to their own content instead of filling the display,
    # so the right-alignment had no real boundary and the mantissa could
    # overflow the Stack's right edge (clipped) while still leaving a gap
    # on the left.
    standard_display = ft.Container(
        content=mantissa_display,
        alignment=ft.Alignment(1, 0),
        padding=ft.padding.Padding(LEFT_LANE_RESERVED, 0, EXPONENT_ZONE_RESERVED, 0),
        left=0,
        top=0,
        right=0,
        bottom=0,
    )

    binary_display = ft.Container(
        content=binary_display_text,
        alignment=ft.Alignment(1, 1),
        padding=ft.padding.Padding(LEFT_LANE_RESERVED, 0, 6, 0),
        left=0,
        top=0,
        right=0,
        bottom=0,
        visible=False,
    )

    display = ft.Stack(
        [
            standard_display,
            binary_display,
            ft.Container(content=memory_indicator, top=2, left=2),
            ft.Container(content=sign_indicator, top=-3, left=0),
            ft.Container(content=exponent_row, top=-2, right=1),
        ],
        width=DISPLAY_CONTENT_WIDTH,
        height=DISPLAY_CONTENT_HEIGHT,
    )

    display_card = ft.Container(
        content=display,
        alignment=ft.Alignment(0, 0),
        padding=ft.padding.Padding(8, 2, 8, 2),
        bgcolor=ft.Colors.GREY_100,
        border=ft.Border.all(6, ft.Colors.BROWN_400),
        border_radius=12,
        width=336,
        height=58,
    )

    def update_display():
        shown_value = state["display_value"] or state["current"] or "0"
        sign_text, unsigned_value = split_sign_prefix(shown_value)
        if is_base_mode_active():
            base_name = get_active_base_name()
            display_limit = get_base_display_limit(base_name)
            base_text = unsigned_value
            if shown_value != "Error" and len(unsigned_value) > display_limit:
                base_text = "Error"

            if base_name == "BIN":
                standard_display.visible = False
                binary_display.visible = True
                binary_display_text.value = base_text
            else:
                standard_display.visible = True
                binary_display.visible = False
                grouped_base_text = group_digits_for_display(base_text)
                mantissa_display.value = grouped_base_text
                exponent_sign_display.value = ""
                exponent_digits_display.value = ""
        else:
            mantissa, exponent = split_display_value(unsigned_value)
            if state["editing_exponent"] and "e" not in (state["current"] or "").lower() and state["current"]:
                exponent = "000"
            standard_display.visible = True
            binary_display.visible = False
            grouped_mantissa_text = group_digits_for_display(mantissa)
            mantissa_display.value = grouped_mantissa_text
            exponent_sign, exponent_digits = split_sign_prefix(exponent)
            exponent_sign_display.value = exponent_sign
            exponent_digits_display.value = exponent_digits
        sign_indicator.value = sign_text
        sign_indicator.visible = bool(sign_text and shown_value != "Error")
        memory_indicator.value = "M" if state["has_memory"] else ""
        memory_indicator.visible = True
        update_bracket_buttons()
        update_memory_buttons()
        update_function_buttons()
        page.update()

    def get_open_bracket_count():
        open_count = sum(1 for token in state["tokens"] if token == "(")
        close_count = sum(1 for token in state["tokens"] if token == ")")
        return max(0, open_count - close_count)

    def update_bracket_buttons():
        open_count = get_open_bracket_count()
        if open_count > 0:
            open_bracket_text.value = f"{open_count} * ("
            close_bracket_text.value = ")"
            open_bracket_button.style.bgcolor = ft.Colors.GREEN_200
            close_bracket_button.style.bgcolor = ft.Colors.GREEN_200
        else:
            open_bracket_text.value = "("
            close_bracket_text.value = ")"
            open_bracket_button.style.bgcolor = ft.Colors.GREY_200
            close_bracket_button.style.bgcolor = ft.Colors.GREY_200

    def clear_memory():
        state["memory"] = Decimal("0")
        state["has_memory"] = False

    def update_memory_buttons():
        memory_color = ft.Colors.GREEN_200 if state["has_memory"] else ft.Colors.GREY_200
        memory_in_button.style.bgcolor = memory_color
        memory_plus_button.style.bgcolor = memory_color
        memory_recall_button.style.bgcolor = memory_color

    def clear():
        state["current"] = "0"
        state["display_value"] = ""
        state["op"] = ""
        state["first"] = 0.0
        state["tokens"] = []
        state["editing_exponent"] = False
        state["replace_on_next_input"] = False
        state["last_was_equals"] = False
        update_display()

    def clear_entry():
        state["current"] = "0"
        state["display_value"] = ""
        state["editing_exponent"] = False
        state["replace_on_next_input"] = False
        update_display()

    def toggle_sign():
        current = state["current"]
        if not current or current == "Error":
            return

        if state["editing_exponent"]:
            mantissa, exponent = parse_scientific_value(current)
            digits = exponent.lstrip("-") or "0"
            new_exponent = digits if exponent.startswith("-") else f"-{digits}"
            state["current"] = compose_scientific_value(mantissa, new_exponent)
            state["display_value"] = ""
            update_display()
            return

        if current.startswith("-"):
            state["current"] = current[1:]
        else:
            if current != "0":
                state["current"] = f"-{current}"
        state["display_value"] = ""
        update_display()

    def start_exponent_edit():
        updated_current, editing_exponent = toggle_exponent_mode(
            state["current"], state["editing_exponent"]
        )
        if updated_current == state["current"] and editing_exponent == state["editing_exponent"]:
            return
        state["current"] = updated_current
        state["display_value"] = ""
        state["editing_exponent"] = editing_exponent
        state["replace_on_next_input"] = False
        if editing_exponent:
            state["last_was_equals"] = False
        update_display()

    def append_exponent_digit(digit):
        current = state["current"]
        if not current or current == "Error":
            return

        state["current"] = append_exponent_digit_to_value(current, digit)
        state["display_value"] = ""
        update_display()

    def append_mantissa_digit(char):
        updated_current, handled = append_mantissa_digit_to_value(state["current"], char)
        if not handled:
            return False
        state["current"] = updated_current
        state["display_value"] = ""
        update_display()
        return handled

    def recall_memory():
        if not state["has_memory"]:
            return
        set_current_from_numeric(state["memory"])
        state["display_value"] = ""
        state["editing_exponent"] = False
        state["replace_on_next_input"] = False
        state["last_was_equals"] = False
        update_display()

    def can_push_current():
        return bool(state["current"] and state["current"] not in {"Error", "-"})

    def push_current_token():
        if can_push_current():
            state["tokens"].append(current_numeric_value())
            state["current"] = ""

    def apply_top_operator(values, operators):
        if len(values) < 2 or not operators:
            raise ValueError("Invalid expression")
        op = operators.pop()
        right = values.pop()
        left = values.pop()
        values.append(calc_binary_value(left, right, op, base_mode=is_base_mode_active()))

    def evaluate_expression(tokens):
        return evaluate_expression_tokens(tokens, base_mode=is_base_mode_active())

    def preview_for_operator(incoming_op):
        tokens = list(state["tokens"])
        if can_push_current():
            tokens.append(current_numeric_value())
        while tokens and tokens[-1] in BINARY_OPS:
            tokens.pop()
        if not tokens:
            return state["current"] or "0"

        values = []
        operators = []

        for token in tokens:
            if token == "(":
                operators.append(token)
            elif token == ")":
                while operators and operators[-1] != "(":
                    apply_top_operator(values, operators)
                if operators and operators[-1] == "(":
                    operators.pop()
            elif token in BINARY_OPS:
                while operators and operators[-1] in BINARY_OPS:
                    top = operators[-1]
                    if OP_PRECEDENCE[top] > OP_PRECEDENCE[token] or (
                        OP_PRECEDENCE[top] == OP_PRECEDENCE[token] and token != "^"
                    ):
                        apply_top_operator(values, operators)
                    else:
                        break
                operators.append(token)
            else:
                if isinstance(token, (int, float)):
                    values.append(token)
                elif isinstance(token, Decimal):
                    values.append(token)
                else:
                    values.append(Decimal(str(token)))

        while operators and operators[-1] in BINARY_OPS:
            top = operators[-1]
            if OP_PRECEDENCE[top] > OP_PRECEDENCE[incoming_op] or (
                OP_PRECEDENCE[top] == OP_PRECEDENCE[incoming_op] and incoming_op != "^"
            ):
                apply_top_operator(values, operators)
            else:
                break

        if not values:
            return state["current"] or "0"
        return format_result_value(values[-1])

    def preview_for_closed_bracket():
        tokens = list(state["tokens"])
        if not tokens or tokens[-1] != ")":
            return state["display_value"] or state["current"] or "0"

        depth = 0
        inner_tokens = []
        for token in reversed(tokens):
            if token == ")":
                depth += 1
                if depth == 1:
                    continue
            elif token == "(":
                depth -= 1
                if depth == 0:
                    break
            if depth >= 1:
                inner_tokens.append(token)

        if not inner_tokens:
            return state["display_value"] or state["current"] or "0"

        inner_tokens.reverse()
        return format_result_value(evaluate_expression(inner_tokens))

    def handle_base_unary(action):
        adopt_display_value_as_current()
        if not can_push_current():
            return
        try:
            value = current_numeric_value()
            if action == "NEG":
                result = normalize_base_word(-value)
            elif action == "NOT":
                result = normalize_base_word(~value)
            else:
                return
            set_current_from_numeric(result)
            state["display_value"] = ""
            state["replace_on_next_input"] = False
            state["last_was_equals"] = False
            update_display()
        except ValueError:
            state["current"] = "Error"
            state["display_value"] = ""
            update_display()

    def handle_function_button(button_id):
        index = int(button_id.split("_", 1)[1])
        row = index // 4
        column = index % 4
        label = (BASE_FUNCTION_LAYOUT if is_base_mode_active() else NORMAL_FUNCTION_LAYOUT)[row][column]

        if is_base_mode_active():
            if label in BASE_SYSTEMS:
                change_base_format(label)
            elif label in {"A", "B", "C", "D", "E", "F"}:
                handle_base_digit_input(label)
            elif label in {"NEG", "NOT"}:
                handle_base_unary(label)
            elif label in BASE_BINARY_OPS:
                handle_operator(label)
            return

        if label in TRIG_FUNCS:
            if state["current"]:
                try:
                    result = calc_unary(float(state["current"]), label)
                    state["current"] = format_number(result)
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                except (ValueError, ZeroDivisionError, OverflowError):
                    state["current"] = "Error"
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                update_display()

    def handle_operator(op):
        if state["current"] == "Error":
            return

        if state["editing_exponent"]:
            state["editing_exponent"] = False

        if can_push_current():
            preview_value = preview_for_operator(op)
            push_current_token()
        elif state["tokens"] and state["tokens"][-1] in BINARY_OPS:
            state["tokens"], _ = replace_last_operator(state["tokens"], op)
            state["display_value"] = preview_for_operator(op)
            state["replace_on_next_input"] = True
            state["last_was_equals"] = False
            update_display()
            return
        else:
            if state["tokens"] and state["tokens"][-1] != "(":
                preview_value = preview_for_operator(op)
            else:
                preview_value = state["current"] or state["display_value"] or "0"

        if state["tokens"] and state["tokens"][-1] != "(":
            state["tokens"].append(op)
            state["display_value"] = preview_value
            state["replace_on_next_input"] = True
            state["last_was_equals"] = False
            update_display()

    def handle_open_bracket():
        if state["current"] == "Error":
            return
        if can_push_current():
            state["tokens"].append(current_numeric_value())
            state["tokens"].append("*")
            state["current"] = ""
        elif state["tokens"] and state["tokens"][-1] == ")":
            state["tokens"].append("*")
        state["tokens"].append("(")
        state["display_value"] = ""
        state["replace_on_next_input"] = False
        state["last_was_equals"] = False
        update_display()

    def handle_close_bracket():
        if state["current"] == "Error":
            return
        if can_push_current():
            push_current_token()
        if not state["tokens"]:
            return
        open_count = sum(1 for token in state["tokens"] if token == "(")
        close_count = sum(1 for token in state["tokens"] if token == ")")
        if open_count <= close_count:
            return
        if state["tokens"][-1] in BINARY_OPS or state["tokens"][-1] == "(":
            return
        state["tokens"].append(")")
        state["display_value"] = preview_for_closed_bracket()
        state["replace_on_next_input"] = True
        state["last_was_equals"] = False
        update_display()

    def evaluate_pending_expression():
        tokens = list(state["tokens"])
        if should_keep_current_on_equals(tokens, state["current"]):
            state["display_value"] = ""
            state["tokens"] = []
            state["op"] = ""
            state["editing_exponent"] = False
            state["replace_on_next_input"] = True
            state["last_was_equals"] = True
            return
        if can_push_current():
            tokens.append(current_numeric_value())
        if not tokens:
            return
        if tokens[-1] in BINARY_OPS or tokens[-1] == "(":
            raise ValueError("Incomplete expression")
        open_count = sum(1 for token in tokens if token == "(")
        close_count = sum(1 for token in tokens if token == ")")
        if open_count > close_count:
            tokens.extend(")" for _ in range(open_count - close_count))
        result = evaluate_expression(tokens)
        state["current"] = format_result_value(result)
        state["display_value"] = ""
        state["tokens"] = []
        state["op"] = ""
        state["editing_exponent"] = False
        state["replace_on_next_input"] = True
        state["last_was_equals"] = True

    # --- Math helpers ---
    def calc_binary(a, b, op):
        return calc_binary_value(a, b, op, base_mode=is_base_mode_active())

    def calc_unary(x, func):
        trig_direct = {"sin", "cos", "tan", "cot"}
        arc_trig = {"asin", "acos", "atan", "acot"}

        if func in trig_direct and state["mode"] == "Deg":
            x = math.radians(x)

        if func == "sin":
            result = _safe_sin(x)
        elif func == "cos":
            result = _safe_cos(x)
        elif func == "tan":
            result = _safe_tan(x)
        elif func == "cot":
            t = _safe_tan(x)
            if t == 0:
                raise ValueError("Undefined")
            result = 1 / t
        elif func == "asin":
            if not (-1 <= x <= 1):
                raise ValueError("Domain error")
            result = math.asin(x)
        elif func == "acos":
            if not (-1 <= x <= 1):
                raise ValueError("Domain error")
            result = math.acos(x)
        elif func == "atan":
            result = math.atan(x)
        elif func == "acot":
            result = math.pi / 2 - math.atan(x)
        elif func == "sinh":
            result = math.sinh(x)
        elif func == "cosh":
            result = math.cosh(x)
        elif func == "tanh":
            result = math.tanh(x)
        elif func == "coth":
            t = math.tanh(x)
            if t == 0:
                raise ValueError("Undefined")
            result = 1 / t
        elif func == "asinh":
            result = math.asinh(x)
        elif func == "acosh":
            if x < 1:
                raise ValueError("Domain error")
            result = math.acosh(x)
        elif func == "atanh":
            if not (-1 < x < 1):
                raise ValueError("Domain error")
            result = math.atanh(x)
        elif func == "acoth":
            if abs(x) <= 1:
                raise ValueError("Domain error")
            result = math.atanh(1 / x)
        else:
            raise ValueError(f"Unknown function: {func}")

        if func in arc_trig and state["mode"] == "Deg":
            result = math.degrees(result)

        return result

    # --- Button handler ---
    def on_click(e):
        char = e.control.data
        if char is None:
            return

        trigger_key_feedback()

        if isinstance(char, str) and char.startswith("FUNC_"):
            handle_function_button(char)
            return

        if is_base_mode_active() and (char.isdigit() or char in "ABCDEF" or char == "."):
            handle_base_digit_input(char)
            return

        if char.isdigit() or char == ".":
            if state["editing_exponent"]:
                if char.isdigit():
                    append_exponent_digit(char)
                return

            if state["replace_on_next_input"]:
                state["current"] = ""
                state["display_value"] = ""
                state["replace_on_next_input"] = False

            if state["last_was_equals"] and char.isdigit():
                clear()
            state["last_was_equals"] = False

            if state["current"] == "Error":
                state["current"] = ""

            if char.isdigit() and state["current"] == "0":
                state["current"] = ""

            if char == "." and "." in state["current"]:
                return
            if char == "." and state["current"] == "":
                state["current"] = "0"
            if append_mantissa_digit(char):
                return
            if char.isdigit() and digit_count(state["current"]) >= MAX_DIGITS:
                return
            state["current"] += char
            state["display_value"] = ""
            update_display()

        elif char in CONSTANTS:
            if state["replace_on_next_input"]:
                state["current"] = ""
                state["display_value"] = ""
                state["replace_on_next_input"] = False
            if state["current"] == "Error":
                state["current"] = ""
            if is_base_mode_active():
                state["current"] = format_base_integer(int(CONSTANTS[char]))
            else:
                state["current"] = format_number(CONSTANTS[char])
            state["display_value"] = ""
            state["editing_exponent"] = False
            state["last_was_equals"] = False
            update_display()

        elif char == "+/-":
            if is_base_mode_active():
                handle_base_unary("NEG")
            else:
                toggle_sign()

        elif char == "EXP":
            if not is_base_mode_active():
                start_exponent_edit()

        elif char == "M in":
            if state["current"] and state["current"] != "Error":
                value = current_numeric_value()
                if value == 0:
                    clear_memory()
                else:
                    state["memory"] = value
                    state["has_memory"] = True
                update_display()

        elif char == "M+":
            if state["current"] and state["current"] != "Error":
                state["memory"] = to_decimal(state["memory"]) + current_numeric_value()
                state["has_memory"] = True
                update_display()

        elif char == "MR":
            recall_memory()

        elif char == "(":
            handle_open_bracket()

        elif char == ")":
            handle_close_bracket()

        elif char in BINARY_OPS:
            handle_operator(char)

        elif char in EXTRA_UNARY_FUNCS:
            if state["current"]:
                try:
                    numeric_value = current_numeric_value()
                    result = calc_extra_unary_value(numeric_value, char)
                    if is_base_mode_active():
                        state["current"] = format_result_value(normalize_base_word(int(result)))
                    else:
                        state["current"] = format_result_value(result)
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                except (ValueError, ZeroDivisionError, OverflowError, InvalidOperation, DivisionByZero):
                    state["current"] = "Error"
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                update_display()

        elif char == "=":
            try:
                evaluate_pending_expression()
            except (ValueError, ZeroDivisionError, OverflowError):
                state["current"] = "Error"
                state["display_value"] = ""
                state["tokens"] = []
                state["op"] = ""
                state["editing_exponent"] = False
                state["replace_on_next_input"] = False
                state["last_was_equals"] = False
            update_display()

        elif char == "AC":
            clear()
        elif char == "CE":
            clear_entry()

    class _VirtualControl:
        def __init__(self, data):
            self.data = data

    class _VirtualEvent:
        def __init__(self, data):
            self.control = _VirtualControl(data)

    def dispatch_button_input(data):
        on_click(_VirtualEvent(data))

    async def copy_display_to_clipboard():
        try:
            await clipboard_service.set(state["display_value"] or state["current"] or "0")
        except Exception:
            return

    async def paste_clipboard_to_input():
        try:
            clipboard_value = await clipboard_service.get()
        except Exception:
            return

        cleaned = str(clipboard_value or "").strip().replace("\u2009", "").replace(" ", "")
        if not cleaned:
            return

        try:
            if is_base_mode_active():
                parsed = parse_base_integer(cleaned, get_active_base_name())
                state["current"] = format_base_integer(parsed)
            else:
                numeric_value = to_decimal(cleaned)
                if not numeric_value.is_finite():
                    return
                state["current"] = format_number(numeric_value)
        except (InvalidOperation, ValueError, OverflowError):
            return

        state["display_value"] = ""
        state["editing_exponent"] = False
        state["replace_on_next_input"] = False
        state["last_was_equals"] = False
        update_display()

    def on_keyboard(e: ft.KeyboardEvent):
        # NOTE: this Flet version's KeyboardEvent only exposes
        # key/shift/ctrl/alt/meta - there is no `code` (physical key) field.
        key = (e.key or "")
        key_lower = key.lower()
        has_shift = bool(getattr(e, "shift", False))
        has_ctrl = bool(getattr(e, "ctrl", False) or getattr(e, "meta", False))

        if has_ctrl and key_lower == "c":
            page.run_task(copy_display_to_clipboard)
            return

        if has_ctrl and key_lower == "v":
            page.run_task(paste_clipboard_to_input)
            return

        # Normalize locale-specific key labels that Flet may emit.
        if key in {"Dead", "dead"}:
            key = "^"
            key_lower = "^"

        # On some layouts the +/* key is reported as "=".
        # Interpret it as + without Shift and * with Shift.
        if key == "=":
            key = "*" if has_shift else "+"
            key_lower = key.lower()

        # Flet may report unshifted key labels for main-row symbol keys.
        # Handle both US and DE layouts explicitly.
        if has_shift:
            shifted_de_map = {
                "7": "/",
                "8": "(",
                "9": ")",
            }
            shifted_us_map = {
                "6": "^",
                "8": "*",
                "9": "(",
                "0": ")",
            }

            # Prefer DE mappings first (requested behavior), then US fallback.
            if key in shifted_de_map:
                key = shifted_de_map[key]
                key_lower = key.lower()
            elif key in shifted_us_map:
                key = shifted_us_map[key]
                key_lower = key.lower()

        key_map = {
            "Enter": "=",
            "Return": "=",
            "Numpad Enter": "=",
            "Escape": "AC",
            "Backspace": "CE",
            "Delete": "CE",
            "Add": "+",
            "Subtract": "-",
            "Multiply": "*",
            "Divide": "/",
            "^": "^",
            "(": "(",
            ")": ")",
            "=": "=",
            "!": "x!",
            "l": "log",
            "L": "log",
            "n": "ln",
            "N": "ln",
            "e": "EXP",
            "E": "EXP",
        }

        mapped = key_map.get(key)

        if mapped is None:
            named_operator_map = {
                "plus": "+",
                "minus": "-",
                "asterisk": "*",
                "slash": "/",
                "add": "+",
                "subtract": "-",
                "multiply": "*",
                "divide": "/",
            }
            mapped = named_operator_map.get(key_lower)

        if mapped is None and key_lower.startswith("numpad "):
            numpad_suffix = key_lower[7:]
            numpad_map = {
                "enter": "=",
                "decimal": ".",
                "add": "+",
                "subtract": "-",
                "multiply": "*",
                "divide": "/",
                "equal": "=",
            }
            if numpad_suffix.isdigit() and len(numpad_suffix) == 1:
                mapped = numpad_suffix
            else:
                mapped = numpad_map.get(numpad_suffix)

        if mapped is None and len(key) == 1 and key in "0123456789.+-*/":
            mapped = key

        if mapped is not None:
            dispatch_button_input(mapped)

    # --- Mode toggles ---
    mode_rad_label = ft.Text("Rad", size=11, weight=ft.FontWeight.BOLD, no_wrap=True)
    mode_deg_label = ft.Text("Deg", size=11, weight=ft.FontWeight.BOLD, no_wrap=True)
    mode_thumb = ft.Container(
        width=22,
        height=20,
        border_radius=12,
        bgcolor=ft.Colors.GREY_300,
        animate=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
    )
    mode_track = ft.Container(
        content=ft.Row(
            [mode_thumb],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=52,
        height=24,
        border_radius=12,
        bgcolor=ft.Colors.GREY_700,
        padding=ft.padding.Padding(3, 2, 3, 2),
    )

    base_normal_label = ft.Text("Std", size=11, weight=ft.FontWeight.BOLD, no_wrap=True)
    base_bases_label = ft.Text("Base", size=11, weight=ft.FontWeight.BOLD, no_wrap=True)
    base_thumb = ft.Container(
        width=22,
        height=20,
        border_radius=12,
        bgcolor=ft.Colors.GREY_300,
        animate=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
    )
    base_track = ft.Container(
        content=ft.Row(
            [base_thumb],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=52,
        height=24,
        border_radius=12,
        bgcolor=ft.Colors.GREY_700,
        padding=ft.padding.Padding(3, 2, 3, 2),
    )
    mode_control = None

    def refresh_mode_control():
        is_deg = state["mode"] == "Deg"
        is_base_mode = state["base_mode"] == "Base"

        if is_base_mode:
            mode_rad_label.color = ft.Colors.GREY_500
            mode_deg_label.color = ft.Colors.GREY_500
        else:
            mode_rad_label.color = ft.Colors.GREY_500 if is_deg else ft.Colors.BLACK
            mode_deg_label.color = ft.Colors.BLACK if is_deg else ft.Colors.GREY_500
        mode_track.content.alignment = (
            ft.MainAxisAlignment.END if is_deg else ft.MainAxisAlignment.START
        )
        mode_track.bgcolor = ft.Colors.GREY_500 if is_base_mode else ft.Colors.GREY_700
        mode_thumb.bgcolor = ft.Colors.GREY_400 if is_base_mode else ft.Colors.GREY_300

        if mode_control is not None:
            mode_control.on_click = None if is_base_mode else toggle_mode
            mode_control.opacity = 0.55 if is_base_mode else 1.0
            mode_control.bgcolor = (
                ft.Colors.with_opacity(0.1, ft.Colors.GREY_400)
                if is_base_mode
                else ft.Colors.with_opacity(0.0, ft.Colors.GREY_200)
            )

        base_normal_label.color = (
            ft.Colors.with_opacity(0.65, ft.Colors.ORANGE_700)
            if is_base_mode
            else ft.Colors.ORANGE_700
        )
        base_bases_label.color = (
            ft.Colors.GREEN_700
            if is_base_mode
            else ft.Colors.with_opacity(0.65, ft.Colors.GREEN_700)
        )
        base_track.content.alignment = (
            ft.MainAxisAlignment.END if is_base_mode else ft.MainAxisAlignment.START
        )

    def toggle_mode(_):
        if state["base_mode"] == "Base":
            return
        trigger_key_feedback()
        state["mode"] = "Deg" if state["mode"] == "Rad" else "Rad"
        refresh_mode_control()
        page.update()

    def toggle_base_mode(_):
        trigger_key_feedback()
        entering_base_mode = state["base_mode"] == "Normal"
        shown_value = state["display_value"] or state["current"] or "0"
        state["base_mode"] = "Base" if entering_base_mode else "Normal"
        state["tokens"] = []
        state["display_value"] = ""
        state["replace_on_next_input"] = False
        state["editing_exponent"] = False
        state["last_was_equals"] = False
        if entering_base_mode:
            state["base_format"] = "DEC"
            state["current"] = format_base_integer(
                convert_standard_text_to_base_word(shown_value),
                "DEC",
            )
        else:
            try:
                numeric_text = convert_base_text_to_signed_decimal_text(shown_value, state["base_format"])
            except ValueError:
                numeric_text = "0"
            state["current"] = numeric_text
        refresh_mode_control()
        update_display()

    def update_function_buttons():
        layout = BASE_FUNCTION_LAYOUT if is_base_mode_active() else NORMAL_FUNCTION_LAYOUT
        for index, button in enumerate(function_buttons):
            row = index // 4
            column = index % 4
            label = layout[row][column]
            function_button_texts[index].value = label
            function_button_texts[index].weight = (
                ft.FontWeight.BOLD if is_base_mode_active() and label in BASE_SYSTEMS else ft.FontWeight.NORMAL
            )
            button.style.bgcolor = ft.Colors.GREEN_200 if is_base_mode_active() else ft.Colors.ORANGE_200
            if is_base_mode_active() and label == state["base_format"]:
                button.style.bgcolor = ft.Colors.GREEN_400
            button.data = f"FUNC_{index}"

    refresh_mode_control()

    mode_control = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=mode_rad_label,
                    expand=True,
                    alignment=ft.Alignment(-1, 0),
                    padding=ft.padding.Padding(0, 0, 0, 2),
                ),
                ft.Container(
                    content=mode_track,
                    width=60,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(
                    content=mode_deg_label,
                    expand=True,
                    alignment=ft.Alignment(1, 0),
                    padding=ft.padding.Padding(0, 0, 0, 2),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        on_click=toggle_mode,
        alignment=ft.Alignment(0, 0),
        expand=True,
        height=34,
        bgcolor=ft.Colors.with_opacity(0.0, ft.Colors.GREY_200),
        border_radius=6,
        padding=ft.padding.Padding(12, 2, 12, 2),
    )

    base_mode_control = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=base_normal_label,
                    expand=True,
                    alignment=ft.Alignment(-1, 0),
                    padding=ft.padding.Padding(0, 0, 0, 2),
                ),
                ft.Container(
                    content=base_track,
                    width=60,
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Container(
                    content=base_bases_label,
                    expand=True,
                    alignment=ft.Alignment(1, 0),
                    padding=ft.padding.Padding(0, 0, 0, 2),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        on_click=toggle_base_mode,
        alignment=ft.Alignment(0, 0),
        expand=True,
        height=34,
        bgcolor=ft.Colors.with_opacity(0.0, ft.Colors.GREY_200),
        border_radius=6,
        padding=ft.padding.Padding(12, 2, 12, 2),
    )

    orientation_toggle_icon = ft.Icon(
        ft.Icons.SCREEN_ROTATION,
        size=18,
        color=ft.Colors.BLACK,
    )

    orientation_toggle_control = ft.Container(
        width=42,
        height=34,
        alignment=ft.Alignment(0, 0),
        border_radius=6,
        bgcolor=ft.Colors.GREY_300,
        content=orientation_toggle_icon,
        visible=is_windows,
    )

    def update_orientation_toggle_control():
        if not is_windows:
            return
        is_landscape = bool(page.width and page.height and page.width > page.height)
        orientation_toggle_icon.name = ft.Icons.SCREEN_ROTATION
        orientation_toggle_control.bgcolor = ft.Colors.ORANGE_200 if is_landscape else ft.Colors.BLUE_200
        orientation_toggle_control.tooltip = (
            "Switch to portrait" if is_landscape else "Switch to landscape"
        )

    def toggle_window_orientation(_):
        if not is_windows:
            return
        is_landscape = bool(page.width and page.height and page.width > page.height)
        if is_landscape:
            page.window.width = windows_portrait_width
            page.window.height = windows_portrait_height
        else:
            page.window.width = windows_landscape_width
            page.window.height = windows_landscape_height
        apply_responsive_layout()

    orientation_toggle_control.on_click = toggle_window_orientation

    refresh_mode_control()

    # --- Button factory ---
    def btn(label, data=None, bgcolor=None, color=None, text_size=17, text_weight=ft.FontWeight.NORMAL, text_ref=None):
        base_bg = bgcolor or ft.Colors.GREY_200
        return ft.Button(
            content=ft.Container(
                content=text_ref or ft.Text(
                    label,
                    size=text_size,
                    weight=text_weight,
                    text_align=ft.TextAlign.CENTER,
                    no_wrap=True,
                ),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.Padding(3, 2, 3, 2),
            ),
            data=data if data is not None else label,
            on_click=on_click,
            expand=True,
            height=45,
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: base_bg,
                    ft.ControlState.PRESSED: get_pressed_button_bg(base_bg),
                },
                color=color or ft.Colors.BLACK,
                overlay_color={
                    ft.ControlState.PRESSED: ft.Colors.with_opacity(0.12, ft.Colors.BLACK),
                    ft.ControlState.HOVERED: ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                },
                elevation={
                    ft.ControlState.DEFAULT: 1,
                    ft.ControlState.PRESSED: 0.25,
                },
                animation_duration=90,
                enable_feedback=True,
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=0,
            ),
        )

    OP_BG = ft.Colors.BLUE_200
    EQ_BG = ft.Colors.BLUE_700
    CLR_BG = ft.Colors.RED_200
    TOP_BG = ft.Colors.BROWN_100
    SWITCH_BG = ft.Colors.GREY_200

    open_bracket_text = ft.Text(
        "(",
        size=19,
        weight=ft.FontWeight.NORMAL,
        text_align=ft.TextAlign.CENTER,
        no_wrap=True,
    )
    close_bracket_text = ft.Text(
        ")",
        size=19,
        weight=ft.FontWeight.NORMAL,
        text_align=ft.TextAlign.CENTER,
        no_wrap=True,
    )
    open_bracket_button = btn("(", text_size=19, text_ref=open_bracket_text)
    close_bracket_button = btn(")", text_size=19, text_ref=close_bracket_text)
    memory_in_button = btn("M in")
    memory_plus_button = btn("M+")
    memory_recall_button = btn("MR")
    clear_button = btn("AC", bgcolor=CLR_BG, text_weight=ft.FontWeight.BOLD)
    clear_entry_button = btn("CE", bgcolor=CLR_BG, text_weight=ft.FontWeight.BOLD)
    digit_0_button = btn("0", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_1_button = btn("1", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_2_button = btn("2", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_3_button = btn("3", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_4_button = btn("4", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_5_button = btn("5", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_6_button = btn("6", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_7_button = btn("7", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_8_button = btn("8", text_size=19, text_weight=ft.FontWeight.BOLD)
    digit_9_button = btn("9", text_size=19, text_weight=ft.FontWeight.BOLD)
    decimal_button = btn(".", text_size=19, text_weight=ft.FontWeight.BOLD)
    sign_button = btn("+/-", text_size=19, text_weight=ft.FontWeight.BOLD)
    exp_button = btn("EXP", text_size=19, text_weight=ft.FontWeight.BOLD)
    equals_button = btn("=", bgcolor=EQ_BG, text_size=19, text_weight=ft.FontWeight.BOLD)
    multiply_button = btn("*", bgcolor=OP_BG, text_size=19, text_weight=ft.FontWeight.BOLD)
    divide_button = btn("/", bgcolor=OP_BG, text_size=19, text_weight=ft.FontWeight.BOLD)
    plus_button = btn("+", bgcolor=OP_BG, text_size=19, text_weight=ft.FontWeight.BOLD)
    minus_button = btn("−", data="-", bgcolor=OP_BG, text_size=19, text_weight=ft.FontWeight.BOLD)
    reciprocal_button = btn("1/x")
    sqrt_button = btn("√x̅", data="sqrt")
    square_button = btn("x²", data="x^2")
    power_button = btn("xʸ", data="^")
    const_pi_button = btn("π", data="CONST_PI")
    const_c_button = btn("c", data="CONST_C")
    const_h_button = btn("ℏ", data="CONST_H")
    const_g_button = btn("G", data="CONST_G")
    log_button = btn("log", data="log")
    ln_button = btn("ln", data="ln")
    exp_e_button = btn("eˣ", data="e^x")
    factorial_button = btn("x!", data="x!")
    function_button_texts = [
        ft.Text("", size=17, weight=ft.FontWeight.NORMAL, text_align=ft.TextAlign.CENTER, no_wrap=True)
        for _ in range(16)
    ]
    function_buttons = [
        btn("", data=f"FUNC_{index}", text_ref=function_button_texts[index])
        for index in range(16)
    ]

    memory_row = ft.Row(
        [clear_button, clear_entry_button, memory_in_button, memory_plus_button, memory_recall_button],
        spacing=8,
    )
    keypad_row_7_9 = ft.Row(
        [digit_7_button, digit_8_button, digit_9_button, open_bracket_button, close_bracket_button],
        spacing=8,
    )
    keypad_row_4_6 = ft.Row(
        [digit_4_button, digit_5_button, digit_6_button, multiply_button, divide_button],
        spacing=8,
    )
    keypad_row_1_3 = ft.Row(
        [digit_1_button, digit_2_button, digit_3_button, plus_button, minus_button],
        spacing=8,
    )
    keypad_row_0_equals = ft.Row(
        [digit_0_button, decimal_button, sign_button, exp_button, equals_button],
        spacing=8,
    )
    scientific_top_row = ft.Row([reciprocal_button, sqrt_button, square_button, power_button], spacing=8)
    scientific_log_row = ft.Row([log_button, ln_button, exp_e_button, factorial_button], spacing=8)
    scientific_row_1 = ft.Row(function_buttons[0:4], spacing=8)
    scientific_row_2 = ft.Row(function_buttons[4:8], spacing=8)
    scientific_row_3 = ft.Row(function_buttons[8:12], spacing=8)
    scientific_row_4 = ft.Row(function_buttons[12:16], spacing=8)
    constants_row = ft.Row([const_pi_button, const_c_button, const_h_button, const_g_button], spacing=8)
    landscape_scientific_buttons = [
        reciprocal_button,
        sqrt_button,
        square_button,
        power_button,
        log_button,
        ln_button,
        exp_e_button,
        factorial_button,
        *function_buttons,
        const_pi_button,
        const_c_button,
        const_h_button,
        const_g_button,
    ]
    landscape_left_buttons = [
        clear_button,
        clear_entry_button,
        memory_in_button,
        memory_plus_button,
        memory_recall_button,
        digit_0_button,
        digit_1_button,
        digit_2_button,
        digit_3_button,
        digit_4_button,
        digit_5_button,
        digit_6_button,
        digit_7_button,
        digit_8_button,
        digit_9_button,
        decimal_button,
        sign_button,
        exp_button,
        equals_button,
        multiply_button,
        divide_button,
        plus_button,
        minus_button,
        open_bracket_button,
        close_bracket_button,
    ]

    top_spacer = ft.Container(height=0, bgcolor=ft.Colors.BLACK)
    top_display_band = ft.Container(
        bgcolor=TOP_BG,
        padding=ft.padding.Padding(0, 6, 0, 8),
        content=ft.Row([display_card], alignment=ft.MainAxisAlignment.CENTER),
    )

    top_section = ft.Container(
        padding=ft.padding.Padding(0, 0, 0, 2),
        content=ft.Column(
            spacing=0,
            controls=[
                top_spacer,
                top_display_band,
            ],
        ),
    )

    switch_row_controls = [mode_control, base_mode_control]
    if is_windows:
        switch_row_controls.append(orientation_toggle_control)

    switch_section = ft.Container(
        bgcolor=SWITCH_BG,
        padding=ft.padding.Padding(6, 4, 6, 4),
        content=ft.Row(switch_row_controls, spacing=8),
    )

    portrait_keypad_section = ft.Container(
        bgcolor=ft.Colors.BLACK,
        padding=8,
        expand=True,
        content=ft.Column(
            spacing=8,
            controls=[
                memory_row,
                keypad_row_7_9,
                keypad_row_4_6,
                keypad_row_1_3,
                keypad_row_0_equals,
                scientific_top_row,
                scientific_log_row,
                scientific_row_1,
                scientific_row_2,
                scientific_row_3,
                scientific_row_4,
                constants_row,
            ],
        ),
    )

    landscape_left_section = ft.Container(
        bgcolor=ft.Colors.BLACK,
        padding=8,
        border=ft.Border.only(right=ft.BorderSide(1, ft.Colors.GREY_700)),
        expand=True,
        content=ft.Column(
            spacing=8,
            controls=[
                memory_row,
                keypad_row_7_9,
                keypad_row_4_6,
                keypad_row_1_3,
                keypad_row_0_equals,
            ],
        ),
    )

    landscape_right_section = ft.Container(
        bgcolor=ft.Colors.BLACK,
        padding=8,
        expand=True,
        content=ft.Column(
            spacing=8,
            controls=[
                scientific_top_row,
                scientific_log_row,
                scientific_row_1,
                scientific_row_2,
                scientific_row_3,
                scientific_row_4,
                constants_row,
            ],
        ),
    )

    layout_host = ft.Container(expand=True)
    safe_area_padding = (
        ft.padding.Padding(10, 8, 10, 8)
        if is_windows
        else ft.padding.Padding(10, 0, 10, 10)
    )
    safe_area = ft.SafeArea(
        minimum_padding=safe_area_padding,
        content=ft.Container(
            content=layout_host,
            border=ft.Border.all(1, ft.Colors.GREY_700),
        ),
    )

    landscape_left_expand = 5
    landscape_right_expand = 4

    def build_portrait_layout():
        return ft.Column(
            expand=True,
            spacing=2,
            controls=[
                top_section,
                switch_section,
                portrait_keypad_section,
            ],
        )

    def build_landscape_layout():
        return ft.Row(
            expand=True,
            spacing=8,
            controls=[
                ft.Container(
                    expand=landscape_left_expand,
                    content=ft.Column(
                        expand=True,
                        spacing=2,
                        controls=[
                            top_section,
                            switch_section,
                            landscape_left_section,
                        ],
                    ),
                ),
                ft.Container(
                    expand=landscape_right_expand,
                    content=landscape_right_section,
                ),
            ],
        )

    def apply_responsive_layout():
        nonlocal landscape_left_expand, landscape_right_expand
        is_landscape = bool(page.width and page.height and page.width > page.height)
        top_spacer.height = 0
        update_orientation_toggle_control()
        top_section.padding = ft.padding.Padding(0, 0, 0, 1) if is_landscape else ft.padding.Padding(0, 0, 0, 2)
        top_display_band.padding = ft.padding.Padding(0, 1, 0, 2) if is_landscape else ft.padding.Padding(0, 6, 0, 8)
        switch_section.padding = ft.padding.Padding(4, 1, 4, 1) if is_landscape else ft.padding.Padding(6, 4, 6, 4)
        portrait_keypad_section.padding = 8 if is_landscape else 6
        portrait_keypad_section.content.spacing = 8 if is_landscape else 6
        landscape_left_section.padding = 4 if is_landscape else 8
        landscape_right_section.padding = 4 if is_landscape else 8
        landscape_left_section.content.spacing = 5 if is_landscape else 8
        landscape_right_section.content.spacing = 4 if is_landscape else 8
        if is_landscape and is_windows:
            landscape_left_expand = 1
            landscape_right_expand = 1
        else:
            landscape_left_expand = 5
            landscape_right_expand = 4
        left_button_height = 39 if is_landscape else 45
        scientific_button_height = 42 if is_landscape else 40
        for button in landscape_left_buttons:
            button.height = left_button_height
        for button in landscape_scientific_buttons:
            button.height = scientific_button_height
        layout_host.content = build_landscape_layout() if is_landscape else build_portrait_layout()
        page.update()

    # --- Layout ---
    page.add(safe_area)
    page.on_resize = lambda _: apply_responsive_layout()
    page.on_keyboard_event = on_keyboard

    update_bracket_buttons()
    update_memory_buttons()
    update_function_buttons()
    apply_responsive_layout()
if __name__ == "__main__":
    import traceback

    def _safe_main(page: ft.Page):
        try:
            main(page)
        except Exception:
            tb = traceback.format_exc()
            try:
                import sys
                print(tb, file=sys.stderr)
            except Exception:
                pass
            page.controls.clear()
            page.add(
                ft.Container(
                    content=ft.Column([
                        ft.Text("Startup error", size=20, weight=ft.FontWeight.BOLD, color=ft.Colors.RED),
                        ft.Text(tb, selectable=True),
                    ]),
                    padding=12,
                )
            )
            page.update()

    ft.run(_safe_main)
