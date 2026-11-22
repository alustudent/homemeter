import logging
import re

from app.config import MIN_PASSWORD_LENGTH
from app.database import Database
from app.errors import AuthError, NotFoundError, ValidationError
from app.models import Role, User, new_id, now_iso
from app.permissions import require_admin
from app.repositories.household_repository import HouseholdRepository
from app.repositories.user_repository import UserRepository
from app.security import hash_password, verify_password

log = logging.getLogger(__name__)

USERNAME_PATTERN = re.compile(r"^[a-z0-9_]{3,30}$")


def _clean_username(username: str) -> str:
    username = username.strip().lower()
    if not USERNAME_PATTERN.match(username):
        raise ValidationError("Username must be 3 to 30 letters, numbers or underscores.")
    return username


def _check_password(password: str) -> None:
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    if password.isalpha() or password.isdigit():
        raise ValidationError("Password must mix letters and numbers.")


class AuthService:
    def __init__(self, db: Database):
        self.db = db
        self.users = UserRepository(db)
        self.households = HouseholdRepository(db)

    def needs_setup(self) -> bool:
        return self.users.count_admins() == 0

    def create_first_admin(self, username: str, password: str) -> User:
        if not self.needs_setup():
            raise ValidationError("An admin account already exists.")
        return self._create(username, password, Role.ADMIN, None)

    def create_user(self, actor: User, username: str, password: str, role: Role, household_id: str | None) -> User:
        require_admin(actor)
        if role is Role.HOUSEHOLD and (household_id is None or self.households.get(household_id) is None):
            raise NotFoundError("Choose an existing household for this account.")
        user = self._create(username, password, role, household_id if role is Role.HOUSEHOLD else None)
        log.info("Admin %s created %s account %s", actor.username, role, user.username)
        return user

    def _create(self, username: str, password: str, role: Role, household_id: str | None) -> User:
        username = _clean_username(username)
        _check_password(password)
        if self.users.username_taken(username):
            raise ValidationError(f"Username '{username}' is already taken.")
        user = User(new_id(), username, role, household_id, now_iso())
        password_hash, salt = hash_password(password)
        with self.db.transaction():
            self.users.add(user, password_hash, salt)
        return user

    def login(self, username: str, password: str) -> User:
        found = self.users.get_with_credentials(username.strip().lower())
        # Same message either way, so nobody can guess which usernames exist
        if found is None or not verify_password(password, found[1], found[2]):
            log.warning("Failed login for '%s'", username)
            raise AuthError("Wrong username or password.")
        log.info("User %s logged in", found[0].username)
        return found[0]

    def change_password(self, actor: User, old_password: str, new_password: str) -> None:
        found = self.users.get_with_credentials(actor.username)
        if found is None or not verify_password(old_password, found[1], found[2]):
            raise AuthError("Your current password is wrong.")
        self._set_password(actor.id, new_password)
        log.info("User %s changed their password", actor.username)

    def reset_password(self, actor: User, user_id: str, new_password: str) -> None:
        require_admin(actor)
        self._get(user_id)
        self._set_password(user_id, new_password)
        log.info("Admin %s reset the password of %s", actor.username, user_id)

    def _set_password(self, user_id: str, password: str) -> None:
        _check_password(password)
        password_hash, salt = hash_password(password)
        with self.db.transaction():
            self.users.update_password(user_id, password_hash, salt)

    def list_users(self, actor: User) -> list[User]:
        require_admin(actor)
        return self.users.list_all()

    def delete_user(self, actor: User, user_id: str) -> None:
        require_admin(actor)
        user = self._get(user_id)
        if user.id == actor.id:
            raise ValidationError("You cannot delete your own account while logged in.")
        if user.is_admin and self.users.count_admins() == 1:
            raise ValidationError("You cannot delete the last admin account.")
        with self.db.transaction():
            self.users.delete(user_id)
        log.info("Admin %s deleted account %s", actor.username, user.username)

    def _get(self, user_id: str) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise NotFoundError("Account not found.")
        return user
