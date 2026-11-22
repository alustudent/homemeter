from app.database import Database
from app.models import Role, User, new_id, now_iso


def make_db() -> Database:
    db = Database(":memory:")
    db.initialise()
    return db


def make_admin() -> User:
    # Services only check the role, so tests do not need a saved account
    return User(new_id(), "admin", Role.ADMIN, None, now_iso())


def make_household_user(household_id: str, username: str = "family") -> User:
    return User(new_id(), username, Role.HOUSEHOLD, household_id, now_iso())
