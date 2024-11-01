import dataclasses
import enum
import typing
import uuid
import collections.abc

from zodchy import codex
from zodchy.types import Empty as EmptyType

IdentifierType: typing.TypeAlias = uuid.UUID
NoValueType: typing.TypeAlias = EmptyType
PacketIdType: typing.TypeAlias = IdentifierType
FrameIdType: typing.TypeAlias = IdentifierType
ActorIdType: typing.TypeAlias = int

Message: typing.TypeAlias = codex.cqea.Message
Task: typing.TypeAlias = codex.cqea.Task
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
ExecutionContext: typing.TypeAlias = collections.abc.Mapping[str, typing.Any]


class ActorExecutionKind(enum.Enum):
    SYNC = enum.auto()
    ASYNC = enum.auto()


class ActorSemanticKind(enum.Enum):
    AUDIT = enum.auto()
    USECASE = enum.auto()
    IO = enum.auto()
    CONTEXT = enum.auto()
    RESPONSE = enum.auto()


@dataclasses.dataclass
class ActorParameter:
    name: str
    contract: typing.Any


@dataclasses.dataclass
class ActorDomainParameter(ActorParameter):
    contract: type[Message] | type[Query]


@dataclasses.dataclass
class ActorContextParameter(ActorParameter):
    contract: type[Context]


@dataclasses.dataclass
class ActorDependencyParameter(ActorParameter):
    default: typing.Any


@dataclasses.dataclass
class ActorParameters:
    domain: collections.abc.Sequence[ActorDomainParameter]
    context: collections.abc.Sequence[ActorContextParameter] | None = None
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


class ActorRegistry(typing.Protocol):
    def add(self, actor: ActorContract): ...

    def get(self, contract: type) -> collections.abc.Generator[ActorRegistryEntry, None, None]: ...

    def get_by_id(self, actor_id: int) -> ActorRegistryEntry | None: ...

    def __iter__(self) -> collections.abc.Generator[ActorRegistryEntry, None, None]: ...

    def __add__(self, other: typing.Self) -> typing.Self: ...
