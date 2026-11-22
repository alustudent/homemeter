import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from app.config import DEFAULT_TARIFFS
from app.models import new_id

log = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS households (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    district    TEXT NOT NULL,
    people      INTEGER NOT NULL CHECK (people > 0),
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id             TEXT PRIMARY KEY,
    username       TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash  TEXT NOT NULL,
    salt           TEXT NOT NULL,
    role           TEXT NOT NULL CHECK (role IN ('admin', 'household')),
    household_id   TEXT REFERENCES households (id) ON DELETE CASCADE,
    created_at     TEXT NOT NULL,
    CHECK ((role = 'admin' AND household_id IS NULL)
        OR (role = 'household' AND household_id IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS readings (
    id            TEXT PRIMARY KEY,
    household_id  TEXT NOT NULL REFERENCES households (id) ON DELETE CASCADE,
    utility       TEXT NOT NULL CHECK (utility IN ('electricity', 'water')),
    value         REAL NOT NULL CHECK (value >= 0),
    read_on       TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    UNIQUE (household_id, utility, read_on)
);

CREATE INDEX IF NOT EXISTS idx_readings_household
    ON readings (household_id, utility, read_on);

CREATE TABLE IF NOT EXISTS tariff_blocks (
    id                     TEXT PRIMARY KEY,
    utility                TEXT NOT NULL CHECK (utility IN ('electricity', 'water')),
    lower_units            REAL NOT NULL CHECK (lower_units >= 0),
    upper_units_inclusive  REAL CHECK (upper_units_inclusive > lower_units),
    price                  REAL NOT NULL CHECK (price >= 0),
    UNIQUE (utility, lower_units)
);
"""


class Database:
    """Owns the SQLite connection. Every write goes through transaction()."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")

    def initialise(self) -> None:
        self.connection.executescript(SCHEMA)
        if self.query_one("SELECT COUNT(*) AS n FROM tariff_blocks")["n"] == 0:
            with self.transaction() as conn:
                conn.executemany(
                    "INSERT INTO tariff_blocks (id, utility, lower_units, upper_units_inclusive, price)"
                    " VALUES (?, ?, ?, ?, ?)",
                    [(new_id(), *row) for row in DEFAULT_TARIFFS],
                )
            log.info("Seeded %d default tariff blocks", len(DEFAULT_TARIFFS))
        log.info("Database ready at %s", self.path)

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Commit when the block succeeds, roll back if it raises."""
        try:
            yield self.connection
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            log.exception("Transaction rolled back")
            raise

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.connection.execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        return self.connection.execute(sql, params).fetchone()

    def close(self) -> None:
        self.connection.close()
