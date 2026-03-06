"""Company (tenant) model."""

from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Company(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Supplier company - the tenant in multi-tenant design."""

    __tablename__ = "companies"

    name: Mapped[str] = mapped_column(String(256), nullable=False)
    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    users = relationship("User", back_populates="company", lazy="selectin")
    roles = relationship("Role", back_populates="company", lazy="selectin")
    products = relationship("Product", back_populates="company", lazy="selectin")
