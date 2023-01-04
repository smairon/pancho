import collections.abc
import typing

from .identity import IdentifierType
from .interaction import Message, Command, MessageStreamType
from .operations import Actor
from .state import StateModel

MessageActorMap = collections.abc.MutableMapping[
    type[Message],
    set[tuple[type[Actor], type[StateModel] | None]]
]


class CommandProcessor(typing.Protocol):
    async def __aenter__(self) -> 'CommandProcessor': ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    async def receive(self, command: Command, scope: collections.abc.Sequence[IdentifierType] | IdentifierType): ...

    def get_message_stream(self) -> MessageStreamType: ...

    async def commit(self): ...

    async def shutdown(self): ...


class CommandProcessorSettings(typing.Protocol):
    register_events: bool = True
    auto_commit: bool = True


class CommandProcessorFactory(typing.Protocol):
    def get_processor(
        self,
        settings: CommandProcessorSettings
    ) -> CommandProcessor: ...
