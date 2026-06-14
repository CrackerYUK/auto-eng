"""Role definitions for the permit-system users app."""

ROLE_OPERATOR = "operator"
ROLE_MASTER = "master"
ROLE_CHIEF = "chief"
ROLE_ADMIN = "admin"

ROLE_NAMES = (ROLE_OPERATOR, ROLE_MASTER, ROLE_CHIEF, ROLE_ADMIN)

LOCAL_PERMISSION_APP_LABELS = ("permits", "approvals", "documents", "audit")

ROLE_PERMISSIONS = {
    ROLE_OPERATOR: (
        ("permits", "permit", "add_permit"),
        ("permits", "permit", "change_permit"),
        ("permits", "permit", "view_permit"),
        ("documents", "documenttemplate", "view_documenttemplate"),
        ("documents", "generateddocument", "view_generateddocument"),
    ),
    ROLE_MASTER: (
        ("permits", "permit", "change_permit"),
        ("permits", "permit", "view_permit"),
        ("approvals", "approvalaction", "add_approvalaction"),
        ("approvals", "approvalaction", "view_approvalaction"),
    ),
    ROLE_CHIEF: (
        ("permits", "permit", "change_permit"),
        ("permits", "permit", "view_permit"),
        ("approvals", "approvalaction", "add_approvalaction"),
        ("approvals", "approvalaction", "view_approvalaction"),
    ),
}
