import collections.abc
import typing
import pydantic
from .interaction import Message
from .state import StateScope, StateIdentifierType


class ContextModel(pydantic.BaseModel):
    pass


ContextDataType = ContextModel | collections.abc.Mapping[StateIdentifierType, ContextModel]


class ContextCollector(typing.Protocol):
    async def __call__(
        self,
        model_contract: type[ContextModel],
        state_scope: StateScope,
        message: Message | None = None
    ) -> collections.abc.Mapping[StateIdentifierType, ContextModel]: ...
