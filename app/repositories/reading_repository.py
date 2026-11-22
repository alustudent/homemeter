import sqlite3
from datetime import date

from app.database import Database
from app.models import MeterReading, Utility


def _to_reading(row: sqlite3.Row) -> MeterReading:
    return MeterReading(
        row["id"], row["household_id"], Utility(row["utility"]), row["value"],
        date.fromisoformat(row["read_on"]), row["created_at"],
    )


class ReadingRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, reading: MeterReading) -> None:
        self.db.connection.execute(
            "INSERT INTO readings (id, household_id, utility, value, read_on, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (reading.id, reading.household_id, reading.utility.value, reading.value,
             reading.read_on.isoformat(), reading.created_at),
        )

    def get(self, reading_id: str) -> MeterReading | None:
        row = self.db.query_one("SELECT * FROM readings WHERE id = ?", (reading_id,))
        return _to_reading(row) if row else None

    def list_for(self, household_id: str, utility: Utility | None = None) -> list[MeterReading]:
        """Oldest first, so each reading can be compared with the one before it."""
        if utility is None:
            rows = self.db.query(
                "SELECT * FROM readings WHERE household_id = ? ORDER BY utility, read_on", (household_id,)
            )
        else:
            rows = self.db.query(
                "SELECT * FROM readings WHERE household_id = ? AND utility = ? ORDER BY read_on",
                (household_id, utility.value),
            )
        return [_to_reading(r) for r in rows]

    def update(self, reading: MeterReading) -> None:
        self.db.connection.execute(
            "UPDATE readings SET value = ?, read_on = ? WHERE id = ?",
            (reading.value, reading.read_on.isoformat(), reading.id),
        )

    def delete(self, reading_id: str) -> None:
        self.db.connection.execute("DELETE FROM readings WHERE id = ?", (reading_id,))
