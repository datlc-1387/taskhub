# Validation limits shared by schemas and dependencies.

# Users
FULL_NAME_MAX_LENGTH = 100
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 72  # bcrypt ignores everything after 72 bytes; also checked in bytes

# Workspaces and projects
WORKSPACE_NAME_MAX_LENGTH = 100
PROJECT_NAME_MAX_LENGTH = 100
PROJECT_DESCRIPTION_MAX_LENGTH = 2000

# Tasks, labels and comments
TASK_TITLE_MAX_LENGTH = 200
TASK_DESCRIPTION_MAX_LENGTH = 5000
LABEL_NAME_MAX_LENGTH = 50
COMMENT_MAX_LENGTH = 5000

# Pagination
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
