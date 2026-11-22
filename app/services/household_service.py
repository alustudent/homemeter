import logging

from app.config import MAX_PEOPLE_PER_HOUSEHOLD, RWANDA_DISTRICTS
from app.database import Database
from app.errors import NotFoundError, ValidationError
from app.models import Household, User, new_id, now_iso
from app.permissions import require_admin, require_household_access
from app.repositories.household_repository import HouseholdRepository

log = logging.getLogger(__name__)


def clean_name(name: str) -> str:
    name = " ".join(name.split())
    if not 2 <= len(name) <= 60:
        raise ValidationError("Household name must be 2 to 60 characters.")
    return name


def clean_district(district: str) -> str:
    match = next((d for d in RWANDA_DISTRICTS if d.lower() == district.strip().lower()), None)
    if match is None:
        raise ValidationError(f"'{district}' is not one of Rwanda's 30 districts.")
    return match


def check_people(people: int) -> int:
    if not 1 <= people <= MAX_PEOPLE_PER_HOUSEHOLD:
        raise ValidationError(f"Number of people must be between 1 and {MAX_PEOPLE_PER_HOUSEHOLD}.")
    return people


class HouseholdService:
    def __init__(self, db: Database):
        self.db = db
        self.repo = HouseholdRepository(db)

    def create(self, actor: User, name: str, district: str, people: int) -> Household:
        require_admin(actor)
        household = Household(new_id(), clean_name(name), clean_district(district), check_people(people), now_iso())
        with self.db.transaction():
            self.repo.add(household)
        log.info("Admin %s created household %s", actor.username, household.id)
        return household

    def get(self, actor: User, household_id: str) -> Household:
        require_household_access(actor, household_id)
        household = self.repo.get(household_id)
        if household is None:
            raise NotFoundError("Household not found.")
        return household

    def list_all(self, actor: User) -> list[Household]:
        require_admin(actor)
        return self.repo.list_all()

    def update(self, actor: User, household_id: str, name: str, district: str, people: int) -> Household:
        require_admin(actor)
        current = self.get(actor, household_id)
        updated = Household(current.id, clean_name(name), clean_district(district), check_people(people), current.created_at)
        with self.db.transaction():
            self.repo.update(updated)
        log.info("Admin %s updated household %s", actor.username, household_id)
        return updated

    def delete(self, actor: User, household_id: str) -> None:
        require_admin(actor)
        self.get(actor, household_id)
        with self.db.transaction():
            self.repo.delete(household_id)
        log.info("Admin %s deleted household %s", actor.username, household_id)
