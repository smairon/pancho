import dataclasses
import enum
import typing
import uuid
import collections.abc
import datetime

from zodchy import codex
from zodchy.types import Empty as EmptyType

IdentifierType: typing.TypeAlias = uuid.UUID
NoValueType: typing.TypeAlias = EmptyType
PacketIdType: typing.TypeAlias = IdentifierType
FrameIdType: typing.TypeAlias = IdentifierType
ActorIdType: typing.TypeAlias = int

Message: typing.TypeAlias = codex.cqea.Message
Query: typing.TypeAlias = codex.cqea.Query
Context: typing.TypeAlias = codex.cqea.Context
Command: typing.TypeAlias = codex.cqea.Command
Event: typing.TypeAlias = codex.cqea.Event
Error: typing.TypeAlias = codex.cqea.Error
IOE: typing.TypeAlias = codex.cqea.IOEvent
BDE: typing.TypeAlias = codex.cqea.BDEvent
ResponseEvent: typing.TypeAlias = codex.cqea.ResponseEvent
ReadEvent: typing.TypeAlias = codex.cqea.ReadEvent
WriteEvent: typing.TypeAlias = codex.cqea.WriteEvent
Frame: typing.TypeAlias = codex.cqea.Frame
DIContainer: typing.TypeAlias = codex.di.DIContainerContract
DIResolver: typing.TypeAlias = codex.di.DIResolverContract
IdentifiersFactory: typing.TypeAlias = codex.identity.IdentifiersFactory
ActorContract: typing.TypeAlias = codex.cqea.Actor

P = typing.TypeVar('P', bound=Message)


class Packet(typing.Generic[P]):
    id: uuid.UUID
    trace_id: uuid.UUID
    created_at: datetime.datetime
    payload: P


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
