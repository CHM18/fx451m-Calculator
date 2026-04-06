"""
fx451m Calculator
A calculator with basic arithmetic and trigonometric/hyperbolic functions using Flet.
Works on desktop (Windows/Mac/Linux) and can be built for Android with: flet build apk
"""

import math
import flet as ft


def main(page: ft.Page):
    page.title = "fx451m Calculator"
    page.window.width = 420
    page.window.height = 772
    page.padding = 0
    page.bgcolor = ft.Colors.BLACK

    # --- Calculator state ---
    state = {
        "current": "",
        "display_value": "",
        "op": "",
        "first": 0.0,
        "tokens": [],
        "memory": 0.0,
        "has_memory": False,
        "mode": "Rad",
        "base_mode": "Normal",
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
    EXTRA_UNARY_FUNCS = {"1/x", "sqrt", "x^2"}
    CONSTANTS = {
        "CONST_PI": math.pi,
        "CONST_C": 299792458,
        "CONST_H": 6.62607015e-34,
        "CONST_G": 6.67430e-11,
    }
    BINARY_OPS = {"+", "-", "*", "/", "^"}
    OP_PRECEDENCE = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}
    MAX_DIGITS = 12

    def digit_count(value):
        return sum(1 for char in value if char.isdigit())

    def format_number(value):
        if value == 0:
            return "0"
        return f"{value:.12g}"

    def parse_scientific_value(value):
        if not value or value == "Error":
            return value, ""
        if "e" not in value.lower():
            return value, ""
        mantissa, exponent = value.lower().split("e", 1)
        return mantissa, exponent

    def compose_scientific_value(mantissa, exponent):
        if exponent in ("", None):
            return mantissa
        return f"{mantissa}e{exponent}"

    def split_display_value(value):
        if not value or value == "0":
            return "0", ""
        if value == "Error":
            return "Error", ""
        if "e" not in value.lower():
            return value, ""

        mantissa, exponent = value.lower().split("e", 1)
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

    mantissa_display = ft.Text(
        value="0",
        text_align=ft.TextAlign.CENTER,
        size=34,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
    )

    exponent_display = ft.Text(
        value="",
        text_align=ft.TextAlign.LEFT,
        size=16,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.BLACK,
    )

    display = ft.Row(
        [
            ft.Container(
                content=memory_indicator,
                width=18,
                alignment=ft.Alignment(-1, 0),
            ),
            ft.Container(content=mantissa_display, alignment=ft.Alignment(1, 0), expand=True),
            ft.Container(
                content=exponent_display,
                width=42,
                alignment=ft.Alignment(-1, -0.75),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=0,
    )

    display_card = ft.Container(
        content=display,
        alignment=ft.Alignment(0, 0),
        padding=ft.padding.symmetric(horizontal=8, vertical=2),
        bgcolor=ft.Colors.GREY_100,
        border=ft.border.all(6, ft.Colors.BROWN_400),
        border_radius=12,
        width=352,
        height=58,
    )

    def update_display():
        shown_value = state["display_value"] or state["current"] or "0"
        mantissa, exponent = split_display_value(shown_value)
        if state["editing_exponent"] and "e" not in (state["current"] or "").lower() and state["current"]:
            exponent = "000"
        mantissa_display.value = mantissa
        exponent_display.value = exponent
        memory_indicator.visible = state["has_memory"]
        update_bracket_buttons()
        update_memory_buttons()
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
        state["memory"] = 0.0
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
        if not state["current"] or state["current"] == "Error":
            return
        if state["editing_exponent"]:
            state["editing_exponent"] = False
            state["display_value"] = ""
            state["replace_on_next_input"] = False
            update_display()
            return
        mantissa, exponent = parse_scientific_value(state["current"])
        state["current"] = compose_scientific_value(mantissa, exponent or "0")
        state["display_value"] = ""
        state["editing_exponent"] = True
        state["replace_on_next_input"] = False
        state["last_was_equals"] = False
        update_display()

    def append_exponent_digit(digit):
        current = state["current"]
        if not current or current == "Error":
            return

        mantissa, exponent = parse_scientific_value(current)
        sign = "-" if exponent.startswith("-") else ""
        digits = exponent.lstrip("-")
        if digits == "0":
            digits = ""
        if len(digits) >= 3:
            return
        digits += digit
        state["current"] = compose_scientific_value(mantissa, f"{sign}{digits or '0'}")
        state["display_value"] = ""
        update_display()

    def recall_memory():
        if not state["has_memory"]:
            return
        state["current"] = format_number(state["memory"])
        state["display_value"] = ""
        state["editing_exponent"] = False
        state["replace_on_next_input"] = False
        state["last_was_equals"] = False
        update_display()

    def can_push_current():
        return bool(state["current"] and state["current"] != "Error")

    def push_current_token():
        if can_push_current():
            state["tokens"].append(state["current"])
            state["current"] = ""

    def apply_top_operator(values, operators):
        if len(values) < 2 or not operators:
            raise ValueError("Invalid expression")
        op = operators.pop()
        right = values.pop()
        left = values.pop()
        values.append(calc_binary(left, right, op))

    def evaluate_expression(tokens):
        values = []
        operators = []

        for token in tokens:
            if token == "(":
                operators.append(token)
            elif token == ")":
                while operators and operators[-1] != "(":
                    apply_top_operator(values, operators)
                if not operators or operators[-1] != "(":
                    raise ValueError("Mismatched brackets")
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
                values.append(float(token))

        while operators:
            if operators[-1] == "(":
                raise ValueError("Mismatched brackets")
            apply_top_operator(values, operators)

        if len(values) != 1:
            raise ValueError("Invalid expression")
        return values[0]

    def preview_for_operator(incoming_op):
        tokens = list(state["tokens"])
        if can_push_current():
            tokens.append(state["current"])
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
                values.append(float(token))

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
        return format_number(values[-1])

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
        return format_number(evaluate_expression(inner_tokens))

    def handle_operator(op):
        if state["current"] == "Error":
            return

        if state["editing_exponent"]:
            state["editing_exponent"] = False

        if can_push_current():
            preview_value = preview_for_operator(op)
            push_current_token()
        elif state["tokens"] and state["tokens"][-1] in BINARY_OPS:
            state["tokens"][-1] = op
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
            state["tokens"].append(state["current"])
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
        if can_push_current():
            tokens.append(state["current"])
        if not tokens:
            return
        if tokens[-1] in BINARY_OPS or tokens[-1] == "(":
            raise ValueError("Incomplete expression")
        open_count = sum(1 for token in tokens if token == "(")
        close_count = sum(1 for token in tokens if token == ")")
        if open_count > close_count:
            tokens.extend(")" for _ in range(open_count - close_count))
        result = evaluate_expression(tokens)
        state["current"] = format_number(result)
        state["display_value"] = ""
        state["tokens"] = []
        state["op"] = ""
        state["editing_exponent"] = False
        state["replace_on_next_input"] = True
        state["last_was_equals"] = True

    # --- Math helpers ---
    def calc_binary(a, b, op):
        if op == "+":
            return a + b
        elif op == "-":
            return a - b
        elif op == "*":
            return a * b
        elif op == "/":
            if b == 0:
                raise ValueError("Division by zero")
            return a / b
        elif op == "^":
            return a ** b

    def calc_extra_unary(x, func):
        if func == "1/x":
            if x == 0:
                raise ValueError("Division by zero")
            return 1 / x
        elif func == "sqrt":
            if x < 0:
                raise ValueError("Domain error")
            return math.sqrt(x)
        elif func == "x^2":
            return x * x
        raise ValueError(f"Unknown function: {func}")

    def calc_unary(x, func):
        trig_direct = {"sin", "cos", "tan", "cot"}
        arc_trig = {"asin", "acos", "atan", "acot"}

        if func in trig_direct and state["mode"] == "Deg":
            x = math.radians(x)

        if func == "sin":
            result = math.sin(x)
        elif func == "cos":
            result = math.cos(x)
        elif func == "tan":
            result = math.tan(x)
        elif func == "cot":
            t = math.tan(x)
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
            state["current"] = format_number(CONSTANTS[char])
            state["display_value"] = ""
            state["editing_exponent"] = False
            state["last_was_equals"] = False
            update_display()

        elif char == "+/-":
            toggle_sign()

        elif char == "EXP":
            start_exponent_edit()

        elif char == "M in":
            if state["current"] and state["current"] != "Error":
                value = float(state["current"])
                if value == 0:
                    clear_memory()
                else:
                    state["memory"] = value
                    state["has_memory"] = True
                update_display()

        elif char == "M+":
            if state["current"] and state["current"] != "Error":
                state["memory"] = state["memory"] + float(state["current"])
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
                    result = calc_extra_unary(float(state["current"]), char)
                    state["current"] = format_number(result)
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                except (ValueError, ZeroDivisionError):
                    state["current"] = "Error"
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                update_display()

        elif char in TRIG_FUNCS:
            if state["current"]:
                try:
                    result = calc_unary(float(state["current"]), char)
                    state["current"] = format_number(result)
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                except (ValueError, ZeroDivisionError):
                    state["current"] = "Error"
                    state["display_value"] = ""
                    state["editing_exponent"] = False
                update_display()

        elif char == "=":
            try:
                evaluate_pending_expression()
            except (ValueError, ZeroDivisionError):
                state["current"] = "Error"
                state["display_value"] = ""
                state["tokens"] = []
                state["op"] = ""
                state["editing_exponent"] = False
                state["replace_on_next_input"] = False
                state["last_was_equals"] = False
            update_display()

        elif char == "C":
            clear()
        elif char == "CE":
            clear_entry()

    # --- Mode toggles ---
    mode_rad_label = ft.Text("Rad", size=11, weight=ft.FontWeight.BOLD)
    mode_deg_label = ft.Text("Deg", size=11, weight=ft.FontWeight.BOLD)
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
        padding=ft.padding.symmetric(horizontal=3, vertical=2),
    )

    base_normal_label = ft.Text("Std", size=11, weight=ft.FontWeight.BOLD)
    base_bases_label = ft.Text("Base", size=11, weight=ft.FontWeight.BOLD)
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
        padding=ft.padding.symmetric(horizontal=3, vertical=2),
    )

    def refresh_mode_control():
        is_deg = state["mode"] == "Deg"
        mode_rad_label.color = ft.Colors.GREY_500 if is_deg else ft.Colors.BLACK
        mode_deg_label.color = ft.Colors.BLACK if is_deg else ft.Colors.GREY_500
        mode_track.content.alignment = (
            ft.MainAxisAlignment.END if is_deg else ft.MainAxisAlignment.START
        )

        is_base_mode = state["base_mode"] == "Base"
        base_normal_label.color = ft.Colors.GREY_500 if is_base_mode else ft.Colors.BLACK
        base_bases_label.color = ft.Colors.BLACK if is_base_mode else ft.Colors.GREY_500
        base_track.content.alignment = (
            ft.MainAxisAlignment.END if is_base_mode else ft.MainAxisAlignment.START
        )

    def toggle_mode(_):
        state["mode"] = "Deg" if state["mode"] == "Rad" else "Rad"
        refresh_mode_control()
        page.update()

    def toggle_base_mode(_):
        state["base_mode"] = "Base" if state["base_mode"] == "Normal" else "Normal"
        refresh_mode_control()
        page.update()

    refresh_mode_control()

    mode_control = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=mode_rad_label,
                    expand=True,
                    alignment=ft.Alignment(-1, 0),
                    padding=ft.padding.only(bottom=2),
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
                    padding=ft.padding.only(bottom=2),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        on_click=toggle_mode,
        alignment=ft.Alignment(0, 0),
        expand=True,
        height=32,
        bgcolor=ft.Colors.with_opacity(0.0, ft.Colors.GREY_200),
        border_radius=6,
        padding=ft.padding.only(left=24, top=2, right=24, bottom=2),
    )

    base_mode_control = ft.Container(
        content=ft.Row(
            [
                ft.Container(
                    content=base_normal_label,
                    expand=True,
                    alignment=ft.Alignment(-1, 0),
                    padding=ft.padding.only(bottom=2),
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
                    padding=ft.padding.only(bottom=2),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=4,
        ),
        on_click=toggle_base_mode,
        alignment=ft.Alignment(0, 0),
        expand=True,
        height=32,
        bgcolor=ft.Colors.with_opacity(0.0, ft.Colors.GREY_200),
        border_radius=6,
        padding=ft.padding.only(left=24, top=2, right=24, bottom=2),
    )

    # --- Button factory ---
    def btn(label, data=None, bgcolor=None, color=None, text_size=17, text_weight=ft.FontWeight.NORMAL, text_ref=None):
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
                padding=ft.padding.symmetric(horizontal=3, vertical=2),
            ),
            data=data if data is not None else label,
            on_click=on_click,
            expand=True,
            height=45,
            style=ft.ButtonStyle(
                bgcolor=bgcolor or ft.Colors.GREY_200,
                color=color or ft.Colors.BLACK,
                shape=ft.RoundedRectangleBorder(radius=6),
                padding=ft.padding.all(0),
            ),
        )

    OP_BG = ft.Colors.ORANGE_200
    EQ_BG = ft.Colors.BLUE_200
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

    # --- Layout ---
    page.add(
        ft.SafeArea(
            minimum_padding=ft.padding.only(left=10, top=0, right=10, bottom=10),
            content=ft.Column(
                expand=True,
                spacing=2,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(bottom=2),
                        content=ft.Column(
                            spacing=2,
                            controls=[
                                ft.Container(height=24, bgcolor=ft.Colors.BLACK),
                                ft.Container(
                                    bgcolor=TOP_BG,
                                    padding=ft.padding.only(top=6, bottom=8),
                                    content=ft.Row([display_card], alignment=ft.MainAxisAlignment.CENTER),
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        bgcolor=SWITCH_BG,
                        padding=ft.padding.symmetric(horizontal=8, vertical=4),
                        content=ft.Row([mode_control, base_mode_control], spacing=8),
                    ),
                    ft.Container(
                        bgcolor=ft.Colors.BLACK,
                        padding=ft.padding.all(8),
                        expand=True,
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Row([
                                    btn("C", bgcolor=CLR_BG, text_weight=ft.FontWeight.BOLD),
                                    btn("CE", bgcolor=CLR_BG, text_weight=ft.FontWeight.BOLD),
                                    memory_in_button,
                                    memory_plus_button,
                                    memory_recall_button,
                                ], spacing=8),
                                ft.Row([
                                    btn("7", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("8", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("9", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    open_bracket_button,
                                    close_bracket_button,
                                ], spacing=8),
                                ft.Row([
                                    btn("4", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("5", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("6", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("*", bgcolor=OP_BG, text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("/", bgcolor=OP_BG, text_size=19, text_weight=ft.FontWeight.BOLD),
                                ], spacing=8),
                                ft.Row([
                                    btn("1", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("2", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("3", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("+", bgcolor=OP_BG, text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("−", data="-", bgcolor=OP_BG, text_size=19, text_weight=ft.FontWeight.BOLD),
                                ], spacing=8),
                                ft.Row([
                                    btn("0", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn(".", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("+/-", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("EXP", text_size=19, text_weight=ft.FontWeight.BOLD),
                                    btn("=", bgcolor=EQ_BG, text_size=19, text_weight=ft.FontWeight.BOLD),
                                ], spacing=8),
                                ft.Row([btn("1/x"), btn("√x̅", data="sqrt"), btn("x²", data="x^2"), btn("xʸ", data="^")], spacing=8),
                                ft.Row([btn("sin"), btn("cos"), btn("tan"), btn("cot")], spacing=8),
                                ft.Row([btn("asin"), btn("acos"), btn("atan"), btn("acot")], spacing=8),
                                ft.Row([btn("sinh"), btn("cosh"), btn("tanh"), btn("coth")], spacing=8),
                                ft.Row([btn("asinh"), btn("acosh"), btn("atanh"), btn("acoth")], spacing=8),
                                ft.Row([btn("π", data="CONST_PI"), btn("c", data="CONST_C"), btn("ℏ", data="CONST_H"), btn("G", data="CONST_G")], spacing=8),
                            ],
                        ),
                    ),
                ],
            ),
        )
    )

    update_bracket_buttons()
    update_memory_buttons()


ft.run(main)
