import unittest
from datetime import date

from app.errors import PermissionDeniedError, ValidationError
from app.models import Utility
from app.services.household_service import HouseholdService
from app.services.reading_service import ReadingService
from tests.helpers import make_admin, make_db, make_household_user

TODAY = date(2026, 11, 22)
POWER = Utility.ELECTRICITY


class ReadingServiceTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        admin = make_admin()
        households = HouseholdService(self.db)
        self.home = households.create(admin, "Mugisha Family", "Gasabo", 5)
        other = households.create(admin, "Uwase Family", "Kicukiro", 3)
        self.family = make_household_user(self.home.id)
        self.neighbour = make_household_user(other.id, "neighbour")
        self.service = ReadingService(self.db)

    def record(self, value, day, utility=POWER):
        return self.service.record(self.family, self.home.id, utility, value, day, today=TODAY)

    def test_record_returns_usage_since_previous(self):
        _, first = self.record(1200, date(2026, 10, 1))
        _, used = self.record(1232.5, date(2026, 11, 1))
        self.assertIsNone(first)
        self.assertEqual(used, 32.5)

    def test_rejects_bad_values_and_dates(self):
        for value, day in ((-1, date(2026, 11, 1)), (float("nan"), date(2026, 11, 1)),
                           (99_999_999, date(2026, 11, 1)), (10, date(2026, 12, 1))):
            with self.assertRaises(ValidationError):
                self.record(value, day)

    def test_meter_cannot_go_down_or_repeat_a_date(self):
        self.record(1200, date(2026, 10, 1))
        self.record(1300, date(2026, 11, 1))
        with self.assertRaisesRegex(ValidationError, "at least 1300"):
            self.record(1250, date(2026, 11, 10))
        with self.assertRaisesRegex(ValidationError, "at most 1300"):
            self.record(1350, date(2026, 10, 15))
        with self.assertRaisesRegex(ValidationError, "already"):
            self.record(1400, date(2026, 11, 1))

    def test_update_keeps_order_and_delete_works(self):
        first, _ = self.record(1200, date(2026, 10, 1))
        self.record(1300, date(2026, 11, 1))
        self.assertEqual(self.service.update(self.family, first.id, 1210, first.read_on, TODAY).value, 1210)
        with self.assertRaises(ValidationError):
            self.service.update(self.family, first.id, 1310, first.read_on, TODAY)
        self.service.delete(self.family, first.id)
        self.assertEqual(len(self.service.list_for(self.family, self.home.id)), 1)

    def test_usage_is_counted_per_month(self):
        self.record(1200, date(2026, 9, 30))
        self.record(1240, date(2026, 10, 31))
        self.record(1250, date(2026, 11, 10))
        self.record(1262, date(2026, 11, 20))
        usage = self.service.usage_by_month(self.family, self.home.id, POWER)
        self.assertEqual(usage, {"2026-10": 40.0, "2026-11": 22.0})

    def test_households_cannot_see_each_other(self):
        reading, _ = self.record(1200, date(2026, 10, 1))
        with self.assertRaises(PermissionDeniedError):
            self.service.list_for(self.neighbour, self.home.id)
        with self.assertRaises(PermissionDeniedError):
            self.service.delete(self.neighbour, reading.id)


if __name__ == "__main__":
    unittest.main()
