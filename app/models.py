import uuid
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum


def new_id() -> str:
    return str(uuid.uuid4())


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Role(StrEnum):
    ADMIN = "admin"
    HOUSEHOLD = "household"


class Utility(StrEnum):
    ELECTRICITY = "electricity"
    WATER = "water"

    @property
    def unit(self) -> str:
        return "kWh" if self is Utility.ELECTRICITY else "m3"

    @property
    def label(self) -> str:
        return self.value.capitalize()


@dataclass(frozen=True)
class Household:
    id: str
    name: str
    district: str
    people: int
    created_at: str


@dataclass(frozen=True)
class User:
    id: str
    username: str
    role: Role
    household_id: str | None
    created_at: str

    @property
    def is_admin(self) -> bool:
        return self.role is Role.ADMIN


@dataclass(frozen=True)
class MeterReading:
    id: str
    household_id: str
    utility: Utility
    value: float
    read_on: date
    created_at: str


@dataclass(frozen=True)
class TariffBlock:
    id: str
    utility: Utility
    lower_units: float
    upper_units_inclusive: float | None
    price: float

    @property
    def label(self) -> str:
        if self.upper_units_inclusive is None:
            return f"above {self.lower_units:g}"
        return f"{self.lower_units:g}-{self.upper_units_inclusive:g}"


@dataclass(frozen=True)
class UsageLine:
    utility: Utility
    units: float
    cost: float
    previous_units: float | None

    @property
    def change(self) -> float | None:
        if not self.previous_units:
            return None
        return (self.units - self.previous_units) / self.previous_units
