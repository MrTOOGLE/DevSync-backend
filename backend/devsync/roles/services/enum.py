from enum import auto, Enum


class PermissionsEnum(Enum):
    @staticmethod
    def _generate_next_value_(name, start, count, last_values) -> str:
        return name.lower()

    # Project
    PROJECT_MANAGE: str = auto()
    # Members
    MEMBER_MANAGE: str = auto()
    # Departments
    DEPARTMENT_MANAGE: str = auto()
    MEMBER_DEPARTMENT_ASSIGN: str = auto()
    # Roles
    ROLE_MANAGE: str = auto()
    MEMBER_ROLE_ASSIGN: str = auto()
    # Voting
    VOTING_MANAGE: str = auto()
    VOTING_CREATE: str = auto()
    VOTING_VOTE: str = auto()
    # Comments
    COMMENT_MANAGE: str = auto()
    COMMENT_CREATE: str = auto()
    # Tasks
    TASK_MANAGE: str = auto()
    TASK_DEPARTMENT_MANAGE: str = auto()
    TASK_VIEW_ALL: str = auto()
    TASK_VIEW_DEPARTMENT: str = auto()
    TASK_VIEW_ASSIGNED: str = auto()

    @property
    def value(self) -> str:
        return super().value
