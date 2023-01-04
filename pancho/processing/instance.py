import collections.abc
import functools
import typing

import zorge.contracts
from zorge.contracts import DependencyContainer
from pancho.definitions import contracts, exceptions
from .generic import MessageQueue
from ..exploration import search_for_subtype


class ActorIdentityMap:
    def __init__(self):
        self._actors = collections.defaultdict(dict)

    def register(
        self,
        state_id: contracts.IdentifierType,
        instance: contracts.Actor
    ):
        self._actors[instance.__class__.__name__][state_id] = instance

    def get_one(
        self,
        contract: type[contracts.Actor],
        state_id: contracts.IdentifierType
    ) -> contracts.Actor | None:
        return self._actors.get(contract.__name__, {}).get(state_id)

    def get_all(self) -> dict[str, dict[contracts.IdentifierType, contracts.Actor]]:
        return self._actors


class Processor(contracts.CommandProcessor):
    def __init__(
        self,
        dependency_container: DependencyContainer,
        message_registry: contracts.MessageRegistry,
        context_registry: contracts.ContextRegistry,
        state_registry: contracts.StateRegistry,
        settings: contracts.CommandProcessorSettings
    ):
        self._dependency_container = dependency_container
        self._message_registry = message_registry
        self._context_registry = context_registry
        self._state_registry = state_registry
        self._settings = settings

    async def __aenter__(self) -> 'Processor':
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._settings.auto_commit and not exc_type:
            await self.commit()

        await self._dependency_provider.shutdown(exc_type)

    def get_message_stream(self) -> contracts.MessageStreamType:
        return self._message_queue.get_stream()

    async def receive(
        self,
        command: contracts.Command,
        state_scope: contracts.StateScope
    ):
        self._message_queue.enqueue(
            contracts.MessageFrame(
                message=command,
                state_scope=state_scope if isinstance(state_scope, collections.abc.Sequence) else (state_scope,)
            )
        )
        while message_frame := self._message_queue.dequeue():
            _message = message_frame.message
            _state_scope = message_frame.state_scope or (None,)
            for actor_contract, message_context_contract in self._message_registry.get_actors_with_context(
                type(_message)
            ):
                context = await self._load_context(
                    context_model_contract=message_context_contract,
                    state_scope=_state_scope,
                    message=_message
                )

                for state_id in _state_scope:
                    for event in self._process_message(
                        actor=await self._get_actor(
                            contract=actor_contract,
                            state_id=state_id
                        ),
                        context=context,
                        message=_message,
                        state_id=state_id
                    ) or ():
                        self._message_queue.enqueue(
                            contracts.MessageFrame(message=event, state_scope=(state_id,))
                        )

    async def commit(self):
        for actors in self._actor_identity_map.get_all().values():
            state = []
            for actor in actors.values():
                state.append(actor.__state__())
            await self._keep_state(state)

    async def shutdown(self, exc_type: typing.Any | None = None):
        await self._dependency_provider.shutdown(exc_type)

    async def _get_actor(
        self,
        contract: type[contracts.Actor],
        state_id: contracts.IdentifierType | None = None
    ) -> contracts.Actor:
        actor = self._actor_identity_map.get_one(contract, state_id)
        if not actor:
            params = {}
            for k, v in contract.__init__.__annotations__.items():
                if search_for_subtype(v, contracts.IdentifierType):
                    params[k] = state_id
                    break
            try:
                actor = contract(**params)
            except Exception as e:
                raise exceptions.ActorInitializationException(contract=contract) from e
            self._actor_identity_map.register(state_id, actor)
        return actor

    @staticmethod
    def _process_message(
        actor: contracts.Actor,
        message: contracts.Message,
        state_id: contracts.IdentifierType,
        context: contracts.ContextModel
    ):
        try:
            return actor.__receive__(
                message=message,
                context=context.get(state_id) if isinstance(context, collections.abc.Mapping) else context
            )
        except Exception as e:
            raise exceptions.ActorMessageProcessingException(type(actor)) from e

    async def _keep_state(
        self,
        state: contracts.StateDataType
    ) -> typing.NoReturn:
        if not state:
            return

        state_model_contract = type(state)
        if isinstance(state, collections.abc.Sequence):
            state_model_contract = type(state[0])

        keeper_contract = self._state_registry.get_handler(state_model_contract)
        if not keeper_contract:
            return

        try:
            keeper = await self._dependency_provider.resolve(keeper_contract)
        except Exception as e:
            raise exceptions.DependencyException(contract=keeper_contract) from e

        try:
            await keeper(state)
        except Exception as e:
            raise exceptions.CommitStateException(contract=keeper_contract) from e

    async def _load_context(
        self,
        context_model_contract: type[contracts.ContextModel],
        state_scope: contracts.StateScope,
        message: contracts.Message
    ) -> contracts.StateDataType | None:
        if not context_model_contract:
            return

        collector_contract = self._context_registry.get_collector(context_model_contract)
        if not collector_contract:
            return

        try:
            collector = await self._dependency_provider.resolve(collector_contract)
        except Exception as e:
            raise exceptions.DependencyException(contract=collector_contract) from e

        try:
            return await collector(context_model_contract, state_scope, message)
        except Exception as e:
            raise exceptions.LoadContextException(contract=type(message)) from e

    @functools.cached_property
    def _dependency_provider(self) -> zorge.contracts.DependencyProvider:
        return self._dependency_container.get_provider()

    @functools.cached_property
    def _message_queue(self) -> MessageQueue:
        return MessageQueue()

    @functools.cached_property
    def _actor_identity_map(self):
        return ActorIdentityMap()
