import unittest

from app.errors import AuthError, PermissionDeniedError, ValidationError
from app.models import Role
from app.services.auth_service import AuthService
from app.services.household_service import HouseholdService
from tests.helpers import make_db


class AuthServiceTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()
        self.auth = AuthService(self.db)
        self.admin = self.auth.create_first_admin("admin", "Admin2026")
        self.household = HouseholdService(self.db).create(self.admin, "Mugisha Family", "Gasabo", 5)

    def test_login_works_and_password_is_hashed(self):
        self.assertEqual(self.auth.login("ADMIN", "Admin2026").id, self.admin.id)
        stored = self.db.query_one("SELECT password_hash FROM users WHERE username = 'admin'")["password_hash"]
        self.assertNotIn("Admin2026", stored)

    def test_wrong_password_and_unknown_user_give_same_error(self):
        with self.assertRaisesRegex(AuthError, "Wrong username or password"):
            self.auth.login("admin", "wrong-pass1")
        with self.assertRaisesRegex(AuthError, "Wrong username or password"):
            self.auth.login("nobody", "Admin2026")

    def test_setup_only_once(self):
        self.assertFalse(self.auth.needs_setup())
        with self.assertRaises(ValidationError):
            self.auth.create_first_admin("second", "Second2026")

    def test_weak_passwords_and_duplicate_usernames_are_rejected(self):
        for password in ("short1", "onlyletters", "12345678"):
            with self.assertRaises(ValidationError):
                self.auth.create_user(self.admin, "family", password, Role.HOUSEHOLD, self.household.id)
        self.auth.create_user(self.admin, "family", "Family2026", Role.HOUSEHOLD, self.household.id)
        with self.assertRaises(ValidationError):
            self.auth.create_user(self.admin, "family", "Family2026", Role.HOUSEHOLD, self.household.id)

    def test_household_user_cannot_create_accounts(self):
        family = self.auth.create_user(self.admin, "family", "Family2026", Role.HOUSEHOLD, self.household.id)
        with self.assertRaises(PermissionDeniedError):
            self.auth.create_user(family, "other", "Other2026", Role.ADMIN, None)

    def test_cannot_delete_self_or_last_admin(self):
        with self.assertRaises(ValidationError):
            self.auth.delete_user(self.admin, self.admin.id)

    def test_change_password(self):
        self.auth.change_password(self.admin, "Admin2026", "Newpass2026")
        self.assertEqual(self.auth.login("admin", "Newpass2026").id, self.admin.id)
        with self.assertRaises(AuthError):
            self.auth.change_password(self.admin, "Admin2026", "Other2026")


if __name__ == "__main__":
    unittest.main()
