"""验收标准自动检查脚本，使用标准库 unittest 运行。"""

import subprocess
import sys
import unittest


class TestAcceptance(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "temp_converter.py", *args],
            capture_output=True,
            text=True,
        )

    def test_ac1_c_to_f(self):
        result = self.run_cli("100", "C", "F")
        self.assertEqual(result.returncode, 0)
        self.assertIn("212", result.stdout)

    def test_ac2_f_to_c(self):
        result = self.run_cli("32", "F", "C")
        self.assertEqual(result.returncode, 0)
        self.assertIn("0", result.stdout)

    def test_ac3_c_to_k(self):
        result = self.run_cli("0", "C", "K")
        self.assertEqual(result.returncode, 0)
        self.assertIn("273.15", result.stdout)

    def test_ac4_below_absolute_zero(self):
        result = self.run_cli("-300", "C", "F")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip())

    def test_ac5_invalid_number(self):
        result = self.run_cli("abc", "C", "F")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip())

    def test_ac6_invalid_unit(self):
        result = self.run_cli("100", "X", "F")
        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(result.stderr.strip())


if __name__ == "__main__":
    unittest.main()
