import dataclasses
import enum
import typing
import uuid
import collections.abc
import datetime

import zodchy

IdentifierType = uuid.UUID
NoValueType = zodchy.types.Empty
PacketIdType = IdentifierType
FrameIdType = IdentifierType
ActorIdType = int

Message = zodchy.codex.cqea.Message
Query = zodchy.codex.cqea.Query
Context = zodchy.codex.cqea.Context
Command = zodchy.codex.cqea.Command
Event = zodchy.codex.cqea.Event
Error = zodchy.codex.cqea.Error
IOE = zodchy.codex.cqea.IOEvent
BDE = zodchy.codex.cqea.BDEvent
ResponseEvent = zodchy.codex.cqea.ResponseEvent
ReadEvent = zodchy.codex.cqea.ReadEvent
WriteEvent = zodchy.codex.cqea.WriteEvent
Frame = zodchy.codex.cqea.Frame

P = typing.TypeVar('P', bound=Message)


class Packet(typing.Generic[P]):
    id: uuid.UUID
    trace_id: uuid.UUID
    created_at: datetime.datetime
    payload: P


DIContainer = zodchy.codex.di.DIContainerContract
DIResolver = zodchy.codex.di.DIResolverContract
IdentifiersFactory = zodchy.codex.identity.IdentifiersFactory

ActorContract = zodchy.codex.cqea.Actor


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
