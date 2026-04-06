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
    page.bgcolor = ft.Colors.WHITE

    # --- Calculator state ---
    state = {
        "current": "",
        "op": "",
        "first": 0.0,
        "memory": 0.0,
        "has_memory": False,
        "mode": "Rad",
        "base_mode": "Normal",
        "editing_exponent": False,
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
                width=34,
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
        padding=ft.padding.symmetric(horizontal=8, vertical=4),
        bgcolor=ft.Colors.GREY_100,
        border=ft.border.all(6, ft.Colors.BROWN_400),
        border_radius=12,
        height=58,
        margin=ft.margin.only(bottom=8),
    )

    def update_display():
        mantissa, exponent = split_display_value(state["current"] if state["current"] else "0")
        if state["editing_exponent"] and "e" not in (state["current"] or "").lower() and state["current"]:
            exponent = "000"
        mantissa_display.value = mantissa
        exponent_display.value = exponent
        memory_indicator.visible = state["has_memory"]
        page.update()

    def clear():
        state["current"] = ""
        state["op"] = ""
        state["first"] = 0.0
        state["editing_exponent"] = False
        state["last_was_equals"] = False
        update_display()

    def clear_entry():
        state["current"] = ""
        state["editing_exponent"] = False
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
            update_display()
            return

        if current.startswith("-"):
            state["current"] = current[1:]
        else:
            if current != "0":
                state["current"] = f"-{current}"
        update_display()

    def start_exponent_edit():
        if not state["current"] or state["current"] == "Error":
            return
        mantissa, exponent = parse_scientific_value(state["current"])
        state["current"] = compose_scientific_value(mantissa, exponent or "0")
        state["editing_exponent"] = True
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
        update_display()

    def recall_memory():
        if not state["has_memory"]:
            return
        state["current"] = format_number(state["memory"])
        state["editing_exponent"] = False
        state["last_was_equals"] = False
        update_display()

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

            if state["last_was_equals"] and char.isdigit():
                clear()
            state["last_was_equals"] = False

            if state["current"] == "Error":
                state["current"] = ""

            if char == "." and "." in state["current"]:
                return
            if char.isdigit() and digit_count(state["current"]) >= MAX_DIGITS:
                return
            state["current"] += char
            update_display()

        elif char in CONSTANTS:
            if state["current"] == "Error":
                state["current"] = ""
            state["current"] = format_number(CONSTANTS[char])
            state["editing_exponent"] = False
            state["last_was_equals"] = False
            update_display()

        elif char == "+/-":
            toggle_sign()

        elif char == "EXP":
            start_exponent_edit()

        elif char == "M in":
            if state["current"] and state["current"] != "Error":
                state["memory"] = float(state["current"])
                state["has_memory"] = True
                update_display()

        elif char == "M+":
            if state["current"] and state["current"] != "Error":
                state["memory"] = state["memory"] + float(state["current"])
                state["has_memory"] = True
                update_display()

        elif char == "MR":
            recall_memory()

        elif char in ("(", ")"):
            return

        elif char in ("+", "-", "*", "/", "^"):
            if state["current"]:
                state["first"] = float(state["current"])
                state["op"] = char
                state["current"] = ""
                state["editing_exponent"] = False
                state["last_was_equals"] = False

        elif char in EXTRA_UNARY_FUNCS:
            if state["current"]:
                try:
                    result = calc_extra_unary(float(state["current"]), char)
                    state["current"] = format_number(result)
                    state["editing_exponent"] = False
                except (ValueError, ZeroDivisionError):
                    state["current"] = "Error"
                    state["editing_exponent"] = False
                update_display()

        elif char in TRIG_FUNCS:
            if state["current"]:
                try:
                    result = calc_unary(float(state["current"]), char)
                    state["current"] = format_number(result)
                    state["editing_exponent"] = False
                except (ValueError, ZeroDivisionError):
                    state["current"] = "Error"
                    state["editing_exponent"] = False
                update_display()

        elif char == "=":
            if state["current"] and state["op"]:
                try:
                    result = calc_binary(
                        state["first"], float(state["current"]), state["op"]
                    )
                    state["current"] = format_number(result)
                    state["op"] = ""
                    state["editing_exponent"] = False
                    state["last_was_equals"] = True
                except (ValueError, ZeroDivisionError):
                    state["current"] = "Error"
                    state["op"] = ""
                    state["editing_exponent"] = False
                    state["last_was_equals"] = False
                update_display()
            elif state["current"]:
                state["editing_exponent"] = False
                state["last_was_equals"] = True

        elif char == "C":
            clear()
        elif char == "CE":
            clear_entry()

    # --- Mode toggles ---
    mode_rad_label = ft.Text("Rad", size=10, weight=ft.FontWeight.BOLD)
    mode_deg_label = ft.Text("Deg", size=10, weight=ft.FontWeight.BOLD)
    mode_thumb = ft.Container(
        width=22,
        height=10,
        border_radius=6,
        bgcolor=ft.Colors.WHITE,
        animate=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
    )
    mode_track = ft.Container(
        content=ft.Row(
            [mode_thumb],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=52,
        height=14,
        border_radius=7,
        bgcolor=ft.Colors.BLUE_200,
        padding=ft.padding.symmetric(horizontal=3, vertical=2),
    )

    base_normal_label = ft.Text("Normal", size=10, weight=ft.FontWeight.BOLD)
    base_bases_label = ft.Text("Base", size=10, weight=ft.FontWeight.BOLD)
    base_thumb = ft.Container(
        width=22,
        height=10,
        border_radius=6,
        bgcolor=ft.Colors.WHITE,
        animate=ft.Animation(140, ft.AnimationCurve.EASE_IN_OUT),
    )
    base_track = ft.Container(
        content=ft.Row(
            [base_thumb],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        width=52,
        height=14,
        border_radius=7,
        bgcolor=ft.Colors.GREEN_200,
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
        content=ft.Column(
            [
                ft.Row(
                    [mode_rad_label, mode_deg_label],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=mode_track,
                    alignment=ft.Alignment(0, 1),
                    expand=True,
                ),
            ],
            spacing=0,
        ),
        on_click=toggle_mode,
        alignment=ft.Alignment(0, 0),
        expand=True,
        height=32,
        bgcolor=ft.Colors.GREY_200,
        border_radius=6,
        padding=ft.padding.only(left=8, top=2, right=8, bottom=2),
    )

    base_mode_control = ft.Container(
        content=ft.Column(
            [
                ft.Row(
                    [base_normal_label, base_bases_label],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.Container(
                    content=base_track,
                    alignment=ft.Alignment(0, 1),
                    expand=True,
                ),
            ],
            spacing=0,
        ),
        on_click=toggle_base_mode,
        alignment=ft.Alignment(0, 0),
        expand=True,
        height=32,
        bgcolor=ft.Colors.GREY_200,
        border_radius=6,
        padding=ft.padding.only(left=8, top=2, right=8, bottom=2),
    )

    # --- Button factory ---
    def btn(label, data=None, bgcolor=None, color=None, text_size=14):
        return ft.Button(
            content=ft.Container(
                content=ft.Text(
                    label,
                    size=text_size,
                    text_align=ft.TextAlign.CENTER,
                    no_wrap=True,
                ),
                alignment=ft.Alignment(0, 0),
                padding=ft.padding.symmetric(horizontal=3, vertical=2),
            ),
            data=data if data is not None else label,
            on_click=on_click,
            expand=True,
            height=47,
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

    # --- Layout ---
    page.add(
        ft.SafeArea(
            minimum_padding=ft.padding.only(left=10, top=38, right=10, bottom=10),
            content=ft.Column(
                expand=True,
                spacing=8,
                controls=[
                    display_card,
                    ft.Row([mode_control, base_mode_control], spacing=8),
                    ft.Row([
                        btn("C", bgcolor=CLR_BG, text_size=12),
                        btn("CE", bgcolor=CLR_BG, text_size=12),
                        btn("M in", text_size=11),
                        btn("M+", text_size=12),
                        btn("MR", text_size=12),
                    ], spacing=8),
                    ft.Row([
                        btn("7", text_size=20),
                        btn("8", text_size=20),
                        btn("9", text_size=20),
                        btn("(", text_size=18),
                        btn(")", text_size=18),
                    ], spacing=8),
                    ft.Row([
                        btn("4", text_size=20),
                        btn("5", text_size=20),
                        btn("6", text_size=20),
                        btn("*", bgcolor=OP_BG, text_size=20),
                        btn("/", bgcolor=OP_BG, text_size=20),
                    ], spacing=8),
                    ft.Row([
                        btn("1", text_size=20),
                        btn("2", text_size=20),
                        btn("3", text_size=20),
                        btn("+", bgcolor=OP_BG, text_size=20),
                        btn("-", bgcolor=OP_BG, text_size=20),
                    ], spacing=8),
                    ft.Row([
                        btn("0", text_size=20),
                        btn(".", text_size=20),
                        btn("+/-", text_size=11),
                        btn("EXP", text_size=12),
                        btn("=", bgcolor=EQ_BG, text_size=20),
                    ], spacing=8),
                    ft.Row([btn("1/x"), btn("sqrt"), btn("x^2"), btn("x^y", data="^")], spacing=8),
                    # Trig
                    ft.Row([btn("sin"), btn("cos"), btn("tan"), btn("cot")], spacing=8),
                    ft.Row([btn("asin"), btn("acos"), btn("atan"), btn("acot")], spacing=8),
                    # Hyperbolic
                    ft.Row([btn("sinh"), btn("cosh"), btn("tanh"), btn("coth")], spacing=8),
                    ft.Row([btn("asinh"), btn("acosh"), btn("atanh"), btn("acoth")], spacing=8),
                    ft.Row([btn("Pi", data="CONST_PI"), btn("c", data="CONST_C"), btn("h", data="CONST_H"), btn("G", data="CONST_G")], spacing=8),
                ],
            ),
        )
    )


ft.run(main)
