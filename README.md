# fx451m-Calculator

A comprehensive GUI pocket calculator written in Python using tkinter that performs basic arithmetic operations and advanced trigonometric/hyperbolic functions.

## Features

- **Basic Arithmetic:**
  - Addition (+)
  - Subtraction (-)
  - Multiplication (*)
  - Division (/)
  - Decimal point support with duplicate prevention
  - Error handling for division by zero

- **Trigonometric Functions:**
  - sin, cos, tan, cot
  - asin (arc sine), acos (arc cosine), atan (arc tangent), acot (arc cotangent)

- **Hyperbolic Functions:**
  - sinh, cosh, tanh, coth
  - asinh (arc hyperbolic sine), acosh (arc hyperbolic cosine), atanh (arc hyperbolic tangent), acoth (arc hyperbolic cotangent)

- **Interface:**
  - Clear (C) and Clear Entry (CE) buttons
  - Degrees/Radians slider toggle
  - Pi (π) constant button (clears display first)
  - User-friendly graphical interface
  - Immediate execution for trigonometric and hyperbolic functions (no "=" needed)
  - Auto-clear after equals when entering new numbers

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/fx451m-Calculator.git
   cd fx451m-Calculator
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv .venv
   ```

3. Activate the virtual environment:
   - Windows:
     ```bash
     .venv\Scripts\activate
     ```
   - Linux/Mac:
     ```bash
     source .venv/bin/activate
     ```

4. The calculator uses only standard library modules (tkinter, math), so no additional dependencies are required.

## How to Use

1. **Mode Selection:** Click the "Rad" or "Deg" button to toggle between radians and degrees mode. Default is radians.

2. **Arithmetic Operations:** Enter first number, click operation (+, -, *, /), enter second number, press '='.

3. **Trigonometric/Hyperbolic Functions:** Enter a number, then click the function button. The result appears immediately.
   - In degrees mode: sin(30) computes sin(30°) and returns the value.
   - In radians mode: sin(π/2) computes sin(π/2 radians).
   - Inverse functions return results in the selected mode.

4. **Constants:** Click the π button to insert the value of Pi (clears any existing number first).

5. **Clearing:** Use 'C' to clear everything, 'CE' to clear the current entry.

6. **Special Behaviors:**
   - Pressing "=" after entering a number (without operation) allows the next digit/Pi entry to clear the display
   - Duplicate decimal points are ignored
   - Pi button always clears the display before inserting π

## Running the Calculator

Ensure you have Python installed on your system (tkinter is included with Python).

Run the calculator:
```bash
python calculator.py
```

Or using the virtual environment:
```bash
.venv\Scripts\python.exe calculator.py
```

## Requirements

- Python 3.x
- tkinter (included with Python standard installation)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- Built with Python's tkinter library for the GUI
- Mathematical functions powered by Python's math module
   ```
3. A window will open with the calculator interface.

## Notes

- Trigonometric functions respect the Rad/Deg mode.
- Hyperbolic functions are not affected by angle mode.
- Domain errors (e.g., asin(2)) will display "Error".
- Undefined results (e.g., tan(90°)) will display "Error".

## Requirements

- Python 3.x (with tkinter and math modules, which are standard)