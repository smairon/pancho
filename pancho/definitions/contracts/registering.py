import typing
import dataclasses
import collections.abc
from zorge import contracts as zorge_contracts
from .operations import Actor
from .interaction import Message
from .state import StateModel, StateHandler
from .context import ContextModel, ContextCollector

DependencyContainer = zorge_contracts.DependencyContainer


@dataclasses.dataclass
class DependencyMapValue:
    field_name: str
    field_type: type[typing.Any]


@dataclasses.dataclass
class DependencyMaps:
    message_actor: dict[
        type[Message],
        type[Actor]
    ]
    actor_state: dict[
        type[Actor],
        DependencyMapValue
    ]
    actor_context: dict[
        type[Actor],
        DependencyMapValue
    ]
    message_context: dict[
        type[Message],
        type[ContextModel]
    ]
    state_getter: dict[
        type[StateModel],
        DependencyMapValue
    ]
    state_keeper: dict[
        type[StateModel],
        DependencyMapValue
    ]
    context_model_collector: dict[
        type[ContextModel],
        DependencyMapValue
    ]


class DependencyRegistry:
    def register_connection_context(
        self,
        open_callback: typing.Callable,
        close_success_callback: typing.Callable,
        close_failure_callback: typing.Callable,
        contract: zorge_contracts.DependencyBindingContract
    ): ...

    def register_registry(
        self,
        instance: zorge_contracts.DependencyBindingInstance,
        contract: zorge_contracts.DependencyBindingContract
    ): ...

    def register_data_vendor(
        self,
        instance: zorge_contracts.DependencyBindingInstance,
        contract: zorge_contracts.DependencyBindingContract
    ): ...

    def register_context_collector(
        self,
        instance: type[ContextCollector],
        contract: type[ContextModel]
    ): ...

    def register_actor(
        self,
        instance: type[Actor],
    ): ...

    def register_state_handler(
        self,
        instance: type[StateHandler]
    ): ...

    def register_view(
        self,
        instance: zorge_contracts.DependencyBindingInstance,
        contract: zorge_contracts.DependencyBindingContract | None = None,
        scope: typing.Literal['instance', 'global'] = 'instance'
    ): ...

    def get_container(self) -> zorge_contracts.DependencyContainer: ...

    def get_maps(self) -> DependencyMaps: ...


class StateRegistry(typing.Protocol):
    def register_state(
        self,
        state_model_contract: type[StateModel],
        state_handler_contract: type[StateHandler]
    ): ...

    def get_handler(
        self,
        state_model_contract: type[StateModel]
    ) -> type[StateHandler] | None: ...


class ContextRegistry(typing.Protocol):
    def register_context(
        self,
        context_model_contract: type[ContextModel],
        context_collector_contract: type[ContextCollector]
    ): ...

    def get_collector(
        self,
        context_model_contract: type[ContextModel]
    ) -> type[ContextCollector] | None: ...


class MessageRegistry(typing.Protocol):
    def register_message(
        self,
        message_contract: type[Message],
        actor_contract: type[Actor],
        context_model_contract: type[ContextModel] | None = None
    ): ...

    def get_actors_with_context(
        self,
        message_contract: type[Message]
    ) -> collections.abc.Iterable[tuple[type[Actor], type[ContextModel] | None]]: ...
