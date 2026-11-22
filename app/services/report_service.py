import re

from app.config import HISTORY_MONTHS
from app.errors import ValidationError
from app.models import Household, UsageLine, User, Utility
from app.permissions import require_admin
from app.services.household_service import HouseholdService
from app.services.reading_service import ReadingService
from app.services.tariff_service import TariffService

MONTH_PATTERN = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def check_month(month: str) -> str:
    month = month.strip()
    if not MONTH_PATTERN.match(month):
        raise ValidationError("Month must look like 2026-11 (YYYY-MM).")
    return month


def previous_month(month: str) -> str:
    year, number = int(month[:4]), int(month[5:])
    return f"{year - 1}-12" if number == 1 else f"{year}-{number - 1:02d}"


def months_ending(month: str, count: int) -> list[str]:
    """The `count` months up to and including `month`, oldest first."""
    months = [month]
    while len(months) < count:
        months.insert(0, previous_month(months[0]))
    return months


class ReportService:
    def __init__(self, households: HouseholdService, readings: ReadingService, tariffs: TariffService):
        self.households = households
        self.readings = readings
        self.tariffs = tariffs

    def monthly(self, actor: User, household_id: str, month: str) -> list[UsageLine]:
        month = check_month(month)
        self.households.get(actor, household_id)
        lines = []
        for utility in Utility:
            usage = self.readings.usage_by_month(actor, household_id, utility)
            units = usage.get(month, 0.0)
            lines.append(UsageLine(utility, units, self.tariffs.cost(utility, units), usage.get(previous_month(month))))
        return lines

    def history(self, actor: User, household_id: str, month: str,
                count: int = HISTORY_MONTHS) -> list[tuple[str, list[UsageLine]]]:
        month = check_month(month)
        self.households.get(actor, household_id)
        usage = {u: self.readings.usage_by_month(actor, household_id, u) for u in Utility}
        rows = []
        for m in months_ending(month, count):
            lines = [
                UsageLine(u, usage[u].get(m, 0.0), self.tariffs.cost(u, usage[u].get(m, 0.0)),
                          usage[u].get(previous_month(m)))
                for u in Utility
            ]
            rows.append((m, lines))
        return rows

    def overview(self, actor: User, month: str) -> list[tuple[Household, list[UsageLine]]]:
        require_admin(actor)
        month = check_month(month)
        return [(h, self.monthly(actor, h.id, month)) for h in self.households.list_all(actor)]
