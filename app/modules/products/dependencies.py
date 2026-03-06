"""Products module dependencies."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import DbSession
from app.modules.products.repository import ProductRepository
from app.modules.products.service import ProductService


def get_product_repository(db: DbSession) -> ProductRepository:
    return ProductRepository(db)


def get_product_service(db: DbSession) -> ProductService:
    return ProductService(db)


ProductServiceDep = Annotated[ProductService, Depends(get_product_service)]
