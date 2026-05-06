"""Central place for enums shared across the app."""

from enum import Enum


class ResponseEnum(str, Enum):
    """Common API response messages."""

    SUCCESS = "Success"
    FAIL = "Fail"
    ERROR = "Error"


class AccountType(str, Enum):
    """Beasy employee account type."""

    SUPER_USER = "super_user"
    ADMIN = "admin"
    MEMBER = "member"


class AccountStatus(str, Enum):
    """Beasy employee account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"

