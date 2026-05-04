"""Term type and history action enums."""

from enum import Enum


class TermType(str, Enum):
    """Allowed legal/application term categories (stored as value in DB column `type`)."""

    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_USE = "terms_of_use"
    REFUND_TERMS = "refund_terms"
    DELIVERY_TERMS = "delivery_terms"


class HistoryAction(str, Enum):
    """Audit action for terms_history."""

    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"
