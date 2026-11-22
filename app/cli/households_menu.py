from app.cli.prompts import Cancelled, ask_int, ask_text, choose, confirm, header, print_table, run_menu, success
from app.config import MAX_PEOPLE_PER_HOUSEHOLD
from app.models import Household, User
from app.services.household_service import HouseholdService, clean_district, clean_name


def choose_household(actor: User, households: HouseholdService) -> Household:
    items = households.list_all(actor)
    index = choose("Choose a household", [f"{h.name} ({h.district}, {h.people} people)" for h in items])
    return items[index]


def show_households(actor: User, households: HouseholdService) -> None:
    header("ALL HOUSEHOLDS")
    rows = [(i, h.name, h.district, h.people, h.created_at[:10])
            for i, h in enumerate(households.list_all(actor), start=1)]
    print_table(["#", "Name", "District", "People", "Added on"], rows)


def _ask_details(current: Household | None = None) -> tuple[str, str, int]:
    name = ask_text("Family name (e.g. Mugisha Family)", clean_name, current.name if current else None)
    district = ask_text("District (e.g. Gasabo)", clean_district, current.district if current else None)
    people = ask_int(f"Number of people (1-{MAX_PEOPLE_PER_HOUSEHOLD})", 1, MAX_PEOPLE_PER_HOUSEHOLD,
                     current.people if current else None)
    return name, district, people


def add_household(actor: User, households: HouseholdService) -> None:
    header("ADD A HOUSEHOLD")
    household = households.create(actor, *_ask_details())
    success(f"Household '{household.name}' saved.")


def edit_household(actor: User, households: HouseholdService) -> None:
    header("EDIT A HOUSEHOLD")
    current = choose_household(actor, households)
    print("Press Enter to keep the value in [brackets].")
    updated = households.update(actor, current.id, *_ask_details(current))
    success(f"Household '{updated.name}' updated.")


def delete_household(actor: User, households: HouseholdService) -> None:
    header("DELETE A HOUSEHOLD")
    household = choose_household(actor, households)
    if not confirm(f"Delete '{household.name}' with all its readings and accounts?"):
        raise Cancelled
    households.delete(actor, household.id)
    success(f"Household '{household.name}' deleted.")


def manage_households(actor: User, households: HouseholdService) -> None:
    run_menu("MANAGE HOUSEHOLDS", [
        ("List households", lambda: show_households(actor, households)),
        ("Add a household", lambda: add_household(actor, households)),
        ("Edit a household", lambda: edit_household(actor, households)),
        ("Delete a household", lambda: delete_household(actor, households)),
    ])
