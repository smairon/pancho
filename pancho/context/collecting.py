import collections.abc
import inspect
import typing

from ..definitions import contracts
from ..exploration.types import search_for_subtype


class ContextCollector(contracts.ContextCollector):
    __internals = {}

    async def __call__(
        self,
        model_contract: type[contracts.ContextModel],
        state_scope: contracts.StateScope,
        message: contracts.Message | None = None
    ) -> collections.abc.Mapping[contracts.StateIdentifierType, contracts.ContextModel]:
        if method := self._search_for_instance(model_contract):
            data = await method(self, state_scope=state_scope, message=message)
            if not isinstance(state_scope, collections.abc.Sequence) and not isinstance(data, collections.abc.Mapping):
                return {
                    state_scope: data
                }
            return data

    @classmethod
    def __internals__(cls):
        if not cls.__internals:
            for member in inspect.getmembers(cls, predicate=inspect.isfunction):
                _method = member[1].__dict__.get('__wrapped__') or member[1]
                _annotations = _method.__annotations__ or {}
                if context_model_contract := search_for_subtype(_annotations.get('return'), contracts.ContextModel):
                    cls.__internals[context_model_contract] = _method
        return cls.__internals

    @classmethod
    def __advertising__(cls):
        return (c for c in cls.__internals__().keys())

    def _search_for_instance(
        self,
        model_contract: type[contracts.ContextModel]
    ) -> typing.Callable:
        for contract in model_contract.__mro__:
            if instance := self.__internals__().get(contract):
                return instance
