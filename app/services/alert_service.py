from dataclasses import dataclass
from datetime import date

from app.config import BLOCK_WARNING_UNITS, SAVING_TIPS, SPIKE_HISTORY_MONTHS, SPIKE_THRESHOLD
from app.models import User, Utility
from app.services.reading_service import ReadingService, month_key
from app.services.report_service import months_ending, previous_month
from app.services.tariff_service import TariffService


@dataclass(frozen=True)
class Alert:
    utility: Utility
    message: str


class AlertService:
    def __init__(self, readings: ReadingService, tariffs: TariffService):
        self.readings = readings
        self.tariffs = tariffs

    def check(self, actor: User, household_id: str, today: date | None = None) -> list[Alert]:
        month = month_key(today or date.today())
        alerts = []
        for utility in Utility:
            usage = self.readings.usage_by_month(actor, household_id, utility)
            if month not in usage:
                alerts.append(Alert(utility, f"No {utility} usage recorded yet this month. Add a reading."))
                continue
            alerts.extend(self._spike(utility, usage, month))
            alerts.extend(self._blocks(utility, usage[month]))
        return alerts

    def _spike(self, utility: Utility, usage: dict[str, float], month: str) -> list[Alert]:
        past = [usage[m] for m in months_ending(previous_month(month), SPIKE_HISTORY_MONTHS) if m in usage]
        if not past:
            return []
        average = sum(past) / len(past)
        units = usage[month]
        if average <= 0 or units <= average * (1 + SPIKE_THRESHOLD):
            return []
        rise = (units - average) / average
        return [Alert(utility, f"{utility.label} use this month is {units:g} {utility.unit}, "
                               f"{rise:.0%} above your {len(past)}-month average of {average:.1f}.")]

    def _blocks(self, utility: Utility, units: float) -> list[Alert]:
        alerts = []
        current = self.tariffs.current_block(utility, units)
        first = self.tariffs.list_for(utility)[0]
        if current.lower_units > first.lower_units:
            alerts.append(Alert(utility, f"You are in the {current.label} {utility.unit} block: each extra "
                                         f"{utility.unit} costs {current.price:g} RWF (first block: {first.price:g} RWF)."))
        upcoming = self.tariffs.next_block(utility, units)
        if upcoming is not None and upcoming.lower_units - units <= BLOCK_WARNING_UNITS[utility.value]:
            gap = upcoming.lower_units - units
            alerts.append(Alert(utility, f"Only {gap:g} {utility.unit} left before the price rises from "
                                         f"{current.price:g} to {upcoming.price:g} RWF per {utility.unit}."))
        return alerts

    def tips(self, utility: Utility, count: int = 2, today: date | None = None) -> list[str]:
        """A couple of tips that change from day to day."""
        tips = SAVING_TIPS[utility.value]
        start = (today or date.today()).toordinal() % len(tips)
        return [tips[(start + i) % len(tips)] for i in range(min(count, len(tips)))]
