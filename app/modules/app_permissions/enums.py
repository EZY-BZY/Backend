"""Enums for app_permissions history."""

from enum import Enum


class AppPermissionHistoryAction(str, Enum):
    """Recorded when a permission row is updated or hard-deleted."""

    UPDATED = "updated"
    DELETED = "deleted"
