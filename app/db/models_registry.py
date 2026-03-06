"""
Import all ORM models so Alembic and SQLAlchemy can discover them.
Do not use for business logic - this is only for metadata/schema.
"""
from app.db.base import Base

# Companies and tenant-scoped modules
from app.modules.companies.models import Company  # noqa: F401
from app.modules.roles.models import Role, Permission, RolePermission  # noqa: F401
from app.modules.users.models import User, UserRole  # noqa: F401
from app.modules.products.models import Product  # noqa: F401
from app.modules.orders.models import Order, OrderItem  # noqa: F401
from app.modules.invoices.models import Invoice  # noqa: F401
from app.modules.payments.models import Payment  # noqa: F401
from app.modules.ledger.models import LedgerEntry  # noqa: F401
from app.modules.audit_logs.models import AuditLog  # noqa: F401
# Organization management
from app.modules.employees.models import Employee, EmployeePermission  # noqa: F401
from app.modules.terms.models import Term  # noqa: F401

__all__ = ["Base"]
