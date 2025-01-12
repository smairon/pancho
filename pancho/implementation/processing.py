import collections.abc
import dataclasses
import typing
import heapq
import itertools

import zodchy

from ..definition import exceptions
from . import registry


@dataclasses.dataclass(order=True)
class Job:
    priority: int
    actor_entry: registry.ActorRegistryEntry
    parameters: collections.abc.Mapping[str, str]


class Stream:
    def __init__(self):
        self._stream = {}

    def insert(self, message: zodchy.codex.cqea.Message) -> bool:
        if (key := self._key(message)) not in self._stream:
            self._stream[key] = message
            return True
        else:
            return False

    def replace(self, message: zodchy.codex.cqea.Message):
        self._stream[self._key(message)] = message

    @staticmethod
    def _key(message: zodchy.codex.cqea.Message):
        return message.__class__.__name__

    def __contains__(self, item: str) -> bool:
        return item in self._stream

    def __getitem__(self, item: str) -> zodchy.codex.cqea.Message:
        return self._stream[item]


class Loop:
    _SEMANTIC_PRIORITY = {
        registry.ActorSemanticKind.CONTEXT: 0,
        registry.ActorSemanticKind.AUDIT: 1,
        registry.ActorSemanticKind.USECASE: 2,
        registry.ActorSemanticKind.IO: 3,
        registry.ActorSemanticKind.RESPONSE: 9,
    }

    def __init__(
        self,
        actor_registry: registry.ActorRegistry,
        stream: Stream
    ):
        self._queue = []
        self._actor_registry = actor_registry
        self._stream = stream
        self._jobs_sequence = 0

    def register(self, message: zodchy.codex.cqea.Message, replace: bool = False):
        if replace:
            self._stream.replace(message)
        elif self._stream.insert(message):
            self._register_job(message)

    def _register_job(self, message: zodchy.codex.cqea.Message):
        is_context = isinstance(message, zodchy.codex.cqea.Context)
        for actor_entry in self._actor_registry.get(message.__class__):
            if (
                is_context
                and actor_entry.semantic_kind == registry.ActorSemanticKind.CONTEXT
            ):
                continue
            for context_parameter in actor_entry.parameters.context or ():
                self._register_context_job(context_parameter.contract)
            self._enqueue_job(actor_entry)

    def _register_context_job(self, contract: type[zodchy.codex.cqea.Context]):
        if contract.__name__ in self._stream:
            return
        for actor_entry in self._actor_registry.get(contract):
            if actor_entry.semantic_kind == registry.ActorSemanticKind.CONTEXT:
                self._enqueue_job(actor_entry)

    def _enqueue_job(self, actor_entry: registry.ActorRegistryEntry):
        if (parameters := self._build_parameters(actor_entry)) is not None:
            self._jobs_sequence += 1
            heapq.heappush(
                self._queue,
                (
                    self._SEMANTIC_PRIORITY[actor_entry.semantic_kind],
                    Job(
                        priority=self._jobs_sequence,  # just for order jobs with the same semantic priority
                        actor_entry=actor_entry,
                        parameters=parameters,
                    ),
                ),
            )

    def _build_parameters(
        self,
        actor_entry: registry.ActorRegistryEntry,
    ):
        parameters = {}
        for p in itertools.chain(
            actor_entry.parameters.domain, actor_entry.parameters.context or ()
        ):
            if p.contract.__name__ not in self._stream:
                return
            parameters[p.name] = p.contract.__name__
        return parameters

    async def __aiter__(self):
        while self._queue:
            yield heapq.heappop(self._queue)[1]


class CQProcessor:
    def __init__(
        self,
        actor_registry: registry.ActorRegistry,
        di_resolver: zodchy.codex.di.DIResolverContract | None = None,
    ):
        self._actor_registry = actor_registry
        self._di_resolver = di_resolver

    async def __call__(
        self, message: zodchy.codex.cqea.Message
    ) -> typing.AsyncGenerator[zodchy.codex.cqea.Message, None]:
        stream = Stream()
        loop = Loop(self._actor_registry, stream)
        loop.register(message)
        async for job in loop:
            for message in await self._run_job(job, stream):
                yield message
                if isinstance(message, zodchy.codex.cqea.Error):
                    return
                loop.register(
                    message,
                    replace=job.actor_entry.semantic_kind
                            == registry.ActorSemanticKind.AUDIT,
                )

    async def _run_job(self, job: Job, stream: Stream):
        params = {
            **{k: stream[v] for k, v in job.parameters.items()},
            **await self._compile_dependency_parameters(job),
        }
        if job.actor_entry.runtime.kind == registry.ActorExecutionKind.ASYNC:
            result = await job.actor_entry.runtime.executable(**params)
        else:
            result = job.actor_entry.runtime.executable(**params)

        if result is None:
            result =()
        elif isinstance(result, zodchy.codex.cqea.Message):
            result = (result,)
        elif not isinstance(result, collections.abc.Iterable):
            raise ValueError(
                f"Unexpected result type for actor {job.actor_entry.runtime.executable.__name__}: {type(result)}"
            )

        return result

    async def _compile_dependency_parameters(self, job: Job):
        params = {}
        if job.actor_entry.parameters.dependencies:
            for dependency_parameter in job.actor_entry.parameters.dependencies:
                if self._di_resolver:
                    params[dependency_parameter.name] = await self._di_resolver.resolve(
                        dependency_parameter.contract
                    )
                else:
                    if dependency_parameter.default is zodchy.types.Empty:
                        raise exceptions.CannotResolveActorParameter(
                            actor_id=job.actor_entry.id,
                            param_name=dependency_parameter.name,
                        )
                    params[dependency_parameter.name] = dependency_parameter.default
        return params
