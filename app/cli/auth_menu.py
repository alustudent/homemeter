from app.cli.households_menu import choose_household
from app.cli.prompts import (Cancelled, ask_secret, ask_text, choose, confirm, error, header, print_table,
                                   run_menu, success)
from app.errors import AuthError, ValidationError
from app.models import Role, User
from app.services.auth_service import AuthService
from app.services.household_service import HouseholdService

MAX_LOGIN_ATTEMPTS = 3


def ask_new_password() -> str:
    while True:
        password = ask_secret("New password (8+ characters, letters and numbers)")
        if password == ask_secret("Type it again"):
            return password
        error("The two passwords do not match. Try again.")


def first_run_setup(auth: AuthService) -> None:
    header("FIRST-TIME SETUP", "Create the admin account that manages HomeMeter")
    while True:
        username = ask_text("Admin username")
        try:
            auth.create_first_admin(username, ask_new_password())
            success("Admin account created. You can now log in.")
            return
        except ValidationError as exc:
            error(str(exc))


def login(auth: AuthService) -> User:
    header("LOG IN")
    for attempt in range(1, MAX_LOGIN_ATTEMPTS + 1):
        username = ask_text("Username")
        try:
            user = auth.login(username, ask_secret("Password"))
            success(f"Welcome, {user.username}!")
            return user
        except AuthError as exc:
            error(f"{exc} ({MAX_LOGIN_ATTEMPTS - attempt} attempts left)")
    raise AuthError("Too many failed attempts. Back to the main menu.")


def change_password(actor: User, auth: AuthService) -> None:
    header("CHANGE MY PASSWORD")
    auth.change_password(actor, ask_secret("Current password"), ask_new_password())
    success("Password changed.")


def _choose_user(actor: User, auth: AuthService) -> User:
    users = auth.list_users(actor)
    return users[choose("Choose an account", [f"{u.username} ({u.role})" for u in users])]


def show_users(actor: User, auth: AuthService, households: HouseholdService) -> None:
    header("ALL ACCOUNTS")
    names = {h.id: h.name for h in households.list_all(actor)}
    rows = [(i, u.username, u.role, names.get(u.household_id, "-"), u.created_at[:10])
            for i, u in enumerate(auth.list_users(actor), start=1)]
    print_table(["#", "Username", "Role", "Household", "Created"], rows)


def create_account(actor: User, auth: AuthService, households: HouseholdService, role: Role) -> None:
    header(f"CREATE A {role.upper()} ACCOUNT")
    household_id = choose_household(actor, households).id if role is Role.HOUSEHOLD else None
    while True:
        username = ask_text("Username")
        try:
            user = auth.create_user(actor, username, ask_new_password(), role, household_id)
            break
        except ValidationError as exc:
            error(f"{exc} Please try again, or press Ctrl+C to cancel.")
    success(f"Account '{user.username}' created.")


def reset_password(actor: User, auth: AuthService) -> None:
    header("RESET A PASSWORD")
    user = _choose_user(actor, auth)
    auth.reset_password(actor, user.id, ask_new_password())
    success(f"Password for '{user.username}' was reset.")


def delete_account(actor: User, auth: AuthService) -> None:
    header("DELETE AN ACCOUNT")
    user = _choose_user(actor, auth)
    if not confirm(f"Delete the account '{user.username}'?"):
        raise Cancelled
    auth.delete_user(actor, user.id)
    success(f"Account '{user.username}' deleted.")


def manage_users(actor: User, auth: AuthService, households: HouseholdService) -> None:
    run_menu("MANAGE USER ACCOUNTS", [
        ("List accounts", lambda: show_users(actor, auth, households)),
        ("Create a household account", lambda: create_account(actor, auth, households, Role.HOUSEHOLD)),
        ("Create an admin account", lambda: create_account(actor, auth, households, Role.ADMIN)),
        ("Reset a password", lambda: reset_password(actor, auth)),
        ("Delete an account", lambda: delete_account(actor, auth)),
    ])
