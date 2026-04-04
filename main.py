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
    page.window.height = 720
    page.padding = 10
    page.bgcolor = ft.Colors.WHITE

    # --- Calculator state ---
    state = {
        "current": "",
        "op": "",
        "first": 0.0,
        "mode": "Rad",
        "last_was_equals": False,
    }

    TRIG_FUNCS = {
        "sin", "cos", "tan", "cot",
        "asin", "acos", "atan", "acot",
        "sinh", "cosh", "tanh", "coth",
        "asinh", "acosh", "atanh", "acoth",
    }

    # --- Display ---
    display = ft.TextField(
        value="0",
        text_align=ft.TextAlign.RIGHT,
        text_size=28,
        read_only=True,
        filled=True,
        border_radius=8,
    )

    def update_display():
        display.value = state["current"] if state["current"] else "0"
        page.update()

    def clear():
        state["current"] = ""
        state["op"] = ""
        state["first"] = 0.0
        state["last_was_equals"] = False
        update_display()

    def clear_entry():
        state["current"] = ""
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

        if char.isdigit() or char == "." or char == "π":
            if state["last_was_equals"] and (char.isdigit() or char == "π"):
                clear()
            state["last_was_equals"] = False

            if char == "." and "." in state["current"]:
                return
            if char == "π":
                state["current"] = str(math.pi)
            else:
                state["current"] += char
            update_display()

        elif char in ("+", "-", "*", "/"):
            if state["current"]:
                state["first"] = float(state["current"])
                state["op"] = char
                state["current"] = ""
                state["last_was_equals"] = False

        elif char in TRIG_FUNCS:
            if state["current"]:
                try:
                    result = calc_unary(float(state["current"]), char)
                    state["current"] = str(result)
                except (ValueError, ZeroDivisionError):
                    state["current"] = "Error"
                update_display()

        elif char == "=":
            if state["current"] and state["op"]:
                try:
                    result = calc_binary(
                        state["first"], float(state["current"]), state["op"]
                    )
                    state["current"] = str(result)
                    state["op"] = ""
                    state["last_was_equals"] = True
                except (ValueError, ZeroDivisionError):
                    state["current"] = "Error"
                    state["op"] = ""
                    state["last_was_equals"] = False
                update_display()
            elif state["current"]:
                state["last_was_equals"] = True

        elif char == "C":
            clear()
        elif char == "CE":
            clear_entry()

    # --- Mode toggle ---
    mode_label = ft.Text("Mode: Rad", size=16, weight=ft.FontWeight.BOLD)

    def on_mode_change(e):
        state["mode"] = "Deg" if e.control.value else "Rad"
        mode_label.value = f"Mode: {state['mode']}"
        page.update()

    mode_switch = ft.Switch(value=False, label="Deg", on_change=on_mode_change)

    # --- Button factory ---
    def btn(label, data=None, bgcolor=None, color=None, text_size=14):
        return ft.Button(
            content=ft.Text(label, size=text_size),
            data=data if data is not None else label,
            on_click=on_click,
            expand=True,
            height=48,
            style=ft.ButtonStyle(
                bgcolor=bgcolor or ft.Colors.GREY_200,
                color=color or ft.Colors.BLACK,
                shape=ft.RoundedRectangleBorder(radius=6),
            ),
        )

    OP_BG = ft.Colors.ORANGE_200
    EQ_BG = ft.Colors.BLUE_200
    CLR_BG = ft.Colors.RED_200

    # --- Layout ---
    page.add(
        ft.Column(
            expand=True,
            spacing=4,
            controls=[
                display,
                ft.Row([mode_label, mode_switch]),
                # Trig
                ft.Row([btn("sin"), btn("cos"), btn("tan"), btn("cot")]),
                ft.Row([btn("asin"), btn("acos"), btn("atan"), btn("acot")]),
                # Hyperbolic
                ft.Row([btn("sinh"), btn("cosh"), btn("tanh"), btn("coth")]),
                ft.Row([btn("asinh"), btn("acosh"), btn("atanh"), btn("acoth")]),
                # Numbers & operators
                ft.Row([btn("7", text_size=20), btn("8", text_size=20), btn("9", text_size=20), btn("/", bgcolor=OP_BG, text_size=20)]),
                ft.Row([btn("4", text_size=20), btn("5", text_size=20), btn("6", text_size=20), btn("*", bgcolor=OP_BG, text_size=20)]),
                ft.Row([btn("1", text_size=20), btn("2", text_size=20), btn("3", text_size=20), btn("-", bgcolor=OP_BG, text_size=20)]),
                ft.Row([btn("0", text_size=20), btn(".", text_size=20), btn("=", bgcolor=EQ_BG, text_size=20), btn("+", bgcolor=OP_BG, text_size=20)]),
                ft.Row([btn("C", bgcolor=CLR_BG), btn("CE", bgcolor=CLR_BG), btn("π", data="π")]),
            ],
        )
    )


ft.run(main)
