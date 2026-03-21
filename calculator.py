"""
Pocket Calculator
A GUI calculator with basic arithmetic and trigonometric/hyperbolic functions using tkinter.
"""

import tkinter as tk
import math

class Calculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Pocket Calculator")
        self.root.geometry("400x600")  # Increased size for more buttons

        self.display = tk.Entry(root, font=('Arial', 20), justify='right', bd=10)
        self.display.grid(row=0, column=0, columnspan=5, padx=10, pady=10, sticky="nsew")

        # Configure grid weights for resizing
        for i in range(10):
            root.grid_rowconfigure(i, weight=1)
        for i in range(5):
            root.grid_columnconfigure(i, weight=1)

        # Basic button layout
        buttons = [
            ('7', 1, 0), ('8', 1, 1), ('9', 1, 2), ('/', 1, 3),
            ('4', 2, 0), ('5', 2, 1), ('6', 2, 2), ('*', 2, 3),
            ('1', 3, 0), ('2', 3, 1), ('3', 3, 2), ('-', 3, 3),
            ('0', 4, 0), ('.', 4, 1), ('=', 4, 2), ('+', 4, 3),
        ]

        for (text, row, col) in buttons:
            btn = tk.Button(root, text=text, font=('Arial', 14), command=lambda t=text: self.on_button_click(t))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        # Trigonometric functions
        trig_buttons = [
            ('sin', 5, 0), ('cos', 5, 1), ('tan', 5, 2), ('cot', 5, 3),
            ('asin', 6, 0), ('acos', 6, 1), ('atan', 6, 2), ('acot', 6, 3),
        ]

        for (text, row, col) in trig_buttons:
            btn = tk.Button(root, text=text, font=('Arial', 12), command=lambda t=text: self.on_button_click(t))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        # Hyperbolic functions
        hyp_buttons = [
            ('sinh', 7, 0), ('cosh', 7, 1), ('tanh', 7, 2), ('coth', 7, 3),
            ('asinh', 8, 0), ('acosh', 8, 1), ('atanh', 8, 2), ('acoth', 8, 3),
        ]

        for (text, row, col) in hyp_buttons:
            btn = tk.Button(root, text=text, font=('Arial', 10), command=lambda t=text: self.on_button_click(t))
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")

        # Clear buttons, Pi, and mode slider
        tk.Button(root, text='C', font=('Arial', 14), command=self.clear).grid(row=9, column=0, padx=2, pady=2, sticky="nsew")
        tk.Button(root, text='CE', font=('Arial', 14), command=self.clear_entry).grid(row=9, column=1, padx=2, pady=2, sticky="nsew")
        tk.Button(root, text='π', font=('Arial', 14), command=lambda: self.on_button_click('pi')).grid(row=9, column=2, padx=2, pady=2, sticky="nsew")
        self.slider_canvas = tk.Canvas(root, width=100, height=50, bg='white', highlightthickness=0)
        self.slider_canvas.grid(row=9, column=3, columnspan=2, padx=2, pady=2, sticky="nsew")
        # Draw slider track
        self.slider_canvas.create_rectangle(10, 10, 90, 20, fill='lightgray', outline='gray')
        # Draw knob (initially on left for Rad)
        self.knob = self.slider_canvas.create_oval(10, 5, 30, 25, fill='blue', outline='darkblue')
        # Draw labels underneath
        self.slider_canvas.create_text(20, 35, text='Rad', font=('Arial', 10))
        self.slider_canvas.create_text(80, 35, text='Deg', font=('Arial', 10))
        # Bind click event
        self.slider_canvas.bind('<Button-1>', self.slider_click)

        self.current = ''
        self.op = ''
        self.first = 0.0
        self.mode = 'Rad'
        self.last_was_equals = False

    def on_button_click(self, char):
        trig_funcs = ['sin', 'cos', 'tan', 'cot', 'asin', 'acos', 'atan', 'acot',
                      'sinh', 'cosh', 'tanh', 'coth', 'asinh', 'acosh', 'atanh', 'acoth']
        
        if char.isdigit() or char == '.' or char == 'pi':
            # Clear display after equals when entering new digit or Pi
            if self.last_was_equals and (char.isdigit() or char == 'pi'):
                self.clear()
                self.last_was_equals = False
            
            # Prevent duplicate decimal points
            if char == '.' and '.' in self.current:
                return
            
            if char == 'pi':
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
                    self.display.delete(0, tk.END)
                    self.display.insert(0, str(result))
                    self.current = str(result)
                except (ValueError, ZeroDivisionError):
                    self.display.delete(0, tk.END)
                    self.display.insert(0, "Error")
                    self.current = ''
        elif char == '=':
            if self.current and self.op:
                try:
                    second = float(self.current)
                    result = self.calculate(self.first, second, self.op)
                    self.display.delete(0, tk.END)
                    self.display.insert(0, str(result))
                    self.current = str(result)
                    self.op = ''
                    self.last_was_equals = True
                except ValueError as e:
                    self.display.delete(0, tk.END)
                    self.display.insert(0, "Error")
                    self.current = ''
                    self.op = ''
                    self.last_was_equals = False
            elif self.current:
                # Equals pressed without operation - just flag for next input
                self.last_was_equals = True

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

    def slider_click(self, event):
        if self.mode == 'Rad':
            self.slider_canvas.coords(self.knob, 70, 5, 90, 25)
            self.mode = 'Deg'
        else:
            self.slider_canvas.coords(self.knob, 10, 5, 30, 25)
            self.mode = 'Rad'

    def clear(self):
        self.current = ''
        self.op = ''
        self.first = 0.0
        self.display.delete(0, tk.END)

    def clear_entry(self):
        self.current = ''
        self.update_display()

    def update_display(self):
        self.display.delete(0, tk.END)
        self.display.insert(0, self.current)

if __name__ == "__main__":
    root = tk.Tk()
    calc = Calculator(root)
    root.mainloop()