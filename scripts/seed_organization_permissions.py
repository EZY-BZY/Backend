"""
Seed permission names for organization module.
Does not create employees; use create_owner first, then assign permissions to members.
Run from project root: python -m scripts.seed_organization_permissions

Usage after owner exists:
  - Assign permissions to a member via PATCH /api/v1/organization/employees/{id}
    with body {"permission_names": ["view_members", "manage_terms", ...]}
  - Or insert into employee_permissions (employee_id, permission_name, created_by_id).
"""

from app.modules.employees.constants import ALL_PERMISSION_NAMES

if __name__ == "__main__":
    print("Organization permission names (use these in employee_permissions.permission_name):")
    for name in ALL_PERMISSION_NAMES:
        print(f"  - {name}")
    print("\nAssign via API: PATCH /api/v1/organization/employees/{id} with permission_names array.")
    print("Or insert into employee_permissions table after creating members.")
