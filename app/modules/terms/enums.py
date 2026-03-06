"""Enums for terms and conditions module."""

from enum import Enum


class TermType(str, Enum):
    """Allowed term_type values."""

    PRIVACY_POLICY = "privacy_policy"
    TERMS_OF_USE = "terms_of_use"
    COOKIES_TERMS = "cookies_terms"


class TermStatus(str, Enum):
    """Allowed status values for a term."""

    VALID = "valid"
    INVALID = "invalid"
