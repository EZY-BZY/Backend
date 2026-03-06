"""Users module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.users.repository import UserRepository
from app.modules.users.service import UserService


def get_user_repository(db: DbSession) -> UserRepository:
    return UserRepository(db)


def get_user_service(db: DbSession) -> UserService:
    return UserService(db)


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
