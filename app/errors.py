class HomeMeterError(Exception):
    """Base error whose message is safe to show to the user."""


class ValidationError(HomeMeterError):
    pass


class NotFoundError(HomeMeterError):
    pass


class AuthError(HomeMeterError):
    pass


class PermissionDeniedError(HomeMeterError):
    pass
