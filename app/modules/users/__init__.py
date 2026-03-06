"""
Users (employees) module.
Public API: UserService.
Users belong to a company and have role assignments.
"""

from app.modules.users.service import UserService

__all__ = ["UserService"]
