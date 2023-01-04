import collections.abc
import collections.abc
import datetime
import typing

from ..definitions import contracts

CommandPayload = collections.abc.Mapping
EventContext = collections.abc.Mapping


class MessageProducer:
    def __init__(
        self,
        actor_id: contracts.IdentifierType,
        identifier_factory: contracts.IdentifierFactory
    ):
        self._actor_id = actor_id
        self._identifier_factory = identifier_factory


class EventProducer(MessageProducer):
    def __init__(
        self,
        actor_id: contracts.IdentifierType,
        context: EventContext,
        identifier_factory: contracts.IdentifierFactory
    ):
        self._context = context
        self._registry = []
        super().__init__(actor_id=actor_id, identifier_factory=identifier_factory)

    def bind(
        self,
        event_contract: type[contracts.Event]
    ):
        self._registry.append(event_contract)
        return self

    def get(self):
        for event_contract in self._registry:
            yield event_contract(
                actor_id=self._actor_id,
                created_at=datetime.datetime.utcnow(),
                message='',
                details=self._prepare_context(event_contract)
            )

    def _prepare_context(
        self,
        event_contract: type[contracts.Event]
    ) -> collections.abc.Mapping:
        result = {}
        for field in event_contract.__annotations__.keys():
            result[field] = self._context.get(field)
        return result


class CommandProducer(MessageProducer):
    def __init__(
        self,
        actor_id: contracts.IdentifierType,
        payload: CommandPayload,
        identifier_factory: contracts.IdentifierFactory
    ):
        self._payload = payload
        self._registry = {}
        super().__init__(actor_id=actor_id, identifier_factory=identifier_factory)

    def bind(
        self,
        command_contract: type[contracts.Command],
        clause: typing.Callable[[], bool] | None = None,
        fields_map: collections.abc.Mapping[str, str] | None = None
    ):
        self._registry[command_contract] = (clause, fields_map)
        return self

    def get(self) -> typing.Generator[type[contracts.Command], None, None]:
        for command_contract, settings in self._registry.items():
            clause, fields_map = settings
            if clause and not clause(self._payload):
                continue

            yield command_contract(
                id=self._identifier_factory.produce_message_id(),
                actor_id=self._actor_id,
                created_at=datetime.datetime.utcnow(),
                **self._prepare_payload(command_contract, fields_map)
            )

    def _prepare_payload(
        self,
        command_contract: type[contracts.Command],
        fields_map: collections.abc.Mapping[str, str] | None
    ) -> collections.abc.Mapping:
        fields_map = fields_map or {}
        result = {}
        for field in command_contract.__annotations__.keys():
            field = fields_map.get(field, field)
            if field in self._payload:
                result[field] = self._payload[field]
        return result


class InteractionFactory(contracts.InteractionFactory):
    def __init__(self, identifier_factory: contracts.IdentifierFactory):
        self._identifier_factory = identifier_factory

    def get_command_producer(
        self,
        actor_id: contracts.IdentifierType | None = None,
        payload: collections.abc.Mapping | None = None
    ) -> CommandProducer:
        actor_id = actor_id or self._identifier_factory.produce_actor_id()
        return CommandProducer(
            actor_id=actor_id,
            payload=payload,
            identifier_factory=self._identifier_factory
        )

    def get_event_producer(
        self,
        actor_id: contracts.IdentifierType,
        context: collections.abc.Mapping | None = None
    ) -> EventProducer:
        return EventProducer(
            actor_id=actor_id,
            context=context,
            identifier_factory=self._identifier_factory
        )
