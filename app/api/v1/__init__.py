"""
API v1 — how routes are grouped for developers and OpenAPI.

The main app mounts this module under ``settings.api_v1_prefix`` (default ``/api/v1``),
so a route defined here as ``/beasy/...`` is served as ``/api/v1/beasy/...``.

**OpenAPI / Swagger**

- Full URL map and request/response schemas: ``/docs`` (Swagger UI) or ``/redoc``.
- Most JSON responses use the shared envelope from ``app.common.api_response``
  (``json_success`` / ``json_error``): ``status_code``, ``Message``, ``Data`` / error payload.
- Route-level explanations: use each handler’s ``summary`` and ``description`` in the
  module’s ``routes_*.py`` files; those strings are what appear in the generated docs.

**Three router groups (intentional split)**

1. ``beasy_router`` — prefix ``/beasy``. **Beasy employees** only: dashboard login,
   internal CRUD, listing owners/companies, **banks & wallets** admin,
   **company linked accounts** under ``/beasy/companies/{company_id}/financial-accounts``,
   etc. Protected with Beasy JWT where the handler
   uses ``CurrentEmployeeRequired``.

2. ``public_router`` — prefix ``/public``. Content **readable without client auth**
   (countries, industries, terms, …). Individual routes may still document extra rules.

3. ``clients_router`` — prefix ``/clients``. **Mobile / client app** flows: owner
   registration, **client auth** (login, forgot password), **companies** (owner-only),
   **read-only banks & wallets catalog** (list), **company financial accounts** CRUD
   under ``/companies/{id}/financial-accounts`` (owner JWT).

**Import order**

Routers are imported at module load; keep new modules alphabetically or grouped by
domain to reduce merge noise. ``include_router`` order rarely matters for FastAPI
path matching; prefer **more specific paths** (longer path templates) before generic
ones if you ever add overlapping routes in the same router.
"""

from fastapi import APIRouter

# --- Beasy (internal / dashboard) ---
from app.modules.app_permissions.routes_beasy import router as app_permissions_beasy_router
from app.modules.banks_and_wallets.routes_beasy import router as banks_wallets_beasy_router
from app.modules.beasy_auth.routes import router as beasy_auth_router
from app.modules.beasy_employees.routes import router as employees_router
from app.modules.companies.routes_beasy import router as companies_beasy_router
from app.modules.companies_owners.routes_beasy import router as owners_beasy_router
from app.modules.company_branches.routes_beasy import router as company_branches_beasy_router
from app.modules.company_contact_info.routes_beasy import (
    router as company_contact_info_beasy_router,
)
from app.modules.company_employees.routes_beasy import router as company_employees_beasy_router
from app.modules.company_documents_and_files.routes_beasy import (
    router as company_documents_beasy_router,
)
from app.modules.company_financials_accounts.routes_beasy import (
    router as company_financials_beasy_router,
)
from app.modules.fixed_assets.routes_beasy import router as fixed_assets_beasy_router
from app.modules.countries.routes_beasy import router as countries_beasy_router
from app.modules.industries.routes_beasy import router as industries_beasy_router
from app.modules.media.routes_beasy import router as media_beasy_router
from app.modules.terms.routes_beasy import router as terms_beasy_router

# --- Public (unauthenticated read-mostly) ---
from app.modules.countries.routes_global import router as countries_public_router
from app.modules.industries.routes_global import router as industries_public_router
from app.modules.terms.routes_global import router as terms_public_router

# --- Clients (mobile / owner app) ---
from app.modules.app_permissions.routes_clients import router as app_permissions_clients_router
from app.modules.banks_and_wallets.routes_clients import router as banks_wallets_clients_router
from app.modules.clients_auth.routes import router as clients_auth_router
from app.modules.companies.routes_clients import router as companies_clients_router
from app.modules.companies_owners.routes_clients import router as owners_clients_router
from app.modules.company_branches.routes_clients import router as company_branches_clients_router
from app.modules.company_contact_info.routes_clients import (
    router as company_contact_info_clients_router,
)
from app.modules.company_employees.routes_clients import router as company_employees_clients_router
from app.modules.company_documents_and_files.routes_clients import (
    router as company_documents_clients_router,
)
from app.modules.company_financials_accounts.routes_clients import (
    router as company_financials_clients_router,
)
from app.modules.fixed_assets.routes_clients import router as fixed_assets_clients_router

api_router = APIRouter()

# ---------------------------------------------------------------------------
# Beasy: /api/v1/beasy/...
# ---------------------------------------------------------------------------
beasy_router = APIRouter(prefix="/beasy")
beasy_router.include_router(beasy_auth_router)  # /auth/login, /auth/refresh
beasy_router.include_router(employees_router)
beasy_router.include_router(media_beasy_router)
beasy_router.include_router(countries_beasy_router)
beasy_router.include_router(industries_beasy_router)
beasy_router.include_router(app_permissions_beasy_router)
beasy_router.include_router(terms_beasy_router)
beasy_router.include_router(owners_beasy_router)
beasy_router.include_router(companies_beasy_router)  # list all companies
beasy_router.include_router(banks_wallets_beasy_router)  # CRUD banks & wallets catalog
beasy_router.include_router(
    company_financials_beasy_router
)  # /companies/{company_id}/financial-accounts — list/get by company
beasy_router.include_router(
    fixed_assets_beasy_router
)  # /companies/{company_id}/fixed-assets — list/get + media in payload
beasy_router.include_router(
    company_documents_beasy_router
)  # /companies/{company_id}/documents-and-files — list/get + media
beasy_router.include_router(
    company_contact_info_beasy_router
)  # /companies/{company_id}/contact-info — list/get
beasy_router.include_router(company_branches_beasy_router)  # /company-branches — list/get + filters
beasy_router.include_router(company_employees_beasy_router)  # /company-employees — list/get + filters
api_router.include_router(beasy_router)

# ---------------------------------------------------------------------------
# Public: /api/v1/public/...
# ---------------------------------------------------------------------------
public_router = APIRouter(prefix="/public", tags=["Public Routes"])
public_router.include_router(countries_public_router)
public_router.include_router(industries_public_router)
public_router.include_router(terms_public_router)
api_router.include_router(public_router)

# ---------------------------------------------------------------------------
# Clients: /api/v1/clients/...
# ---------------------------------------------------------------------------
clients_router = APIRouter(prefix="/clients")
clients_router.include_router(owners_clients_router)  # e.g. register / verify owner
clients_router.include_router(clients_auth_router)  # login, forgot password, change password
clients_router.include_router(companies_clients_router)  # /companies — owner JWT
# Read-only catalog; no Bearer required. Active rows only; response omits ``is_active`` (Beasy-only).
clients_router.include_router(banks_wallets_clients_router)
clients_router.include_router(app_permissions_clients_router)
# Nested: /companies/{company_id}/financial-accounts — register AFTER companies router
# so paths stay grouped in OpenAPI; FastAPI matches the longer path correctly.
clients_router.include_router(company_financials_clients_router)
clients_router.include_router(fixed_assets_clients_router)
clients_router.include_router(company_documents_clients_router)
clients_router.include_router(company_contact_info_clients_router)
clients_router.include_router(company_branches_clients_router)  # /companies/{id}/branches
clients_router.include_router(company_employees_clients_router)  # /companies/{id}/employees
api_router.include_router(clients_router)
