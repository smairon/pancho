import abc
import collections.abc
import inspect
import typing

from ..definitions import contracts
from ..exploration.types import search_for_subtype


class Actor(contracts.Actor, abc.ABC):
    __internals: contracts.ActorInternals = None

    def __init__(
        self,
        state_id: contracts.StateIdentifierType | None = None
    ):
        self._state_id = state_id
        self._state = None

    def __receive__(
        self,
        message: contracts.Message,
        context: contracts.ContextModel | None = None
    ) -> collections.abc.Iterable[contracts.Event] | None:
        handler_method_name = self._search_for_instance(type(message))
        if handler_method_name:
            method = getattr(self, handler_method_name)
            if self.__internals__().message_context_map.get(type(message)):
                events = method(message, context)
            else:
                events = method(message)
            if events is not None:
                if not isinstance(events, collections.abc.Sequence):
                    events = (events,)
                return events

    @abc.abstractmethod
    def __state__(self) -> contracts.StateModel | None:
        ...

    def __state_id__(self) -> contracts.IdentifierType | None:
        return self._state_id

    @classmethod
    def __internals__(cls) -> contracts.ActorInternals:
        if not cls.__internals:
            message_handler_map = {}
            message_context_map = {}
            for member in inspect.getmembers(cls, predicate=inspect.isfunction):
                _method = member[1].__dict__.get('__wrapped__') or member[1]
                _message_contract = None
                _annotations = _method.__annotations__
                if _annotations:
                    for v in _annotations.values():
                        if hasattr(v, '__mro__') and (contracts.Event in v.__mro__ or contracts.Command in v.__mro__):
                            _message_contract = v
                            message_handler_map[_message_contract] = member[0]
                            break

                    if _message_contract is None:
                        continue

                    for v in _annotations.values():
                        if context_model_contract := search_for_subtype(v, contracts.ContextModel):
                            message_context_map[_message_contract] = context_model_contract

            cls.__internals = contracts.ActorInternals(
                message_handler_map=message_handler_map,
                message_context_map=message_context_map
            )
        return cls.__internals

    @classmethod
    def __advertising__(cls) -> typing.Iterable[
        tuple[type[contracts.Message] | type[contracts.ContextModel]]
    ]:
        for message_contract in cls.__internals__().message_handler_map.keys():
            context_contract = cls.__internals__().message_context_map.get(message_contract)
            yield message_contract, context_contract

    def _search_for_instance(self, message_contract) -> str | None:
        for contract in message_contract.__mro__:
            if instance := self.__internals__().message_handler_map.get(contract):
                return instance
