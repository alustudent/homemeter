from app.errors import PermissionDeniedError
from app.models import User


def require_admin(actor: User) -> None:
    if not actor.is_admin:
        raise PermissionDeniedError("Only an admin can do that.")


def require_household_access(actor: User, household_id: str) -> None:
    """Admins can reach every household; a household account only its own."""
    if not actor.is_admin and actor.household_id != household_id:
        raise PermissionDeniedError("You can only access your own household.")
