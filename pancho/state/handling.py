import abc
import collections.abc
import inspect

from ..definitions import contracts
from ..exploration import search_for_subtype


class StateKeeper(contracts.StateKeeper, abc.ABC):
    @classmethod
    def __advertising__(cls) -> collections.abc.Iterable[type[contracts.StateModel]]:
        for member in inspect.getmembers(cls, predicate=inspect.isfunction):
            for _param_type in member[1].__annotations__.values():
                if _state_model_contract := search_for_subtype(_param_type, contracts.StateModel):
                    yield _state_model_contract
