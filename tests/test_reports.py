import unittest
from datetime import date

from app.errors import PermissionDeniedError, ValidationError
from app.models import Utility
from app.services.alert_service import AlertService
from app.services.household_service import HouseholdService
from app.services.reading_service import ReadingService
from app.services.report_service import ReportService, months_ending, previous_month
from app.services.tariff_service import TariffService
from tests.helpers import make_admin, make_db, make_household_user

POWER, WATER = Utility.ELECTRICITY, Utility.WATER


class TariffTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        self.tariffs = TariffService(self.db)

    def test_block_pricing_matches_reg_tariff(self):
        self.assertEqual(self.tariffs.cost(POWER, 20), 20 * 89)
        self.assertEqual(self.tariffs.cost(POWER, 32.5), 20 * 89 + 12.5 * 310)
        self.assertEqual(self.tariffs.cost(POWER, 60), 20 * 89 + 30 * 310 + 10 * 369)

    def test_only_admin_changes_prices(self):
        admin = make_admin()
        household = HouseholdService(self.db).create(admin, "Mugisha Family", "Gasabo", 5)
        family = make_household_user(household.id)
        block = self.tariffs.list_for(WATER)[0]
        self.assertEqual(self.tariffs.update_price(admin, block.id, 400).price, 400)
        with self.assertRaises(PermissionDeniedError):
            self.tariffs.update_price(family, block.id, 1)
        with self.assertRaises(ValidationError):
            self.tariffs.update_price(admin, block.id, -5)


class MonthHelpersTest(unittest.TestCase):
    def test_previous_month_and_ranges(self):
        self.assertEqual(previous_month("2026-01"), "2025-12")
        self.assertEqual(months_ending("2026-02", 3), ["2025-12", "2026-01", "2026-02"])


class ReportAndAlertTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        self.admin = make_admin()
        households = HouseholdService(self.db)
        self.home = households.create(self.admin, "Mugisha Family", "Gasabo", 5)
        readings = ReadingService(self.db)
        tariffs = TariffService(self.db)
        self.reports = ReportService(households, readings, tariffs)
        self.alerts = AlertService(readings, tariffs)
        days = [date(2026, 7, 31), date(2026, 8, 31), date(2026, 9, 30), date(2026, 10, 31), date(2026, 11, 20)]
        for day, value in zip(days, [1000, 1038, 1075, 1114, 1161]):
            readings.record(self.admin, self.home.id, POWER, value, day, today=date(2026, 11, 22))

    def test_monthly_report(self):
        power, water = self.reports.monthly(self.admin, self.home.id, "2026-11")
        self.assertEqual((power.units, power.previous_units), (47, 39))
        self.assertEqual(power.cost, 20 * 89 + 27 * 310)
        self.assertEqual(water.units, 0)

    def test_overview_is_admin_only(self):
        family = make_household_user(self.home.id)
        with self.assertRaises(PermissionDeniedError):
            self.reports.overview(family, "2026-11")

    def test_alerts_flag_spike_and_next_block(self):
        messages = [a.message for a in self.alerts.check(self.admin, self.home.id, date(2026, 11, 22))]
        self.assertTrue(any("above your 3-month average" in m for m in messages))
        self.assertTrue(any("Only 3 kWh left" in m for m in messages))
        self.assertTrue(any("No water usage" in m for m in messages))

    def test_tips(self):
        self.assertEqual(len(self.alerts.tips(WATER, 2, date(2026, 11, 22))), 2)


if __name__ == "__main__":
    unittest.main()
