"""Roles module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.roles.service import RoleService


def get_role_service(db: DbSession) -> RoleService:
    return RoleService(db)


RoleServiceDep = Annotated[RoleService, Depends(get_role_service)]
