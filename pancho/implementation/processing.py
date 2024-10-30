import collections.abc
import dataclasses
import typing
import heapq
import itertools
from os import write

import zorge

from ..definition import contracts, exceptions


@dataclasses.dataclass
class Job:
    actor_entry: contracts.ActorRegistryEntry
    parameters: collections.abc.Mapping[str, contracts.Message]


class Loop:
    _SEMANTIC_PRIORITY = {
        contracts.ActorSemanticKind.CONTEXT: 0,
        contracts.ActorSemanticKind.AUDIT: 1,
        contracts.ActorSemanticKind.USECASE: 2,
        contracts.ActorSemanticKind.IO: 3,
        contracts.ActorSemanticKind.RESPONSE: 9
    }

    def __init__(
        self,
        actor_registry: contracts.ActorRegistry
    ):
        self._queue = []
        self._actor_registry = actor_registry
        self._stream = {}

    def register(self, message: contracts.Message):
        if (key := message.__class__.__name__) not in self._stream:
            self._stream[key] = message
            self._register_job(message)

    def _register_job(self, message: contracts.Message):
        is_context = isinstance(message, contracts.Context)
        for actor_entry in self._actor_registry.get(message.__class__):
            if is_context and actor_entry.semantic_kind == contracts.ActorSemanticKind.CONTEXT:
                continue
            for context_parameter in actor_entry.parameters.context or ():
                self._register_context_job(context_parameter.contract)
            self._enqueue_job(actor_entry)

    def _register_context_job(self, contract: type[contracts.Context]):
        if contract.__name__ in self._stream:
            return
        for actor_entry in self._actor_registry.get(contract):
            if actor_entry.semantic_kind == contracts.ActorSemanticKind.CONTEXT:
                self._enqueue_job(actor_entry)

    def _enqueue_job(self, actor_entry: contracts.ActorRegistryEntry):
        if (parameters := self._build_parameters(actor_entry)) is not None:
            heapq.heappush(
                self._queue,
                (
                    self._SEMANTIC_PRIORITY[actor_entry.semantic_kind],
                    Job(
                        actor_entry=actor_entry,
                        parameters=parameters
                    )
                )
            )

    def _build_parameters(
        self,
        actor_entry: contracts.ActorRegistryEntry,
    ):
        parameters = {}
        for p in itertools.chain(actor_entry.parameters.domain, actor_entry.parameters.context or ()):
            if p.contract.__name__ not in self._stream:
                return
            parameters[p.name] = self._stream[p.contract.__name__]
        return parameters

    async def __aiter__(self):
        while self._queue:
            yield heapq.heappop(self._queue)[1]


class CQProcessor:
    def __init__(
        self,
        actor_registry: contracts.ActorRegistry,
        di_resolver: contracts.DIResolver | None = None
    ):
        self._actor_registry = actor_registry
        self._di_resolver = di_resolver

    async def __call__(
        self,
        message: contracts.Message
    ) -> typing.AsyncGenerator[contracts.Message, None]:
        loop = Loop(self._actor_registry)
        loop.register(message)
        async for job in loop:
            for message in await self._run_job(job):
                yield message
                if isinstance(message, contracts.Error):
                    return
                loop.register(message)

    async def _run_job(self, job: Job):
        params = {
            **job.parameters,
            **await self._compile_dependency_parameters(job)
        }
        if job.actor_entry.runtime.kind == contracts.ActorExecutionKind.ASYNC:
            result = await job.actor_entry.runtime.executable(**params)
        else:
            result = job.actor_entry.runtime.executable(**params)
        if not isinstance(result, collections.abc.Iterable):
            if result is None:
                result = ()
            elif isinstance(result, contracts.Message):
                result = (result,)
            else:
                raise ValueError(
                    f'Unexpected result type for actor {job.actor_entry.runtime.executable.__name__}: {type(result)}'
                )
        return result

    async def _compile_dependency_parameters(self, job: Job):
        params = {}
        if job.actor_entry.parameters.dependencies:
            for dependency_parameter in job.actor_entry.parameters.dependencies:
                if self._di_resolver:
                    params[dependency_parameter.name] = await self._di_resolver.resolve(dependency_parameter.contract)
                else:
                    if dependency_parameter.default is contracts.NoValueType:
                        raise exceptions.CannotResolveActorParameter(
                            actor_id=job.actor_entry.id,
                            param_name=dependency_parameter.name
                        )
                    params[dependency_parameter.name] = dependency_parameter.default
        return params


