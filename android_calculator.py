"""
fx451m-Calculator Android App
A mobile calculator with basic arithmetic and trigonometric/hyperbolic functions using Kivy.
"""

import math
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.togglebutton import ToggleButton
from kivy.metrics import dp
from kivy.core.window import Window


class Calculator(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = dp(5)
        self.padding = dp(10)

        # Calculator state
        self.current = ''
        self.op = ''
        self.first = 0.0
        self.mode = 'Rad'  # 'Rad' or 'Deg'
        self.last_was_equals = False

        # Display
        self.display = TextInput(
            text='',
            font_size=dp(32),
            size_hint_y=0.15,
            halign='right',
            multiline=False,
            readonly=True,
            background_color=(0.9, 0.9, 0.9, 1)
        )
        self.add_widget(self.display)

        # Mode toggle
        mode_layout = BoxLayout(size_hint_y=0.08, spacing=dp(5))
        mode_layout.add_widget(Label(text="Mode:", size_hint_x=0.3))

        self.mode_toggle = ToggleButton(
            text='Rad',
            group='mode',
            state='down',
            size_hint_x=0.35
        )
        self.mode_toggle.bind(on_press=self.toggle_mode)

        deg_toggle = ToggleButton(
            text='Deg',
            group='mode',
            size_hint_x=0.35
        )
        deg_toggle.bind(on_press=self.toggle_mode)

        mode_layout.add_widget(self.mode_toggle)
        mode_layout.add_widget(deg_toggle)
        self.add_widget(mode_layout)

        # Button grid
        button_grid = GridLayout(cols=4, spacing=dp(3), size_hint_y=0.77)

        # Row 1: Trigonometric functions
        trig_buttons = ['sin', 'cos', 'tan', 'cot']
        for btn_text in trig_buttons:
            btn = Button(text=btn_text, font_size=dp(16))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Row 2: Inverse trig functions
        inv_trig_buttons = ['asin', 'acos', 'atan', 'acot']
        for btn_text in inv_trig_buttons:
            btn = Button(text=btn_text, font_size=dp(14))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Row 3: Hyperbolic functions
        hyp_buttons = ['sinh', 'cosh', 'tanh', 'coth']
        for btn_text in hyp_buttons:
            btn = Button(text=btn_text, font_size=dp(14))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Row 4: Inverse hyperbolic functions
        inv_hyp_buttons = ['asinh', 'acosh', 'atanh', 'acoth']
        for btn_text in inv_hyp_buttons:
            btn = Button(text=btn_text, font_size=dp(12))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Row 5: 7, 8, 9, /
        num_buttons_1 = ['7', '8', '9', '/']
        for btn_text in num_buttons_1:
            btn = Button(text=btn_text, font_size=dp(20))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Row 6: 4, 5, 6, *
        num_buttons_2 = ['4', '5', '6', '*']
        for btn_text in num_buttons_2:
            btn = Button(text=btn_text, font_size=dp(20))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Row 7: 1, 2, 3, -
        num_buttons_3 = ['1', '2', '3', '-']
        for btn_text in num_buttons_3:
            btn = Button(text=btn_text, font_size=dp(20))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Row 8: 0, ., =, +
        num_buttons_4 = ['0', '.', '=', '+']
        for btn_text in num_buttons_4:
            btn = Button(text=btn_text, font_size=dp(20))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Row 9: C, CE, π
        control_buttons = ['C', 'CE', 'π']
        for btn_text in control_buttons:
            btn = Button(text=btn_text, font_size=dp(18))
            btn.bind(on_press=self.on_button_press)
            button_grid.add_widget(btn)

        # Empty space for alignment
        button_grid.add_widget(Label())

        self.add_widget(button_grid)

    def toggle_mode(self, instance):
        if instance.text == 'Rad':
            self.mode = 'Rad'
        else:
            self.mode = 'Deg'

    def on_button_press(self, instance):
        char = instance.text
        self.process_input(char)

    def process_input(self, char):
        trig_funcs = ['sin', 'cos', 'tan', 'cot', 'asin', 'acos', 'atan', 'acot',
                      'sinh', 'cosh', 'tanh', 'coth', 'asinh', 'acosh', 'atanh', 'acoth']

        if char.isdigit() or char == '.' or char == 'π':
            # Clear display after equals when entering new digit or Pi
            if self.last_was_equals and (char.isdigit() or char == 'π'):
                self.clear()
                self.last_was_equals = False

            # Prevent duplicate decimal points
            if char == '.' and '.' in self.current:
                return

            if char == 'π':
                self.current = str(math.pi)
            else:
                self.current += char
            self.update_display()

        elif char in ['+', '-', '*', '/']:
            if self.current:
                self.first = float(self.current)
                self.op = char
                self.current = ''

        elif char in trig_funcs:
            if self.current:
                try:
                    result = self.calculate_unary(float(self.current), char)
                    self.current = str(result)
                    self.update_display()
                except (ValueError, ZeroDivisionError):
                    self.current = 'Error'
                    self.update_display()

        elif char == '=':
            if self.current and self.op:
                try:
                    second = float(self.current)
                    result = self.calculate(self.first, second, self.op)
                    self.current = str(result)
                    self.op = ''
                    self.last_was_equals = True
                    self.update_display()
                except ValueError:
                    self.current = 'Error'
                    self.op = ''
                    self.last_was_equals = False
                    self.update_display()
            elif self.current:
                # Equals pressed without operation - just flag for next input
                self.last_was_equals = True

        elif char == 'C':
            self.clear()

        elif char == 'CE':
            self.clear_entry()

    def calculate(self, a, b, op):
        if op == '+':
            return a + b
        elif op == '-':
            return a - b
        elif op == '*':
            return a * b
        elif op == '/':
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b

    def calculate_unary(self, x, op):
        trig_direct = ['sin', 'cos', 'tan', 'cot']
        arc_trig = ['asin', 'acos', 'atan', 'acot']

        if op in trig_direct:
            if self.mode == 'Deg':
                x = math.radians(x)

        if op == 'sin':
            result = math.sin(x)
        elif op == 'cos':
            result = math.cos(x)
        elif op == 'tan':
            result = math.tan(x)
        elif op == 'cot':
            tan_x = math.tan(x)
            if tan_x == 0:
                raise ValueError("Undefined")
            result = 1 / tan_x
        elif op == 'asin':
            if -1 <= x <= 1:
                result = math.asin(x)
            else:
                raise ValueError("Domain error")
        elif op == 'acos':
            if -1 <= x <= 1:
                result = math.acos(x)
            else:
                raise ValueError("Domain error")
        elif op == 'atan':
            result = math.atan(x)
        elif op == 'acot':
            result = math.pi / 2 - math.atan(x)
        elif op == 'sinh':
            result = math.sinh(x)
        elif op == 'cosh':
            result = math.cosh(x)
        elif op == 'tanh':
            result = math.tanh(x)
        elif op == 'coth':
            tanh_x = math.tanh(x)
            if tanh_x == 0:
                raise ValueError("Undefined")
            result = 1 / tanh_x
        elif op == 'asinh':
            result = math.asinh(x)
        elif op == 'acosh':
            if x >= 1:
                result = math.acosh(x)
            else:
                raise ValueError("Domain error")
        elif op == 'atanh':
            if -1 < x < 1:
                result = math.atanh(x)
            else:
                raise ValueError("Domain error")
        elif op == 'acoth':
            if abs(x) > 1:
                result = math.atanh(1 / x)
            else:
                raise ValueError("Domain error")

        if op in arc_trig:
            if self.mode == 'Deg':
                result = math.degrees(result)

        return result

    def clear(self):
        self.current = ''
        self.op = ''
        self.first = 0.0
        self.update_display()

    def clear_entry(self):
        self.current = ''
        self.update_display()

    def update_display(self):
        self.display.text = self.current


class CalculatorApp(App):
    def build(self):
        self.title = 'fx451m-Calculator'
        Window.clearcolor = (0.95, 0.95, 0.95, 1)  # Light gray background
        return Calculator()


if __name__ == '__main__':
    CalculatorApp().run()