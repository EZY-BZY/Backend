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


class OwnerAccountStatus(str, Enum):
    """Company owner account status."""

    ACTIVE = "active"
    PENDING_VERIFICATION = "pending_verification"
    SUSPENDED = "suspended"
    BLOCKED = "blocked"
    DELETED = "deleted"


class ClientAccountType(str, Enum):
    """Client login account type selector."""

    OWNER = "owner"
    EMPLOYEE = "employee"


class CompanyStatus(str, Enum):
    """Company account visibility / lifecycle for client apps."""

    ACTIVE = "active"
    INACTIVE = "inactive"


class CompanyServiceType(str, Enum):
    """What the company offers on the platform."""

    SERVICES = "services"
    PRODUCTS = "products"
    PRODUCTS_AND_SERVICES = "products_and_services"

