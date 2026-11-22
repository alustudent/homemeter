import logging
import math

from app.database import Database
from app.errors import NotFoundError, ValidationError
from app.models import TariffBlock, User, Utility
from app.permissions import require_admin
from app.repositories.tariff_repository import TariffRepository

log = logging.getLogger(__name__)


def cost_for(units: float, blocks: list[TariffBlock]) -> float:
    """Block pricing: each unit is charged at the price of the block it falls in."""
    total = 0.0
    for block in blocks:
        upper = block.upper_units_inclusive if block.upper_units_inclusive is not None else math.inf
        total += max(0.0, min(units, upper) - block.lower_units) * block.price
    return round(total, 2)


class TariffService:
    def __init__(self, db: Database):
        self.db = db
        self.repo = TariffRepository(db)

    def list_for(self, utility: Utility) -> list[TariffBlock]:
        return self.repo.list_for(utility)

    def cost(self, utility: Utility, units: float) -> float:
        return cost_for(units, self.repo.list_for(utility))

    def current_block(self, utility: Utility, units: float) -> TariffBlock:
        blocks = self.repo.list_for(utility)
        return next(
            (b for b in blocks if b.upper_units_inclusive is None or units <= b.upper_units_inclusive),
            blocks[-1],
        )

    def next_block(self, utility: Utility, units: float) -> TariffBlock | None:
        blocks = self.repo.list_for(utility)
        current = self.current_block(utility, units)
        later = [b for b in blocks if b.lower_units > current.lower_units]
        return later[0] if later else None

    def update_price(self, actor: User, block_id: str, price: float) -> TariffBlock:
        require_admin(actor)
        if not math.isfinite(price) or not 0 <= price <= 100_000:
            raise ValidationError("Price must be between 0 and 100,000 RWF per unit.")
        block = self.repo.get(block_id)
        if block is None:
            raise NotFoundError("Tariff block not found.")
        with self.db.transaction():
            self.repo.update_price(block_id, round(price, 2))
        log.info("Admin %s set %s block %s to %.2f RWF", actor.username, block.utility, block.label, price)
        return self.repo.get(block_id)
