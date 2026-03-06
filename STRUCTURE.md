# Project structure (modular monolith)

```
backend/
├── main.py                 # FastAPI app entry, lifespan, middleware, /health
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── alembic.ini
├── alembic/
│   ├── env.py              # Uses app.core.config, app.db.base, models_registry
│   ├── script.py.mako
│   └── versions/
│       └── 001_initial_schema.py
├── scripts/
│   ├── seed_roles_permissions.py
│   └── create_admin.py
│
└── app/
    ├── __init__.py
    ├── core/                # Config, security, logging, exceptions
    │   ├── config.py        # Pydantic Settings from env
    │   ├── security.py      # JWT, password hashing
    │   ├── logging_config.py
    │   ├── exceptions.py    # AppError, handlers
    │   └── middleware.py    # Request logging
    │
    ├── common/              # Shared utilities
    │   ├── schemas.py       # PaginatedResponse, MessageResponse
    │   └── pagination.py    # PaginationParams, paginate_query
    │
    ├── db/
    │   ├── base.py         # Base, TimestampMixin, UUIDPrimaryKeyMixin
    │   ├── session.py      # Engine, SessionLocal, get_db, DbSession
    │   └── models_registry.py  # Import all models for Alembic
    │
    ├── api/
    │   ├── deps.py         # get_pagination, Pagination
    │   └── v1/
    │       └── __init__.py # api_router, includes all module routes
    │
    └── modules/
        ├── auth/           # Login, refresh, get_current_user, require_permission
        │   ├── schemas.py, service.py, dependencies.py, routes.py
        ├── companies/      # Tenant CRUD
        │   ├── models.py, schemas.py, repository.py, service.py
        │   ├── dependencies.py, routes.py
        ├── users/          # Employees
        │   ├── models.py (User, UserRole), schemas, repository, service
        │   ├── dependencies.py, routes.py
        ├── roles/          # RBAC
        │   ├── models.py (Role, Permission, RolePermission), constants.py
        │   ├── schemas, repository, service, dependencies, routes
        ├── products/
        ├── orders/
        ├── invoices/
        ├── payments/
        ├── ledger/
        └── audit_logs/
```

Each module that owns data contains:

- `models.py` or `models/` – SQLAlchemy models
- `schemas.py` – Pydantic request/response
- `repository.py` or `repositories/` – data access
- `service.py` or `services/` – business logic (public API)
- `routes.py` – FastAPI router
- `dependencies.py` – FastAPI Depends for the module
- `constants.py`, `exceptions.py` when needed

Cross-module use: auth uses `UserService`, `CompanyService`, `RoleService` via their public services; never direct repository or model imports from another module except for shared types (e.g. UserRole in roles.service for the permission query).
