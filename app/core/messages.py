# Error messages returned to API clients.
# Templates with {placeholders} are filled with str.format() where they are raised.

# Generic (exception handlers)
INVALID_DATA = "Invalid data"
INTERNAL_ERROR = "Internal server error. Please try again later"

# Tokens
TOKEN_EXPIRED = "The token has expired"
TOKEN_INVALID = "Invalid token"
TOKEN_WRONG_TYPE = "Need {expected} token, but received {actual} token"
REFRESH_TOKEN_REVOKED = "The refresh token has been revoked"

# Authentication and users
EMAIL_ALREADY_REGISTERED = "Email already registered"
INCORRECT_CREDENTIALS = "Incorrect email or password"
CURRENT_PASSWORD_INCORRECT = "The current password is incorrect"
PASSWORD_TOO_LONG = (
    "Maximum password length is {max_bytes} bytes (approximately {max_bytes} unaccented characters)"
)
ACCOUNT_LOCKED = "The account has been locked"
TOKEN_USER_NOT_FOUND = "User doesn't exist"
USER_NOT_FOUND = "User {user_id} doesn't exist"

# Workspaces and members
WORKSPACE_NOT_FOUND = "Workspace {workspace_id} does not exist"
ROLE_REQUIRED = "Requires the {role} role or higher within the workspace"
USER_NOT_MEMBER = "User {user_id} is not a member of the workspace"
USER_ALREADY_MEMBER = "User is already a member"
CANNOT_CHANGE_OWNER_ROLE = "Cannot change OWNER role"
CANNOT_CHANGE_WORKSPACE_OWNER = "Cannot change or remove the workspace owner"

# Projects, tasks, labels and comments
PROJECT_NOT_FOUND = "Project {project_id} does not exist"
TASK_NOT_FOUND = "Task {task_id} does not exist"
TASK_DELETE_FORBIDDEN = "Only EDITOR/OWNER or the creator can delete the task"
LABEL_NOT_FOUND = "Label {label_id} does not exist"
LABEL_NOT_IN_PROJECT = "Label {label_id} does not belong to the project"
LABELS_NOT_IN_PROJECT = "Labels {label_ids} do not belong to the project"
LABEL_ALREADY_ON_TASK = "Label {label_id} is already attached to the task"
LABEL_NOT_ON_TASK = "Label {label_id} is not attached to the task"
COMMENT_NOT_FOUND = "Comment {comment_id} does not exist"
COMMENT_DELETE_FORBIDDEN = "Only the author or the OWNER can delete a comment"
