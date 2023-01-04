import collections.abc
import typing

from zorge.di.container import DependencyContainer
from zorge import contracts as zorge_contracts
from ..definitions import contracts
from ..identity.factory import UUIDIdentifierFactory
from ..interaction.factory import InteractionFactory


class DependencyRegistry:
    def __init__(
        self,
        dc: zorge_contracts.DependencyContainer | None = None,
        identifier_factory: contracts.IdentifierFactory = UUIDIdentifierFactory,
        interaction_factory: contracts.InteractionFactory = InteractionFactory,
    ):
        self._dc = dc or DependencyContainer()
        self._dc.register_contractual_dependency(
            instance=identifier_factory,
            contract=contracts.IdentifierFactory
        )
        self._dc.register_contractual_dependency(
            instance=interaction_factory,
            contract=contracts.InteractionFactory
        )

    def register_connection_context(
        self,
        open_callback: typing.Callable,
        close_success_callback: typing.Callable,
        close_failure_callback: typing.Callable,
        contract: zorge_contracts.DependencyBindingContract
    ):
        self._dc.register_instance_singleton(
            instance=open_callback,
            contract=contract,
        )
        self._dc.register_shutdown_callback(
            success_callback=close_success_callback,
            failure_callback=close_failure_callback,
            contract=contract,
        )

    def register_registry(
        self,
        instance: zorge_contracts.DependencyBindingInstance,
        contract: zorge_contracts.DependencyBindingContract
    ):
        self._dc.register_global_singleton(
            instance=instance,
            contract=contract
        )

    def register_data_vendor(
        self,
        instance: zorge_contracts.DependencyBindingInstance,
        contract: zorge_contracts.DependencyBindingContract
    ):
        self._dc.register_contractual_dependency(
            instance=instance,
            contract=contract
        )

    def register_context_collector(
        self,
        instance: type[contracts.ContextCollector],
    ):
        self._dc.register_selfish_dependency(
            instance=instance,
        )

    def register_actor(
        self,
        instance: type[contracts.Actor],
    ):
        self._dc.register_selfish_dependency(
            instance=instance,
            singleton_scope=zorge_contracts.DependencyBindingScope.INSTANCE
        )

    def register_state_handler(
        self,
        instance: type[contracts.StateHandler]
    ):
        self._dc.register_selfish_dependency(
            instance=instance,
            singleton_scope=zorge_contracts.DependencyBindingScope.INSTANCE
        )

    def register_view(
        self,
        instance: zorge_contracts.DependencyBindingInstance,
        contract: zorge_contracts.DependencyBindingContract | None = None,
        scope: typing.Literal['instance', 'global'] = 'instance'
    ):
        if not contract:
            self._dc.register_selfish_dependency(
                instance=instance,
                singleton_scope={
                    'instance': zorge_contracts.DependencyBindingScope.INSTANCE,
                    'global': zorge_contracts.DependencyBindingScope.GLOBAL
                }[scope]
            )
        else:
            {
                'instance': self._dc.register_global_singleton,
                'global': self._dc.register_global_singleton
            }[scope](
                instance=instance,
                contract=contract
            )

    def get_container(self) -> DependencyContainer:
        return self._dc


class StateRegistry(contracts.StateRegistry):
    def __init__(self):
        self._map = {}

    def register_state(
        self,
        state_model_contract: type[contracts.StateModel],
        state_handler_contract: type[contracts.StateHandler]
    ):
        if contracts.StateKeeper in state_handler_contract.__mro__:
            self._map[state_model_contract] = state_handler_contract

    def get_handler(
        self,
        state_model: type[contracts.StateModel]
    ) -> type[contracts.StateHandler] | None:
        return self._map.get(state_model)


class ContextRegistry(contracts.ContextRegistry):
    def __init__(self):
        self._map = {}

    def register_context(
        self,
        context_model_contract: type[contracts.ContextModel],
        context_collector_contract: type[contracts.ContextCollector]
    ):
        self._map[context_model_contract] = context_collector_contract

    def get_collector(
        self,
        context_model: type[contracts.ContextModel]
    ) -> type[contracts.ContextCollector] | None:
        return self._map.get(context_model)


class MessageRegistry(contracts.MessageRegistry):
    def __init__(self):
        self._map = collections.defaultdict(set)

    def register_message(
        self,
        message_contract: type[contracts.Message],
        actor_contract: type[contracts.Actor],
        context_model_contract: type[contracts.ContextModel] | None = None
    ):
        self._map[message_contract].add((actor_contract, context_model_contract))

    def get_actors_with_context(
        self,
        message_contract: type[contracts.Message]
    ) -> collections.abc.Iterable[tuple[type[contracts.Actor], type[contracts.ContextModel] | None]]:
        for item in self._map.get(self._search_for_contract(message_contract), ()):
            yield item

    def _search_for_contract(self, message_contract) -> type:
        for contract in message_contract.__mro__:
            if contract in self._map:
                return contract
