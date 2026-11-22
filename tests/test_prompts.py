import io
import unittest
from contextlib import redirect_stdout
from datetime import date
from unittest.mock import patch

from app.cli import prompts
from app.errors import ValidationError


def answers(*values):
    return patch("builtins.input", side_effect=list(values))


class PromptsTest(unittest.TestCase):
    def test_ask_int_repeats_until_valid(self):
        with answers("abc", "9", "2"), redirect_stdout(io.StringIO()) as out:
            self.assertEqual(prompts.ask_int("Pick", 0, 3), 2)
        self.assertIn("whole number between 0 and 3", out.getvalue())

    def test_ask_float_accepts_commas_and_default(self):
        with answers("1,520.5", ""):
            self.assertEqual(prompts.ask_float("Value"), 1520.5)
            self.assertEqual(prompts.ask_float("Value", 7), 7)

    def test_ask_date_and_month(self):
        with answers("2026-02-30", "2026-02-28", "", "2026-13", "2026-11"), redirect_stdout(io.StringIO()):
            self.assertEqual(prompts.ask_date("Day"), date(2026, 2, 28))
            self.assertEqual(prompts.ask_date("Day", date(2026, 1, 1)), date(2026, 1, 1))
            self.assertEqual(prompts.ask_month("Month", "2026-10"), "2026-11")

    def test_ask_text_uses_validator(self):
        def upper(text):
            if text == "bad":
                raise ValidationError("nope")
            return text.upper()

        with answers("", "bad", "ok"), redirect_stdout(io.StringIO()):
            self.assertEqual(prompts.ask_text("Name", upper), "OK")

    def test_ctrl_c_cancels(self):
        with patch("builtins.input", side_effect=KeyboardInterrupt), redirect_stdout(io.StringIO()):
            with self.assertRaises(prompts.Cancelled):
                prompts.ask_int("Pick", 0, 3)

    def test_run_action_never_crashes(self):
        def boom():
            raise RuntimeError("bug")

        with redirect_stdout(io.StringIO()) as out, self.assertLogs(prompts.log, "ERROR"):
            prompts.run_action(boom, pause_after=False)
        self.assertIn("Something went wrong", out.getvalue())

    def test_print_table(self):
        with redirect_stdout(io.StringIO()) as out:
            prompts.print_table(["A", "Long header"], [(1, "x")])
        self.assertIn("Long header", out.getvalue())


if __name__ == "__main__":
    unittest.main()
