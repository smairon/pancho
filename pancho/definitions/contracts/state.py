import pydantic
import collections.abc
import typing

from .identity import IdentifierType

StateIdentifierType = IdentifierType


class StateModel(pydantic.BaseModel):
    pass


T = typing.TypeVar('T', bound=StateModel)
StateDataType = T | collections.abc.Iterable[T] | None

StateScope = collections.abc.Sequence[StateIdentifierType] | StateIdentifierType


class StateHandler(typing.Protocol):
    @classmethod
    def __advertising__(cls) -> collections.abc.Iterable[type[StateModel]]: ...


class StateKeeper(StateHandler):
    async def __call__(self, state: StateDataType) -> typing.NoReturn: ...
