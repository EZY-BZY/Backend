"""Permission names used for require_permission(). Stored in DB; these are the canonical names."""

# Members
PERM_VIEW_MEMBERS = "view_members"
PERM_CREATE_MEMBER = "create_member"
PERM_UPDATE_MEMBER = "update_member"
PERM_DELETE_MEMBER = "delete_member"
PERM_VIEW_MEMBER = "view_member"

# Terms
PERM_VIEW_TERMS = "view_terms"
PERM_MANAGE_TERMS = "manage_terms"  # add, edit, delete terms
PERM_ADD_TERM = "add_term"
PERM_EDIT_TERM = "edit_term"
PERM_DELETE_TERM = "delete_term"

# Owner (internal; owner creation is a special endpoint)
PERM_CREATE_OWNER = "create_owner"

ALL_PERMISSION_NAMES = [
    PERM_VIEW_MEMBERS,
    PERM_CREATE_MEMBER,
    PERM_UPDATE_MEMBER,
    PERM_DELETE_MEMBER,
    PERM_VIEW_MEMBER,
    PERM_VIEW_TERMS,
    PERM_MANAGE_TERMS,
    PERM_ADD_TERM,
    PERM_EDIT_TERM,
    PERM_DELETE_TERM,
]
