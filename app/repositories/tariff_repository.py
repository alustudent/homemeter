import sqlite3

from app.database import Database
from app.models import TariffBlock, Utility


def _to_block(row: sqlite3.Row) -> TariffBlock:
    return TariffBlock(
        row["id"], Utility(row["utility"]), row["lower_units"], row["upper_units_inclusive"], row["price"]
    )


class TariffRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_for(self, utility: Utility) -> list[TariffBlock]:
        rows = self.db.query(
            "SELECT * FROM tariff_blocks WHERE utility = ? ORDER BY lower_units", (utility.value,)
        )
        return [_to_block(r) for r in rows]

    def get(self, block_id: str) -> TariffBlock | None:
        row = self.db.query_one("SELECT * FROM tariff_blocks WHERE id = ?", (block_id,))
        return _to_block(row) if row else None

    def update_price(self, block_id: str, price: float) -> None:
        self.db.connection.execute("UPDATE tariff_blocks SET price = ? WHERE id = ?", (price, block_id))
