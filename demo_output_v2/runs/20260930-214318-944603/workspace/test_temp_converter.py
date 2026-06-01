"""温度转换的自动测试，使用标准库 unittest。"""

import unittest

from temp_converter import (
    TemperatureError,
    convert,
    format_result,
    main,
    validate_input,
)


class TestConvert(unittest.TestCase):
    def test_celsius_to_fahrenheit(self):
        self.assertAlmostEqual(convert(100, "C", "F"), 212.0)

    def test_fahrenheit_to_celsius(self):
        self.assertAlmostEqual(convert(32, "F", "C"), 0.0)

    def test_celsius_to_kelvin(self):
        self.assertAlmostEqual(convert(0, "C", "K"), 273.15)

    def test_kelvin_to_celsius(self):
        self.assertAlmostEqual(convert(273.15, "K", "C"), 0.0)

    def test_same_unit_identity(self):
        for unit in ("C", "F", "K"):
            self.assertAlmostEqual(convert(42, unit, unit), 42.0)

    def test_lowercase_units(self):
        self.assertAlmostEqual(convert(100, "c", "f"), 212.0)

    def test_absolute_zero_celsius(self):
        self.assertAlmostEqual(convert(-273.15, "C", "K"), 0.0)

    def test_absolute_zero_fahrenheit(self):
        self.assertAlmostEqual(convert(-459.67, "F", "K"), 0.0)

    def test_below_absolute_zero_celsius(self):
        with self.assertRaises(TemperatureError):
            convert(-300, "C", "F")

    def test_below_absolute_zero_kelvin(self):
        with self.assertRaises(TemperatureError):
            convert(-1, "K", "C")

    def test_invalid_number(self):
        with self.assertRaises(TemperatureError):
            convert("abc", "C", "F")

    def test_invalid_unit(self):
        with self.assertRaises(TemperatureError):
            convert(100, "X", "F")

    def test_invalid_target_unit(self):
        with self.assertRaises(TemperatureError):
            convert(100, "C", "X")


class TestValidateInput(unittest.TestCase):
    def test_returns_normalized(self):
        value, frm, to = validate_input("100", "c", "f")
        self.assertEqual(value, 100.0)
        self.assertEqual(frm, "C")
        self.assertEqual(to, "F")


class TestFormatResult(unittest.TestCase):
    def test_integer_like(self):
        self.assertEqual(format_result(212.0, "F"), "212 F")

    def test_decimal(self):
        self.assertEqual(format_result(273.15, "K"), "273.15 K")

    def test_negative_zero(self):
        self.assertEqual(format_result(-0.0, "C"), "0 C")


class TestMain(unittest.TestCase):
    def test_success_exit_code(self):
        self.assertEqual(main(["100", "C", "F"]), 0)

    def test_error_exit_code(self):
        self.assertEqual(main(["-300", "C", "F"]), 1)

    def test_invalid_number_exit_code(self):
        self.assertEqual(main(["abc", "C", "F"]), 1)

    def test_invalid_unit_exit_code(self):
        self.assertEqual(main(["100", "X", "F"]), 1)


if __name__ == "__main__":
    unittest.main()
