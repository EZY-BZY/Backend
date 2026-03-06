"""API v1 router - mounts all module routes."""

from fastapi import APIRouter

from app.modules.auth.routes import router as auth_router
from app.modules.companies.routes import router as companies_router
from app.modules.users.routes import router as users_router
from app.modules.roles.routes import router as roles_router
from app.modules.products.routes import router as products_router
from app.modules.orders.routes import router as orders_router
from app.modules.invoices.routes import router as invoices_router
from app.modules.payments.routes import router as payments_router
from app.modules.ledger.routes import router as ledger_router
from app.modules.audit_logs.routes import router as audit_logs_router
from app.modules.employees.routes import router as employees_router
from app.modules.terms.routes import router as terms_router

api_router = APIRouter()

# Mount module routes under /api/v1 (prefix added in main)
api_router.include_router(auth_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)
api_router.include_router(roles_router)
api_router.include_router(products_router)
api_router.include_router(orders_router)
api_router.include_router(invoices_router)
api_router.include_router(payments_router)
api_router.include_router(ledger_router)
api_router.include_router(audit_logs_router)

# Organization management: employees (owner + members) and terms
organization_router = APIRouter(prefix="/organization", tags=["organization"])
organization_router.include_router(employees_router)
organization_router.include_router(terms_router)
api_router.include_router(organization_router)
