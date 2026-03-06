"""Enums for employees module."""

from enum import Enum


class AccountType(str, Enum):
    """Employee account type. Only one 'owner' allowed in the system."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class AccountStatus(str, Enum):
    """Employee account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
