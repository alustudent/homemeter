import logging
import math
from collections import defaultdict
from datetime import date

from app.config import MAX_METER_VALUE
from app.database import Database
from app.errors import NotFoundError, ValidationError
from app.models import MeterReading, User, Utility, new_id, now_iso
from app.permissions import require_household_access
from app.repositories.reading_repository import ReadingRepository

log = logging.getLogger(__name__)

EARLIEST_DATE = date(2000, 1, 1)


def month_key(day: date) -> str:
    return f"{day.year:04d}-{day.month:02d}"


def _check_value(value: float) -> float:
    if not math.isfinite(value) or value < 0:
        raise ValidationError("Meter reading must be a number of 0 or more.")
    if value > MAX_METER_VALUE:
        raise ValidationError(f"Meter reading looks too large (over {MAX_METER_VALUE:,}). Check for an extra digit.")
    return round(value, 3)


def _check_date(read_on: date, today: date) -> date:
    if read_on > today:
        raise ValidationError("Reading date cannot be in the future.")
    if read_on < EARLIEST_DATE:
        raise ValidationError(f"Reading date cannot be before {EARLIEST_DATE}.")
    return read_on


def _check_order(others: list[MeterReading], utility: Utility, value: float, read_on: date) -> MeterReading | None:
    """Meters only count up, so a reading must sit between its neighbours. Returns the previous one."""
    if any(r.read_on == read_on for r in others):
        raise ValidationError(f"There is already a {utility} reading on {read_on}. Edit that one instead.")
    before = [r for r in others if r.read_on < read_on]
    after = [r for r in others if r.read_on > read_on]
    if before and value < before[-1].value:
        raise ValidationError(
            f"Reading must be at least {before[-1].value:g} {utility.unit} (the reading on {before[-1].read_on})."
        )
    if after and value > after[0].value:
        raise ValidationError(
            f"Reading must be at most {after[0].value:g} {utility.unit} (the reading on {after[0].read_on})."
        )
    return before[-1] if before else None


class ReadingService:
    def __init__(self, db: Database):
        self.db = db
        self.repo = ReadingRepository(db)

    def record(self, actor: User, household_id: str, utility: Utility, value: float,
               read_on: date, today: date | None = None) -> tuple[MeterReading, float | None]:
        """Save a reading and return it with the units used since the previous reading."""
        require_household_access(actor, household_id)
        value = _check_value(value)
        read_on = _check_date(read_on, today or date.today())
        previous = _check_order(self.repo.list_for(household_id, utility), utility, value, read_on)
        reading = MeterReading(new_id(), household_id, utility, value, read_on, now_iso())
        with self.db.transaction():
            self.repo.add(reading)
        log.info("%s recorded %s %.3f on %s for %s", actor.username, utility, value, read_on, household_id)
        return reading, (round(value - previous.value, 3) if previous else None)

    def list_for(self, actor: User, household_id: str, utility: Utility | None = None) -> list[MeterReading]:
        require_household_access(actor, household_id)
        return self.repo.list_for(household_id, utility)

    def update(self, actor: User, reading_id: str, value: float, read_on: date,
               today: date | None = None) -> MeterReading:
        current = self._get(actor, reading_id)
        value = _check_value(value)
        read_on = _check_date(read_on, today or date.today())
        others = [r for r in self.repo.list_for(current.household_id, current.utility) if r.id != reading_id]
        _check_order(others, current.utility, value, read_on)
        updated = MeterReading(current.id, current.household_id, current.utility, value, read_on, current.created_at)
        with self.db.transaction():
            self.repo.update(updated)
        log.info("%s updated reading %s", actor.username, reading_id)
        return updated

    def delete(self, actor: User, reading_id: str) -> None:
        self._get(actor, reading_id)
        with self.db.transaction():
            self.repo.delete(reading_id)
        log.info("%s deleted reading %s", actor.username, reading_id)

    def usage_by_month(self, actor: User, household_id: str, utility: Utility) -> dict[str, float]:
        """Units used per month: each reading minus the one before, counted in the later reading's month."""
        readings = self.list_for(actor, household_id, utility)
        usage: dict[str, float] = defaultdict(float)
        for previous, current in zip(readings, readings[1:]):
            usage[month_key(current.read_on)] += current.value - previous.value
        return {month: round(units, 3) for month, units in usage.items()}

    def _get(self, actor: User, reading_id: str) -> MeterReading:
        reading = self.repo.get(reading_id)
        if reading is None:
            raise NotFoundError("Reading not found.")
        require_household_access(actor, reading.household_id)
        return reading
