import unittest

from app.errors import PermissionDeniedError, ValidationError
from app.services.household_service import HouseholdService
from tests.helpers import make_admin, make_db, make_household_user


class HouseholdServiceTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        self.admin = make_admin()
        self.service = HouseholdService(self.db)

    def test_create_cleans_input(self):
        household = self.service.create(self.admin, "  Mugisha   Family ", "gasabo", 5)
        self.assertEqual((household.name, household.district), ("Mugisha Family", "Gasabo"))

    def test_rejects_unknown_district_and_bad_people(self):
        with self.assertRaises(ValidationError):
            self.service.create(self.admin, "Mugisha Family", "Nairobi", 5)
        with self.assertRaises(ValidationError):
            self.service.create(self.admin, "Mugisha Family", "Gasabo", 0)

    def test_update_and_delete(self):
        household = self.service.create(self.admin, "Mugisha Family", "Gasabo", 5)
        self.service.update(self.admin, household.id, "Mugisha Family", "Kicukiro", 6)
        self.assertEqual(self.service.get(self.admin, household.id).district, "Kicukiro")
        self.service.delete(self.admin, household.id)
        self.assertEqual(self.service.list_all(self.admin), [])

    def test_household_user_cannot_manage_households(self):
        household = self.service.create(self.admin, "Mugisha Family", "Gasabo", 5)
        family = make_household_user(household.id)
        with self.assertRaises(PermissionDeniedError):
            self.service.create(family, "Other Family", "Gasabo", 2)


if __name__ == "__main__":
    unittest.main()
