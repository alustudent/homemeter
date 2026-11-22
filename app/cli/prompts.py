import getpass
import logging
import re
from datetime import date
from typing import Callable, Sequence

from app.errors import HomeMeterError, ValidationError

log = logging.getLogger(__name__)

LINE = "=" * 56
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class Cancelled(Exception):
    """The user pressed Ctrl+C or chose 0 to go back."""


def _read(prompt: str) -> str:
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print()
        raise Cancelled from None


def header(title: str, subtitle: str | None = None) -> None:
    print(f"\n{LINE}\n  {title}")
    if subtitle:
        print(f"  {subtitle}")
    print(LINE)


def success(message: str) -> None:
    print(f"[OK] {message}")


def warn(message: str) -> None:
    print(f"[!] {message}")


def error(message: str) -> None:
    print(f"[X] {message}")


def pause() -> None:
    _read("\nPress Enter to continue...")


def money(amount: float) -> str:
    return f"{amount:,.0f} RWF"


def ask_text(prompt: str, validate: Callable[[str], str] | None = None, default: str | None = None) -> str:
    """Ask until the answer is not empty and passes `validate`, which returns the cleaned value."""
    suffix = f" [{default}]" if default else ""
    while True:
        answer = _read(f"{prompt}{suffix}: ").strip() or (default or "")
        if not answer:
            error("This cannot be empty.")
            continue
        try:
            return validate(answer) if validate else answer
        except ValidationError as exc:
            error(str(exc))


def ask_int(prompt: str, low: int, high: int, default: int | None = None) -> int:
    suffix = f" [{default}]" if default is not None else ""
    while True:
        answer = _read(f"{prompt}{suffix}: ").strip()
        if not answer and default is not None:
            return default
        try:
            number = int(answer)
        except ValueError:
            error(f"Please type a whole number between {low} and {high}.")
            continue
        if low <= number <= high:
            return number
        error(f"Please type a whole number between {low} and {high}.")


def ask_float(prompt: str, default: float | None = None) -> float:
    suffix = f" [{default:g}]" if default is not None else ""
    while True:
        answer = _read(f"{prompt}{suffix}: ").strip().replace(",", "")
        if not answer and default is not None:
            return default
        try:
            return float(answer)
        except ValueError:
            error("Please type a number, for example 1520.5")


def ask_date(prompt: str, default: date | None = None) -> date:
    default = default or date.today()
    while True:
        answer = _read(f"{prompt} (YYYY-MM-DD) [{default}]: ").strip()
        if not answer:
            return default
        try:
            return date.fromisoformat(answer)
        except ValueError:
            error("Please type a real date like 2026-11-20.")


def ask_month(prompt: str, default: str) -> str:
    while True:
        answer = _read(f"{prompt} (YYYY-MM) [{default}]: ").strip() or default
        if MONTH_PATTERN.match(answer):
            return answer
        error("Please type a month like 2026-11.")


def ask_secret(prompt: str) -> str:
    try:
        return getpass.getpass(f"{prompt}: ")
    except KeyboardInterrupt:
        print()
        raise Cancelled from None


def confirm(prompt: str) -> bool:
    return _read(f"{prompt} (y/n): ").strip().lower() in ("y", "yes")


def choose(prompt: str, labels: Sequence[str]) -> int:
    """Show a numbered list and return the index picked. 0 goes back."""
    if not labels:
        warn("There is nothing to choose from yet.")
        raise Cancelled
    for number, label in enumerate(labels, start=1):
        print(f" {number}. {label}")
    print(" 0. Back")
    picked = ask_int(prompt, 0, len(labels))
    if picked == 0:
        raise Cancelled
    return picked - 1


def print_table(headers: Sequence[str], rows: Sequence[Sequence[object]]) -> None:
    if not rows:
        warn("Nothing to show yet.")
        return
    cells = [[str(c) for c in row] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in cells)) for i, h in enumerate(headers)]
    print("  ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  ".join("-" * w for w in widths))
    for row in cells:
        print("  ".join(c.ljust(w) for c, w in zip(row, widths)))


def run_action(action: Callable[[], None], pause_after: bool = True) -> None:
    """Run one menu action so that no error can crash the app."""
    try:
        action()
    except Cancelled:
        print("Cancelled. Back to the menu.")
    except HomeMeterError as exc:
        error(str(exc))
    except Exception:
        log.exception("Unexpected error in %s", getattr(action, "__name__", action))
        error("Something went wrong. The details were saved to homemeter.log.")
    if pause_after:
        try:
            pause()
        except Cancelled:
            pass


def run_menu(title: str, options: Sequence[tuple[str, Callable[[], None]]],
             subtitle: str | None = None, exit_label: str = "Back", pause_after: bool = True) -> None:
    while True:
        header(title, subtitle)
        for number, (label, _) in enumerate(options, start=1):
            print(f" {number}. {label}")
        print(f" 0. {exit_label}")
        try:
            picked = ask_int(f"\nType a number (0-{len(options)}) and press Enter", 0, len(options))
        except Cancelled:
            return
        if picked == 0:
            return
        run_action(options[picked - 1][1], pause_after)

