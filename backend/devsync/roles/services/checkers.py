from abc import ABC, abstractmethod
from typing import TypeVar, Protocol

from rest_framework.views import APIView
from typing_extensions import ParamSpec, runtime_checkable, Generic

from roles.models import Role

P = ParamSpec("P")
R = TypeVar("R")


@runtime_checkable
class ParamViewFuncGetter(Protocol[P, R]):
    """
    Protocol defining a callable that gets parameters from a view function.

    This describes a callable that takes an APIView instance and returns
    a value of type R, using the parameters P.
    """
    def __call__(self: APIView, *args: P.args, **kwargs: P.kwargs) -> R:
        pass


class BaseParamChecker(ABC, Generic[P, R]):
    """
    Abstract base class for parameter checkers.

    Provides infrastructure for checking parameters against some source value.
    The source value is obtained through a ParamViewFuncGetter and must be
    loaded before checking.

    Args:
        source: A callable that retrieves the source value to check against
    """
    def __init__(self, source: ParamViewFuncGetter[P, R]):
        self._source_getter = source
        self._source: R = Ellipsis

    def load_source(self, view: APIView, *args: P.args, **kwargs: P.kwargs) -> None:
        """
        Load the source value from the given view and arguments.

        Args:
            view: The APIView instance to get the source from
            args: Positional arguments to pass to the source getter
            kwargs: Keyword arguments to pass to the source getter
        """
        self._source = self._source_getter(view, *args, **kwargs)

    def __call__(self, project_id: int, user_id: int) -> bool:
        """
        Check if the user meets the parameter requirements.

        Args:
            project_id: The project ID to check permissions for
            user_id: The user ID to check permissions for

        Returns:
            bool: True if the check passes, False otherwise

        Raises:
            ValueError: If the source hasn't been loaded
        """
        if self._source is Ellipsis:
            raise ValueError("Source is not loaded. Use firstly .load_source() function.")
        return self._check(project_id, user_id)

    @abstractmethod
    def _check(self, project_id: int, user_id: int) -> bool:
        """
        Abstract method to implement the actual parameter check logic.

        Args:
            project_id: The project ID to check
            user_id: The user ID to check

        Returns:
            bool: True if the check passes, False otherwise
        """


class RankChecker(BaseParamChecker[P, int]):
    """
    Checker that verifies if a user's rank is higher than a source rank.

    The source rank is obtained through the source getter and compared against
    the user's rank in the specified project.
    """
    def _check(self, project_id: int, user_id: int) -> bool:
        user_rank = Role.objects.filter(
            project_id=project_id,
            members__user_id=user_id,
        ).order_by('-rank').only('rank').first().rank
        return user_rank > self._source


get_rank_from_validated_data = lambda view, *args, **kwargs: args[0].validated_data['rank']
get_rank_from_role_instance = lambda view, *args, **kwargs: args[0].rank
get_rank_from_role_related_instance = lambda view, *args, **kwargs: args[0].role.rank
