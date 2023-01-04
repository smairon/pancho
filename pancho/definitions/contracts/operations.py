import typing
import collections.abc
import dataclasses

from .interaction import Message
from .context import ContextModel
from .state import StateModel


@dataclasses.dataclass
class ActorInternals:
    message_handler_map: dict = dataclasses.field(default_factory=dict)
    message_context_map: dict = dataclasses.field(default_factory=dict)


@typing.runtime_checkable
class Actor(typing.Protocol):
    def __receive__(
        self,
        message: Message,
        context: ContextModel | None = None
    ) -> collections.abc.Iterable[Message] | None: ...

    def __state__(self) -> StateModel | None: ...

    @classmethod
    def __advertising__(cls) -> typing.Iterable[
        tuple[type[Message] | type[ContextModel]]
    ]: ...
