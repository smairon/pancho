import collections.abc
import itertools
import typing
import inspect
import dataclasses
import enum
from types import ModuleType

import zodchy

from ..definition import exceptions

ActorIdType: typing.TypeAlias = int
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
    contract: type[zodchy.codex.cqea.Message]


@dataclasses.dataclass
class ActorContextParameter(ActorParameter):
    contract: type[zodchy.codex.cqea.Context]


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


class ActorRegistry:
    def __init__(self):
        self._actors = {}
        self._contract_actor_map = collections.defaultdict(list)

    def add(
        self,
        actor: zodchy.codex.cqea.Actor
    ):
        if actor_entry := self._actor_entry(actor):
            self._register_entry(actor_entry)

    def get(
        self,
        contract: type
    ) -> collections.abc.Generator[ActorRegistryEntry, None, None]:
        chain = contract.__mro__ if hasattr(contract, '__mro__') else (contract,)
        for contract in chain:
            for entry_id in self._contract_actor_map.get(contract) or ():
                yield self._actors.get(entry_id)

    def get_by_id(
        self,
        actor_id: int
    ) -> ActorRegistryEntry | None:
        return self._actors.get(actor_id)

    def __iter__(self):
        for entry in self._actors.values():
            yield entry

    def __add__(self, other: typing.Self):
        for entry in other:
            self._register_entry(entry)
        return self

    def _register_entry(
        self,
        entry: ActorRegistryEntry
    ):
        self._actors[entry.id] = entry
        if entry.semantic_kind == ActorSemanticKind.CONTEXT:
            self._contract_actor_map[entry.return_annotation].append(entry.id)
        else:
            for parameter in itertools.chain(entry.parameters.domain, entry.parameters.context or ()):
                self._contract_actor_map[parameter.contract].append(entry.id)

    def _actor_entry(
        self,
        actor: zodchy.codex.cqea.Actor
    ) -> ActorRegistryEntry | None:
        semantic_kind = self._derive_semantic_kind(actor=actor)
        if semantic_kind is None:
            return
        signature = inspect.signature(actor)
        parameters = self._derive_parameters(signature)
        return_annotation = signature.return_annotation
        return ActorRegistryEntry(
            id=id(actor),
            parameters=parameters,
            return_annotation=return_annotation,
            semantic_kind=semantic_kind,
            runtime=ActorRuntime(
                executable=self._derive_executable(actor),
                kind=self._derive_execution_kind(actor)
            )
        )

    @staticmethod
    def _derive_semantic_kind(
        actor: zodchy.codex.cqea.Actor,
    ) -> ActorSemanticKind | None:
        _map = {
            'io': ActorSemanticKind.IO,
            'reader': ActorSemanticKind.IO,
            'writer': ActorSemanticKind.IO,
            'auditor': ActorSemanticKind.AUDIT,
            'usecase': ActorSemanticKind.USECASE,
            'context': ActorSemanticKind.CONTEXT,
            'response': ActorSemanticKind.RESPONSE,
            'skip': None
        }
        if '__semantic__' not in actor.__dict__:
            for item in _map.keys():
                if actor.__name__.endswith(f'_{item}'):
                    actor.__dict__['__semantic__'] = item
                    break
            else:
                return
        return _map[actor.__dict__['__semantic__']]

    @staticmethod
    def _derive_execution_kind(
        actor: zodchy.codex.cqea.Actor
    ) -> ActorExecutionKind:
        execution_type = ActorExecutionKind.SYNC
        if inspect.iscoroutinefunction(actor):
            execution_type = ActorExecutionKind.ASYNC

        return execution_type

    @staticmethod
    def _derive_executable(
        actor: zodchy.codex.cqea.Actor
    ):
        if inspect.isfunction(actor):
            return actor
        elif hasattr(actor, '__call__'):
            return actor.__call__

    def _derive_parameters(
        self,
        signature: inspect.Signature
    ) -> ActorParameters:
        domain = []
        dependencies = []
        context = []
        for parameter in signature.parameters.values():
            actor_parameter = self._derive_parameter(parameter)
            if isinstance(actor_parameter, ActorDomainParameter):
                domain.append(actor_parameter)
            if isinstance(actor_parameter, ActorContextParameter):
                context.append(actor_parameter)
            elif isinstance(actor_parameter, ActorDependencyParameter):
                dependencies.append(actor_parameter)
        if not domain:
            raise exceptions.CannotDefineActorParameter(signature)
        return ActorParameters(
            domain=domain,
            context=context or None,
            dependencies=dependencies or None
        )

    @staticmethod
    def _derive_parameter(parameter: inspect.Parameter) -> ActorParameter:
        _types_chain = _evoke_types_chain(parameter.annotation)
        if contract := _search_contract(_types_chain, zodchy.codex.cqea.Task, zodchy.codex.cqea.Event):
            return ActorDomainParameter(
                name=parameter.name,
                contract=contract
            )
        elif contract := _search_contract(_types_chain, zodchy.codex.cqea.Context):
            return ActorContextParameter(
                name=parameter.name,
                contract=contract
            )
        else:
            return ActorDependencyParameter(
                name=parameter.name,
                contract=parameter.annotation,
                default=zodchy.types.Empty if parameter.default is inspect.Parameter.empty else parameter.default
            )


def _evoke_types_chain(annotation):
    _origin = typing.get_origin(annotation)
    if not _origin:
        return zodchy.types.Empty if annotation is inspect.Parameter.empty else annotation
    else:
        args = typing.get_args(annotation)
        chain = [_origin]
        if len(args) == 1:
            r = _evoke_types_chain(args[0])
            if isinstance(r, collections.abc.Sequence):
                chain.extend(r)
            else:
                chain.append(r)
        else:
            chain.append(tuple(_evoke_types_chain(arg) for arg in args))
    return chain


def _search_contract(
    haystack: collections.abc.Sequence | type,
    *needles: type
) -> typing.Any:
    haystack = haystack if isinstance(haystack, collections.abc.Sequence) else (haystack,)
    if collections.abc.Callable in haystack:
        return
    for element in haystack:
        if isinstance(element, collections.abc.Sequence):
            if result := _search_contract(element, *needles):
                return result
        else:
            if any(
                needle is element or
                (hasattr(element, '__mro__') and needle in element.__mro__)
                for needle in needles
            ):
                return element


def register_module(
    registry: ActorRegistry,
    module: ModuleType
) -> ActorRegistry:
    for e in inspect.getmembers(module):
        entity = e[1]
        if inspect.ismodule(entity) and module.__name__ in entity.__name__:
            register_module(registry, entity)
        elif inspect.isfunction(entity) and not entity.__name__.startswith('_'):
            registry.add(entity)
    return registry
