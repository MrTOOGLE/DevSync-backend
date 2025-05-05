from abc import ABC, abstractmethod
from typing import TypeVar, Protocol

from rest_framework.views import APIView
from typing_extensions import ParamSpec, runtime_checkable, Generic

from roles.models import Role

P = ParamSpec("P")
R = TypeVar("R")


@runtime_checkable
class ParamViewFuncGetter(Protocol[P, R]):
    def __call__(self: APIView, *args: P.args, **kwargs: P.kwargs) -> R:
        pass


class BaseParamChecker(ABC, Generic[P, R]):
    def __init__(self, source: ParamViewFuncGetter[P, R]):
        self._source_getter = source
        self._source: R = Ellipsis

    def load_source(self, view: APIView, *args: P.args, **kwargs: P.kwargs) -> None:
        self._source = self._source_getter(view, *args, **kwargs)

    def __call__(self, project_id: int, user_id: int) -> bool:
        if self._source is Ellipsis:
            raise ValueError("Source is not loaded. Use firstly .load_source() function.")
        return self._check(project_id, user_id)

    @abstractmethod
    def _check(self, project_id: int, user_id: int) -> bool:
        pass


class RankChecker(BaseParamChecker[P, int]):
    def _check(self, project_id: int, user_id: int) -> bool:
        user_rank = Role.objects.filter(
            project_id=project_id,
            members__user_id=user_id,
        ).order_by('-rank').only('rank').first().rank
        return user_rank > self._source


get_rank_from_validated_data = lambda view, *args, **kwargs: args[0].validated_data['rank']
get_rank_from_role_instance = lambda view, *args, **kwargs: args[0].rank
get_rank_from_role_related_instance = lambda view, *args, **kwargs: args[0].role.rank