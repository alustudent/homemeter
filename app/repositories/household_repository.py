import sqlite3

from app.database import Database
from app.models import Household


def _to_household(row: sqlite3.Row) -> Household:
    return Household(row["id"], row["name"], row["district"], row["people"], row["created_at"])


class HouseholdRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, household: Household) -> None:
        self.db.connection.execute(
            "INSERT INTO households (id, name, district, people, created_at) VALUES (?, ?, ?, ?, ?)",
            (household.id, household.name, household.district, household.people, household.created_at),
        )

    def get(self, household_id: str) -> Household | None:
        row = self.db.query_one("SELECT * FROM households WHERE id = ?", (household_id,))
        return _to_household(row) if row else None

    def list_all(self) -> list[Household]:
        return [_to_household(r) for r in self.db.query("SELECT * FROM households ORDER BY name")]

    def update(self, household: Household) -> None:
        self.db.connection.execute(
            "UPDATE households SET name = ?, district = ?, people = ? WHERE id = ?",
            (household.name, household.district, household.people, household.id),
        )

    def delete(self, household_id: str) -> None:
        # Readings and household accounts go with it (ON DELETE CASCADE)
        self.db.connection.execute("DELETE FROM households WHERE id = ?", (household_id,))
