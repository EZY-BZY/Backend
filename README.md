# Supplier SaaS Backend

Production-ready **modular monolith** backend for a multi-tenant SaaS for supplier companies. Built with FastAPI, PostgreSQL, SQLAlchemy 2.0, JWT auth, and Docker.

## Architecture

- **Modular monolith**: One deployable app, with clear module boundaries. Each module owns its models, schemas, repositories, services, routes, and dependencies.
- **Multi-tenancy**: Each supplier company is a tenant. All data is isolated by `company_id`; the backend never trusts client-sent tenant IDs.
- **Tech stack**: FastAPI, PostgreSQL, MongoDB, Redis, SQLAlchemy 2.0, Alembic, Pydantic v2, JWT (access + refresh), Docker.

### Infrastructure connections

| Store | Purpose | Config |
|-------|---------|--------|
| **PostgreSQL** | Relational data (ORM, migrations) | `DATABASE_URL` |
| **MongoDB** | Documents, flexible payloads | `MONGODB_URL`, `MONGODB_DATABASE` |
| **Redis** | Cache, pub/sub, queues | `REDIS_URL` |

Connection helpers live under `app/infrastructure/` (`postgres.py`, `mongo.py`, `redis_service.py`). Use `from app.infrastructure.deps import DbSession, MongoDatabase, RedisClient` in routes. See `docs/INFRASTRUCTURE.md`.

### Module layout

```
app/
  core/              # Config, security, logging, exceptions
  common/            # Pagination, API envelope, shared schemas
  infrastructure/    # Postgres, MongoDB, Redis connection services
  db/                # Session, base models, model registry
  api/               # Shared deps, v1 router
  modules/
    beasy_auth/       # Beasy dashboard login + JWT refresh
    beasy_employees/  # Beasy employees (B-easy staff: Super User, members)
```

**Beasy auth** (dashboard login) is documented in [docs/BEASY_AUTH.md](docs/BEASY_AUTH.md).  
**Beasy employees** (folder `beasy_employees`, import `app.modules.beasy_employees`) is documented in [docs/BEASY_EMPLOYEES.md](docs/BEASY_EMPLOYEES.md).

## Quick start

### Local (no Docker)

1. **Environment**

   ```bash
   cp .env.example .env
   # Edit .env: set DATABASE_URL and SECRET_KEY
   ```

2. **Database**

   ```bash
   python -m venv .venv
   source .venv/bin/activate   # or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   alembic upgrade head
   ```

3. **Run**

   ```bash
   uvicorn main:app --reload
   ```

   - API: http://localhost:8000  
   - Docs: http://localhost:8000/docs  

### Docker

Stack: **app**, **PostgreSQL**, **MongoDB**, **Redis**.

```bash
docker-compose up -d db mongo redis
# Wait for services to be healthy, then:
alembic upgrade head
docker-compose up app
```

Or start the full stack:

```bash
docker-compose up --build
```

Readiness (all three stores): `GET http://localhost:8000/health/ready`

## API versioning

All module routes are under **`/api/v1`**, e.g.:

- `POST /api/v1/auth/login`
- `GET /api/v1/companies/{id}`
- `GET /api/v1/orders/{id}`
- `GET /api/v1/ledger/balance/{from_company_id}/{to_company_id}`

## Authentication

- **Login**: `POST /api/v1/auth/login` with JSON `{"email", "password", "company_slug"}` (company_slug optional if user has one company).
- **Tokens**: Access token (short-lived) and refresh token (long-lived). Use `Authorization: Bearer <access_token>`.
- **Refresh**: `POST /api/v1/auth/refresh` with JSON `{"refresh_token": "..."}`.
- **Current user**: Use dependency `get_current_active_user` or `get_current_company_member` for tenant-scoped routes.
- **Permissions**: Use `Depends(require_permission("orders:manage"))` (or similar) on routes that need RBAC.

## Seeding and first admin

1. Create a company (e.g. via `POST /api/v1/companies` or a script).
2. Seed roles and permissions:

   ```bash
   python -m scripts.seed_roles_permissions
   ```

3. Create first admin user:

   ```bash
   python -m scripts.create_admin <company_slug> <email> <password>
   ```

   Example: `python -m scripts.create_admin acme admin@acme.com SecurePass123`

## Multi-tenancy and security

- **Tenant ID**: Always taken from the JWT `company_id` (or from the current user’s company). Never use a client-provided company id for access control.
- **Helpers**: `get_current_company_member` ensures the user belongs to the company in the token.
- **Filtering**: All tenant-scoped queries filter by `company_id` in the service/repository layer.

## Ledger and balances

- **Ledger entries**: `from_company_id`, `to_company_id`, `amount`, `source_type`, `source_id` (e.g. invoice, payment). Used to compute “who owes whom.”
- **Balance**: `GET /api/v1/ledger/balance/{from_company_id}/{to_company_id}?currency=USD` returns the amount that `from_company` owes `to_company` (positive = debt).

## Audit logs

- **Table**: `audit_logs` with `actor_user_id`, `company_id`, `action`, `target_type`, `target_id`, `metadata`, `created_at`.
- **Actions**: e.g. login, create_employee, block_employee, create_order, create_invoice, register_payment. Use `AuditLogService.log()` from other modules after sensitive operations.

## Health check

- **GET /health** returns `{"status": "Success", "service": "..."}` for load balancers and containers.

## Development

- **Migrations**: `alembic revision --autogenerate -m "description"` then `alembic upgrade head`.
- **Tests**: Add pytest in `tests/`; use `httpx` and `TestClient` for API tests. Focus on auth and tenant isolation.

## License

Proprietary / your choice.
