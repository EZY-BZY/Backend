# Organization Management Module

> **Current code:** B-easy staff APIs live under **`app/modules/beasy_employees/`** (Beasy employees). See [BEASY_EMPLOYEES.md](./BEASY_EMPLOYEES.md).

## Overview

This module provides **organization-level** APIs: one **owner**, multiple **members**, and **terms and conditions** (multilingual). It is separate from the multi-tenant companies/users module.

## Database Design

### Tables

1. **employees**
   - `id` (UUID, PK)
   - `full_name`, `email` (unique), `phone`
   - `password_hash`
   - `account_type`: `owner` | `admin` | `member`
   - `account_status`: `active` | `inactive` | `suspended`
   - `deleted_at` (soft delete)
   - `created_at`, `updated_at`, `created_by_id`, `updated_by_id` (FK → employees)
   - **Constraint**: At most one row with `account_type = 'owner'` and `deleted_at IS NULL` (partial unique index).

2. **employee_permissions**
   - `id` (UUID, PK)
   - `employee_id` (FK → employees, CASCADE)
   - `permission_name` (e.g. `view_members`, `manage_terms`)
   - `created_at`, `created_by_id` (FK → employees)
   - Unique (`employee_id`, `permission_name`).

3. **terms**
   - `id` (UUID, PK)
   - `term_title_ar`, `term_title_en`, `term_title_fr`
   - `term_desc_ar`, `term_desc_en`, `term_desc_fr`
   - `term_order` (int), `term_type` (enum), `status` (enum)
   - `created_at`, `updated_at`, `created_by_id`, `updated_by_id` (FK → employees)
   - **term_type**: `privacy_policy` | `terms_of_use` | `cookies_terms`
   - **status**: `valid` | `invalid`

## Folder Structure

```
app/modules/
  employees/
    enums.py          # AccountType, AccountStatus
    constants.py      # Permission name constants
    models.py         # Employee, EmployeePermission
    schemas.py        # OwnerCreate, MemberCreate, MemberUpdate, EmployeeRead, ...
    repository.py     # EmployeeRepository, EmployeePermissionRepository
    service.py        # EmployeeService (owner + members)
    dependencies.py   # get_current_employee, require_permission(permission_name)
    routes.py         # /owner, /auth/login, CRUD members
  terms/
    enums.py          # TermType, TermStatus
    models.py         # Term
    schemas.py        # TermCreate, TermUpdate, TermRead, TermReadByLanguage
    repository.py     # TermRepository
    service.py        # TermService
    dependencies.py   # TermServiceDep
    routes.py         # CRUD terms, list with filters, by-language
```

## API Endpoints

Base path: **`/api/v1/organization`**.

### Auth

- **POST /employees/auth/login**  
  Body: `{ "email", "password" }`.  
  Returns JWT with `sub = employee_id`. Use `Authorization: Bearer <access_token>` on protected routes.

### Owner (no auth required for creation; call once)

- **POST /employees/owner**  
  Body: `{ "full_name", "email", "phone?", "password" }`.  
  Creates the organization owner. Fails with 400 if owner already exists.

### Members (require auth + permission)

- **POST /employees** — create member — `create_member`
- **GET /employees** — list members (owner excluded), filter by account_status, name, email, phone; pagination — `view_members`
- **GET /employees/{id}** — get one member — `view_member`
- **PATCH /employees/{id}** — update member — `update_member`
- **DELETE /employees/{id}** — soft-deactivate member — `delete_member`

### Terms (manage endpoints require permission)

- **POST /terms** — add term — `manage_terms`
- **PATCH /terms/{id}** — edit term — `manage_terms`
- **DELETE /terms/{id}** — delete term — `manage_terms`
- **GET /terms/{id}** — view single term
- **GET /terms** — list terms (filter by type, status; sort by term_order)
- **GET /terms/{id}/by-language?lang=ar|en|fr** — term content for one language

## Permission Dependency

Use in route dependencies:

```python
from app.modules.employees.dependencies import require_permission, CurrentEmployeeRequired

@router.post("", dependencies=[Depends(require_permission("manage_terms"))])
def add_term(..., current: CurrentEmployeeRequired):
    ...
```

- **require_permission(permission_name)**  
  Resolves current employee from JWT, loads permissions from **employee_permissions**, allows request only if `permission_name` is present.
- Permission names are stored in DB (e.g. `view_members`, `create_member`, `manage_terms`). See `app.modules.employees.constants.ALL_PERMISSION_NAMES`.

## Business Rules

- Only **one** owner in the system; enforced by partial unique index and service check.
- Owner is **excluded** from “list members” results.
- Members are soft-deleted (`deleted_at`); owner cannot be deactivated via members API.
- Terms support **Arabic, English, French** (title + description per language).
- Only employees with the required permission (from DB) can add/edit/delete terms.

## Migrations and Seeds

- **Migration**: `alembic/versions/002_organization_employees_terms.py` creates `employees`, `employee_permissions`, `terms` and the one-owner constraint.
- **Seeds**: `scripts/seed_organization_permissions.py` prints permission names; assign permissions via PATCH member or direct insert into `employee_permissions`.

## Best Practices and Future Improvements

1. **Owner creation**: Consider protecting POST /employees/owner with a one-time secret or super-admin check in production.
2. **Refresh token**: Add org refresh endpoint that accepts refresh_token and returns new access token (reuse existing JWT helpers).
3. **Audit**: Add audit_log table or reuse existing audit_logs module for who created/updated owner, members, terms.
4. **Pagination**: List members and list terms already use page/page_size; keep a consistent max page_size (e.g. 100).
5. **Validation**: Pydantic schemas validate input; add business rules in service layer (e.g. no duplicate email).
6. **Expansion**: To support more roles, add an optional `role` field or keep using permission_names only; both are valid.
