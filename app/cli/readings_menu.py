from app.cli.prompts import (Cancelled, ask_date, ask_float, choose, confirm, error, header, print_table,
                                   run_menu, success)
from app.errors import ValidationError
from app.models import MeterReading, User, Utility
from app.services.reading_service import ReadingService


def choose_utility() -> Utility:
    utilities = list(Utility)
    return utilities[choose("Choose utility", [f"{u.label} ({u.unit})" for u in utilities])]


def record_reading(actor: User, household_id: str, readings: ReadingService) -> None:
    header("RECORD A METER READING")
    utility = choose_utility()
    while True:
        value = ask_float(f"Meter reading in {utility.unit}")
        read_on = ask_date("Reading date")
        try:
            reading, used = readings.record(actor, household_id, utility, value, read_on)
            break
        except ValidationError as exc:
            error(f"{exc} Please try again, or press Ctrl+C to cancel.")
    success(f"Saved {utility} reading of {reading.value:g} {utility.unit} on {reading.read_on}.")
    if used is None:
        print("This is the first reading, so usage starts from here.")
    else:
        print(f"You used {used:g} {utility.unit} since your previous reading.")


def _rows(items: list[MeterReading]) -> list[tuple]:
    rows, previous = [], {}
    for number, r in enumerate(items, start=1):
        before = previous.get(r.utility)
        used = f"{r.value - before.value:g}" if before else "-"
        rows.append((number, r.utility.label, r.read_on, f"{r.value:g} {r.utility.unit}", used))
        previous[r.utility] = r
    return rows


def show_readings(actor: User, household_id: str, readings: ReadingService) -> None:
    header("MY READINGS")
    print_table(["#", "Utility", "Date", "Meter", "Used since previous"], _rows(readings.list_for(actor, household_id)))


def _choose_reading(actor: User, household_id: str, readings: ReadingService) -> MeterReading:
    utility = choose_utility()
    items = readings.list_for(actor, household_id, utility)
    return items[choose("Choose a reading", [f"{r.read_on}: {r.value:g} {utility.unit}" for r in items])]


def edit_reading(actor: User, household_id: str, readings: ReadingService) -> None:
    header("EDIT A READING")
    current = _choose_reading(actor, household_id, readings)
    print("Press Enter to keep the value in [brackets].")
    while True:
        value = ask_float(f"Meter reading in {current.utility.unit}", current.value)
        read_on = ask_date("Reading date", current.read_on)
        try:
            updated = readings.update(actor, current.id, value, read_on)
            break
        except ValidationError as exc:
            error(f"{exc} Please try again, or press Ctrl+C to cancel.")
    success(f"Reading updated to {updated.value:g} {updated.utility.unit} on {updated.read_on}.")


def delete_reading(actor: User, household_id: str, readings: ReadingService) -> None:
    header("DELETE A READING")
    reading = _choose_reading(actor, household_id, readings)
    if not confirm(f"Delete the {reading.utility} reading of {reading.read_on}?"):
        raise Cancelled
    readings.delete(actor, reading.id)
    success("Reading deleted.")


def manage_readings(actor: User, household_id: str, readings: ReadingService) -> None:
    run_menu("MANAGE MY READINGS", [
        ("View all readings", lambda: show_readings(actor, household_id, readings)),
        ("Edit a reading", lambda: edit_reading(actor, household_id, readings)),
        ("Delete a reading", lambda: delete_reading(actor, household_id, readings)),
    ])
