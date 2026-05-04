"""Enums for the Beasy employees (`beasy_employees`) module."""

from enum import Enum


class AccountType(str, Enum):
    """Employee account type. Only one 'Super User' allowed in the system."""

    SUPER_USER = "super_user"
    ADMIN = "admin"
    MEMBER = "member"


class AccountStatus(str, Enum):
    """Employee account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
