import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Protocol, Any, cast, Iterable, Optional

from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from typing_extensions import runtime_checkable, Generic, Mapping, Literal

from projects.models import Project
from roles.models import Role

T = TypeVar("T")

logger = logging.getLogger('django')


@runtime_checkable
class ParamViewFuncGetter(Protocol[T]):
    """Protocol for callables that extract parameters from view functions."""

    def __call__(self: APIView, *args: Any, **kwargs: Any) -> T:
        pass


class BaseParamChecker(ABC, Generic[T]):

    def __init__(self, source_getter: ParamViewFuncGetter[T], check_order: Literal['post', 'pre'] = 'post',
                 stop_on_success=False) -> None:
        self._source_getter = source_getter
        self._source: Optional[T] = Ellipsis
        self._view: Optional[APIView] = None
        self._check_order = check_order
        self._stop_on_success = stop_on_success

    @property
    def check_order(self) -> Literal['post', 'pre']:
        return self._check_order

    @property
    def view(self) -> APIView:
        return self._view

    @property
    def stop_on_success(self) -> bool:
        return self._stop_on_success

    def load_source(self, view: APIView, *args: Any, **kwargs: Any) -> None:
        """Load the source value from view context."""
        self._source = self._source_getter(view, *args, **kwargs)
        self._view = view

    def __call__(self, project: Project, user_id: int, roles: Iterable[Role]) -> bool:
        """Validate parameters against the loaded source."""
        if self._source is Ellipsis:
            raise ValueError(
                "Source not loaded. Call load_source() first or check source initialization."
            )
        return self._check(project, user_id, roles)

    @abstractmethod
    def _check(self, project: Project, user_id: int, roles: Iterable[Role]) -> bool:
        """Implement concrete validation logic in subclasses."""

    @staticmethod
    def _get_user_rank(roles: Iterable[Role]):
        """Get the highest rank from user's roles."""
        return max(roles, key=lambda role: role.rank).rank


class RankChecker(BaseParamChecker[int]):
    """Validates if user's rank exceeds the source rank."""

    def _check(self, project: Project, user_id: int, roles: Iterable[Role]) -> bool:
        return self._get_user_rank(roles) > self._source


class NotOwnerTargetChecker(BaseParamChecker[int]):
    """Validates that user is not the project owner."""

    def _check(self, project: Project, user_id: int, roles: Iterable[Role]) -> bool:
        return project.owner_id != user_id


class CompareUsersRankChecker(BaseParamChecker[int]):
    """Compares ranks between current user and source user."""

    def _check(self, project: Project, user_id: int, roles: Iterable[Role]) -> bool:
        if project.owner_id == user_id:
            return True
        if project.owner_id == self._source:
            return False
        highest_role = Role.objects.filter(
            project_id=project.id,
            members__user_id=self._source
        ).only('rank').order_by('-rank').first()

        return self._get_user_rank(roles) > highest_role.rank


class CreatorBypassChecker(BaseParamChecker[int]):
    """
    Special checker that bypasses validation if user is the creator.
    Runs early (pre-check) and stops further checks on success.
    """

    def __init__(self, source_getter: ParamViewFuncGetter[T], check_order: Literal['post', 'pre'] = 'pre',
                 stop_on_success=True) -> None:
        super().__init__(source_getter, check_order, stop_on_success)

    def _check(self, project: Project, user_id: int, roles: Iterable[Role]) -> bool:
        return user_id == self._source


def source_path(attr: str, default: T = None, attr_index=1) -> ParamViewFuncGetter[T]:
    """
    Factory for creating type-safe attribute path getters.

    Args:
        attr: Dot-separated path to the attribute
        default: Default value if path resolution fails
        attr_index: Position of the target object in view args

    Returns:
        Callable that extracts the attribute value from view context
    """

    def getter(*args: Any, **kwargs: Any) -> T:
        current = args[attr_index]
        if isinstance(current, Serializer):
            current = current.validated_data
        for part in attr.split('.'):
            if current is default:
                break
            current = (
                current.get(part, default)
                if isinstance(current, Mapping)
                else getattr(current, part, default)
            )

        return cast(T, current)

    return getter
