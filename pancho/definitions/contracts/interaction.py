import collections.abc
import typing
import datetime
import pydantic
import dataclasses

from .identity import IdentifierType
from .state import StateScope


class Message(pydantic.BaseModel):
    created_at: datetime.datetime = pydantic.Field(default_factory=datetime.datetime.utcnow)


class Command(Message):
    launch_at: datetime.datetime | None = pydantic.Field(default=None)


class Event(Message):
    state_id: IdentifierType


class InfoEvent(Event):
    context: dict | None = pydantic.Field(default=None)


class ExceptionContext(pydantic.BaseModel):
    code: int
    message: str
    details: list | None = pydantic.Field(default=None)


class ExceptionEvent(Event):
    context: ExceptionContext


class CommandProducer(typing.Protocol):
    def bind(
        self,
        command_contract: type[Command],
        clause: typing.Callable[[], bool] | None = None,
        fields_map: collections.abc.Mapping[str, str] | None = None
    ): ...

    def get(self) -> typing.Generator[type[Command], None, None]: ...


class EventProducer(typing.Protocol):
    def bind(
        self,
        event_contract: type[Event]
    ): ...

    def get(self) -> typing.Generator[type[Event], None, None]: ...


class InteractionFactory(typing.Protocol):
    def get_command_producer(
        self,
        actor_id: IdentifierType | None = None,
        payload: collections.abc.Mapping | None = None
    ) -> CommandProducer: ...

    def get_event_producer(
        self,
        actor_id: IdentifierType,
        context: collections.abc.Mapping | None = None
    ) -> EventProducer: ...


@dataclasses.dataclass
class MessageFrame:
    message: Message
    state_scope: StateScope | None = None


class MessageQueue(typing.Protocol):
    def enqueue(
        self,
        data: MessageFrame | collections.abc.Iterable[MessageFrame]
    ) -> typing.NoReturn:
        ...

    def dequeue(
        self
    ) -> MessageFrame | None:
        ...


MessageStreamType = typing.Iterable[Message]
