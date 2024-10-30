import collections.abc
import itertools
import typing
import inspect
import types

from ..definition import contracts, exceptions


def register_module(
    registry: contracts.ActorRegistry,
    module: types.ModuleType
) -> contracts.ActorRegistry:
    for e in inspect.getmembers(module):
        entity = e[1]
        if inspect.ismodule(entity) and module.__name__ in entity.__name__:
            register_module(registry, entity)
        elif inspect.isfunction(entity) and not entity.__name__.startswith('_'):
            registry.add(entity)
    return registry


class ActorRegistry:
    def __init__(self):
        self._actors = {}
        self._contract_actor_map = collections.defaultdict(list)

    def add(
        self,
        actor: contracts.ActorContract
    ):
        if actor_entry := self._actor_entry(actor):
            self._register_entry(actor_entry)

    def get(
        self,
        contract: type
    ) -> collections.abc.Generator[contracts.ActorRegistryEntry, None, None]:
        chain = contract.__mro__ if hasattr(contract, '__mro__') else (contract,)
        for contract in chain:
            for entry_id in self._contract_actor_map.get(contract) or ():
                yield self._actors.get(entry_id)

    def get_by_id(
        self,
        actor_id: int
    ) -> contracts.ActorRegistryEntry | None:
        return self._actors.get(actor_id)

    def __iter__(self):
        for entry in self._actors.values():
            yield entry

    def __add__(self, other: contracts.ActorRegistry):
        for entry in other:
            self._register_entry(entry)
        return self

    def _register_entry(
        self,
        entry: contracts.ActorRegistryEntry
    ):
        self._actors[entry.id] = entry
        if entry.semantic_kind == contracts.ActorSemanticKind.CONTEXT:
            self._contract_actor_map[entry.return_annotation].append(entry.id)
        else:
            for parameter in itertools.chain(entry.parameters.domain, entry.parameters.context or ()):
                self._contract_actor_map[parameter.contract].append(entry.id)

    def _actor_entry(
        self,
        actor: contracts.ActorContract
    ) -> contracts.ActorRegistryEntry | None:
        semantic_kind = self._derive_semantic_kind(actor=actor)
        if semantic_kind is None:
            return
        signature = inspect.signature(actor)
        parameters = self._derive_parameters(signature)
        return_annotation = signature.return_annotation
        return contracts.ActorRegistryEntry(
            id=id(actor),
            parameters=parameters,
            return_annotation=return_annotation,
            semantic_kind=semantic_kind,
            runtime=contracts.ActorRuntime(
                executable=self._derive_executable(actor),
                kind=self._derive_execution_kind(actor)
            )
        )

    @staticmethod
    def _derive_semantic_kind(
        actor: contracts.ActorContract,
    ) -> contracts.ActorSemanticKind | None:
        _map = {
            'io': contracts.ActorSemanticKind.IO,
            'reader': contracts.ActorSemanticKind.IO,
            'writer': contracts.ActorSemanticKind.IO,
            'auditor': contracts.ActorSemanticKind.AUDIT,
            'usecase': contracts.ActorSemanticKind.USECASE,
            'context': contracts.ActorSemanticKind.CONTEXT,
            'response': contracts.ActorSemanticKind.RESPONSE,
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
        actor: contracts.ActorContract
    ) -> contracts.ActorExecutionKind:
        execution_type = contracts.ActorExecutionKind.SYNC
        if inspect.iscoroutinefunction(actor):
            execution_type = contracts.ActorExecutionKind.ASYNC

        return execution_type

    @staticmethod
    def _derive_executable(
        actor: contracts.ActorContract
    ):
        if inspect.isfunction(actor):
            return actor
        elif hasattr(actor, '__call__'):
            return actor.__call__

    def _derive_parameters(
        self,
        signature: inspect.Signature
    ) -> contracts.ActorParameters:
        domain = []
        dependencies = []
        context = []
        for parameter in signature.parameters.values():
            actor_parameter = self._derive_parameter(parameter)
            if isinstance(actor_parameter, contracts.ActorDomainParameter):
                domain.append(actor_parameter)
            if isinstance(actor_parameter, contracts.ActorContextParameter):
                context.append(actor_parameter)
            elif isinstance(actor_parameter, contracts.ActorDependencyParameter):
                dependencies.append(actor_parameter)
        if not domain:
            raise exceptions.CannotDefineActorParameter(signature)
        return contracts.ActorParameters(
            domain=domain,
            context=context or None,
            dependencies=dependencies or None
        )

    @staticmethod
    def _derive_parameter(parameter: inspect.Parameter) -> contracts.ActorParameter:
        _types_chain = _evoke_types_chain(parameter.annotation)
        if contract := _search_contract(_types_chain, contracts.Task, contracts.Event):
            return contracts.ActorDomainParameter(
                name=parameter.name,
                contract=contract
            )
        elif contract := _search_contract(_types_chain, contracts.Context):
            return contracts.ActorContextParameter(
                name=parameter.name,
                contract=contract
            )
        else:
            return contracts.ActorDependencyParameter(
                name=parameter.name,
                contract=parameter.annotation,
                default=contracts.NoValueType if parameter.default is inspect.Parameter.empty else parameter.default
            )


def _evoke_types_chain(annotation):
    _origin = typing.get_origin(annotation)
    if not _origin:
        return contracts.NoValueType if annotation is inspect.Parameter.empty else annotation
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
