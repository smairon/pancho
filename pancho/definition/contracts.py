import dataclasses
import enum
import typing
import uuid
import collections.abc
import datetime

import zodchy

IdentifierType = uuid.UUID
PacketIdType = IdentifierType
FrameIdType = IdentifierType
ActorIdType = int

NoValueType = zodchy.codex.NoValueType

Message = zodchy.codex.Message

Query = zodchy.codex.Query
Context = zodchy.codex.Context
Command = zodchy.codex.Command

Event = zodchy.codex.Event

Error = zodchy.codex.Error
IOE = zodchy.codex.IOEvent
BDE = zodchy.codex.BDEvent
ResponseEvent = zodchy.codex.ResponseEvent
ReadEvent = zodchy.codex.ReadEvent
WriteEvent = zodchy.codex.WriteEvent

Frame = zodchy.codex.Frame

P = typing.TypeVar('P', bound=Message)


class Packet(typing.Generic[P]):
    id: uuid.UUID
    trace_id: uuid.UUID
    created_at: datetime.datetime
    payload: P


DIContainer = zodchy.codex.DIContainerContract
DIResolver = zodchy.codex.DIResolverContract
IdentifiersFactory = zodchy.codex.IdentifiersFactory

ActorContract = collections.abc.Callable


class ActorExecutionKind(enum.Enum):
    SYNC = enum.auto()
    ASYNC = enum.auto()


class ActorSemanticKind(enum.Enum):
    DOMAIN = enum.auto()
    WRITE = enum.auto()
    CONTEXT = enum.auto()
    READ = enum.auto()
    AUDIT = enum.auto()
    RESPONSE = enum.auto()


@dataclasses.dataclass
class ActorParameter:
    name: str
    contract: typing.Any


@dataclasses.dataclass
class ActorDefinitiveParameter(ActorParameter):
    contract: type[Message] | type[Query]
    context: type[Context] | None = None
    is_batch: bool = False
    is_wrapped: bool = False
    is_packed: bool = False


@dataclasses.dataclass
class ActorDependencyParameter(ActorParameter):
    default: typing.Any


@dataclasses.dataclass
class ActorParameters:
    definitive: ActorDefinitiveParameter
    dependencies: collections.abc.Sequence[ActorDependencyParameter] | None = None


@dataclasses.dataclass
class ActorRuntime:
    executable: collections.abc.Callable
    kind: ActorExecutionKind


@dataclasses.dataclass
class ActorRegistryEntry:
    id: ActorIdType
    semantic_kind: ActorSemanticKind
    parameters: ActorParameters
    return_annotation: typing.Any
    runtime: ActorRuntime


class ActorRegistry:
    def add(self, actor: ActorContract): ...

    def get(self, contract: type) -> collections.abc.Generator[ActorRegistryEntry, None, None]: ...

    def get_by_id(self, actor_id: int) -> ActorRegistryEntry | None: ...

    def __iter__(self) -> collections.abc.Generator[ActorRegistryEntry, None, None]: ...

    def __add__(self, other: typing.Self) -> typing.Self: ...
