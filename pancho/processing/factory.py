import functools
from .instance import Processor
from .generic import ProcessorSettings
from ..definitions import contracts
from ..bootstraping.registering import MessageRegistry, StateRegistry, ContextRegistry


class ProcessorFactory(contracts.CommandProcessorFactory):
    def __init__(
        self,
        dependency_registry: contracts.DependencyRegistry,
    ):
        self._dependency_container = dependency_registry.get_container()

    def get_processor(
        self,
        settings: contracts.CommandProcessorSettings = ProcessorSettings()
    ) -> Processor:
        return Processor(
            dependency_container=self._dependency_container,
            message_registry=self._message_registry,
            state_registry=self._state_registry,
            context_registry=self._context_registry,
            settings=settings
        )

    @functools.cached_property
    def _message_registry(self) -> contracts.MessageRegistry:
        dc = self._dependency_container
        mr = MessageRegistry()
        for actor_contract in dc.get_bindings().filter(lambda c, r: contracts.Actor in c.__mro__).keys():
            for message_contract, context_model_contract in actor_contract.__advertising__():
                mr.register_message(
                    message_contract=message_contract,
                    actor_contract=actor_contract,
                    context_model_contract=context_model_contract
                )
        return mr

    @functools.cached_property
    def _state_registry(self) -> contracts.StateRegistry:
        dc = self._dependency_container
        sr = StateRegistry()
        for state_handler_contract in dc.get_bindings().filter(lambda c, r: contracts.StateHandler in c.__mro__).keys():
            for state_model_contract in state_handler_contract.__advertising__() or ():
                sr.register_state(
                    state_model_contract=state_model_contract,
                    state_handler_contract=state_handler_contract
                )
        return sr

    @functools.cached_property
    def _context_registry(self) -> contracts.ContextRegistry:
        dc = self._dependency_container
        cr = ContextRegistry()
        for context_collector_contract in dc.get_bindings().filter(
            lambda c, r: contracts.ContextCollector in c.__mro__
        ).keys():
            for context_model_contract in context_collector_contract.__advertising__():
                cr.register_context(
                    context_model_contract=context_model_contract,
                    context_collector_contract=context_collector_contract
                )
        return cr
