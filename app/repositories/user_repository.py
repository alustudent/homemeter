import sqlite3

from app.database import Database
from app.models import Role, User


def _to_user(row: sqlite3.Row) -> User:
    return User(row["id"], row["username"], Role(row["role"]), row["household_id"], row["created_at"])


class UserRepository:
    def __init__(self, db: Database):
        self.db = db

    def add(self, user: User, password_hash: str, salt: str) -> None:
        self.db.connection.execute(
            "INSERT INTO users (id, username, password_hash, salt, role, household_id, created_at)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user.id, user.username, password_hash, salt, user.role.value, user.household_id, user.created_at),
        )

    def get(self, user_id: str) -> User | None:
        row = self.db.query_one("SELECT * FROM users WHERE id = ?", (user_id,))
        return _to_user(row) if row else None

    def get_with_credentials(self, username: str) -> tuple[User, str, str] | None:
        row = self.db.query_one("SELECT * FROM users WHERE username = ?", (username,))
        return (_to_user(row), row["password_hash"], row["salt"]) if row else None

    def username_taken(self, username: str) -> bool:
        return self.db.query_one("SELECT 1 FROM users WHERE username = ?", (username,)) is not None

    def list_all(self) -> list[User]:
        return [_to_user(r) for r in self.db.query("SELECT * FROM users ORDER BY role, username")]

    def count_admins(self) -> int:
        return self.db.query_one("SELECT COUNT(*) AS n FROM users WHERE role = 'admin'")["n"]

    def update_password(self, user_id: str, password_hash: str, salt: str) -> None:
        self.db.connection.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE id = ?", (password_hash, salt, user_id)
        )

    def delete(self, user_id: str) -> None:
        self.db.connection.execute("DELETE FROM users WHERE id = ?", (user_id,))
