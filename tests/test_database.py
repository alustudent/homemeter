import sqlite3
import unittest

from tests.helpers import make_db


class DatabaseTest(unittest.TestCase):
    def setUp(self):
        self.db = make_db()

    def test_creates_all_tables(self):
        names = {r["name"] for r in self.db.query("SELECT name FROM sqlite_master WHERE type = 'table'")}
        self.assertTrue({"households", "users", "readings", "tariff_blocks"} <= names)

    def test_seeds_default_tariffs_once(self):
        self.db.initialise()
        self.assertEqual(self.db.query_one("SELECT COUNT(*) AS n FROM tariff_blocks")["n"], 7)

    def test_foreign_keys_are_enforced(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.transaction() as conn:
                conn.execute("INSERT INTO readings VALUES ('r1', 'missing', 'water', 1, '2026-01-01', 'now')")

    def test_failed_transaction_rolls_back(self):
        with self.assertRaises(sqlite3.IntegrityError):
            with self.db.transaction() as conn:
                conn.execute("INSERT INTO households VALUES ('h1', 'A', 'Gasabo', 2, 'now')")
                conn.execute("INSERT INTO households VALUES ('h2', 'B', 'Gasabo', 0, 'now')")
        self.assertIsNone(self.db.query_one("SELECT * FROM households WHERE id = 'h1'"))


if __name__ == "__main__":
    unittest.main()
