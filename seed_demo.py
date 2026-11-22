"""Fill an empty database with demo accounts and five months of readings for the presentation."""
import logging
import sys
from datetime import date

from app.config import DB_PATH
from app.database import Database
from app.models import Role, Utility
from app.services.auth_service import AuthService
from app.services.household_service import HouseholdService
from app.services.reading_service import ReadingService

DEMO_ADMIN = ("admin", "Admin2026")
DEMO_HOUSEHOLDS = [
    # name, district, people, username, password, electricity readings, water readings
    ("Mugisha Family", "Gasabo", 5, "mugisha", "Mugisha2026",
     [1200, 1238, 1275, 1316, 1355, 1402], [310, 322, 333.5, 345, 357, 366]),
    ("Uwase Family", "Kicukiro", 3, "uwase", "Uwase2026",
     [860, 878, 895, 913, 930, 941], [150, 157, 163.5, 170, 176, 180]),
]
READING_DATES = [date(2026, 6, 30), date(2026, 7, 31), date(2026, 8, 31),
                 date(2026, 9, 30), date(2026, 10, 31), date(2026, 11, 20)]


def seed(db: Database) -> None:
    auth, households, readings = AuthService(db), HouseholdService(db), ReadingService(db)
    if not auth.needs_setup():
        sys.exit("The database already has accounts. Delete homemeter.db first to reseed it.")
    admin = auth.create_first_admin(*DEMO_ADMIN)
    for name, district, people, username, password, power, water in DEMO_HOUSEHOLDS:
        household = households.create(admin, name, district, people)
        auth.create_user(admin, username, password, Role.HOUSEHOLD, household.id)
        for utility, values in ((Utility.ELECTRICITY, power), (Utility.WATER, water)):
            for read_on, value in zip(READING_DATES, values):
                readings.record(admin, household.id, utility, value, read_on, today=date(2026, 11, 30))
        print(f"Added {name}: log in as {username} / {password}")
    print(f"Admin: log in as {DEMO_ADMIN[0]} / {DEMO_ADMIN[1]}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    database = Database(DB_PATH)
    database.initialise()
    try:
        seed(database)
    finally:
        database.close()
