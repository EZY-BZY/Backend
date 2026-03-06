"""
Roles and permissions module.
Public API: RoleService, Permission names.
Used by: auth (for token claims), users (for assignments).
"""

from app.modules.roles.service import RoleService

__all__ = ["RoleService"]
