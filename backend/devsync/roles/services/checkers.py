import logging
from abc import ABC, abstractmethod
from typing import TypeVar, Protocol, Any, cast, Iterable, Optional

from rest_framework.serializers import Serializer
from rest_framework.views import APIView
from typing_extensions import runtime_checkable, Generic, Mapping

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
    """Abstract base class for parameter validation against a source value."""
    def __init__(self, source_getter: ParamViewFuncGetter[T]) -> None:
        self._source_getter = source_getter
        self._source: Optional[T] = None
        self._view: Optional[APIView] = None

    def load_source(self, view: APIView, *args: Any, **kwargs: Any) -> None:
        """Load the source value from view context."""
        self._source = self._source_getter(view, *args, **kwargs)
        self._view = view

    def __call__(self, project: Project, user_id: int, roles: Iterable[Role]) -> bool:
        """Validate parameters against the loaded source."""
        if self._source is None:
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


def source_path(attr: str, _default: T = None, _attr_index=1) -> ParamViewFuncGetter[T]:
    """Factory for creating type-safe attribute path getters."""
    def getter(*args: Any, **kwargs: Any) -> T:
        current = args[_attr_index]
        if isinstance(current, Serializer):
            current = current.validated_data
        for part in attr.split('.'):
            if current is _default:
                break
            current = (
                current.get(part, _default)
                if isinstance(current, Mapping)
                else getattr(current, part, _default)
            )

        return cast(T, current)

    return getter
