import collections.abc
import dataclasses
import datetime
import typing
import uuid
from collections import deque

from ..definition import contracts, exceptions


@dataclasses.dataclass
class Frame:
    payload: contracts.Message
    context: contracts.Context


@dataclasses.dataclass
class Packet:
    id: uuid.UUID
    trace_id: uuid.UUID
    created_at: datetime.datetime
    payload: contracts.Message


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
    ) -> typing.Generator[contracts.Message, None, None]:
        postponed_actors = set()
        stream = [m async for m in self._loop(message, postponed_actors)]
        for actor_id in postponed_actors:
            await self._execute_actor(self._actor_registry.get_by_id(actor_id), stream)
        return (p.payload for p in stream)

    async def _loop(self, init_message: contracts.Message, postponed_actors: set) -> collections.abc.AsyncGenerator:
        trace_id = uuid.uuid4()
        queue = deque((init_message,))
        while len(queue) > 0:
            message = queue.pop()
            yield self._compile_packet(message, trace_id)
            async for message in self._process_message(message, postponed_actors):
                if isinstance(message, contracts.Error):
                    queue = deque((message,))
                    break
                else:
                    queue.append(message)

    async def _process_message(self, message: contracts.Message, postponed_actors: set):
        for actor_entry in self._actor_registry.get(type(message)):
            if actor_entry.parameters.definitive.is_batch:
                postponed_actors.add(actor_entry.id)
                continue
            output = await self._execute_actor(actor_entry, message)
            if output:
                if isinstance(output, contracts.Error):
                    yield output
                    break
                if actor_entry.semantic_kind == contracts.ActorSemanticKind.AUDIT:
                    message = output
                    continue
                if not isinstance(output, collections.abc.Sequence):
                    output = (output,)
                for item in output:
                    if item is contracts.Message or contracts.Message in type(item).__mro__:
                        yield item
                    else:
                        raise exceptions.CannotProcessActorResult(actor_entry.id)

    async def _execute_actor(
        self,
        actor_entry: contracts.ActorRegistryEntry,
        data: contracts.Message | collections.abc.Iterable[Packet]
    ):
        params = await self._compile_actor_params(actor_entry, data)
        if actor_entry.runtime.kind == contracts.ActorExecutionKind.ASYNC:
            result = await actor_entry.runtime.executable(**params)
        else:
            result = actor_entry.runtime.executable(**params)
        return result

    async def _compile_actor_params(
        self,
        actor_entry: contracts.ActorRegistryEntry,
        data: contracts.Message | collections.abc.Iterable[Packet]
    ):
        _wrapped = actor_entry.parameters.definitive.is_wrapped
        _definitive_name = actor_entry.parameters.definitive.name

        if actor_entry.parameters.definitive.is_batch:
            if not actor_entry.parameters.definitive.is_packed:
                data = (d.payload for d in data)
            data = data or ()
        else:
            data = await self._compile_frame(actor_entry, data) if _wrapped else data

        params = {
            _definitive_name: data
        }

        if actor_entry.parameters.dependencies:
            for dependency_parameter in actor_entry.parameters.dependencies:
                if self._di_resolver:
                    params[dependency_parameter.name] = await self._di_resolver.resolve(dependency_parameter.contract)
                else:
                    if dependency_parameter.default is contracts.NoValueType:
                        raise exceptions.CannotResolveActorParameter(
                            actor_id=actor_entry.id,
                            param_name=dependency_parameter.name
                        )
                    params[dependency_parameter.name] = dependency_parameter.default
        return params

    @staticmethod
    def _compile_packet(
        message: contracts.Message,
        trace_id: uuid.UUID
    ):
        return Packet(
            id=uuid.uuid4(),
            trace_id=trace_id,
            created_at=datetime.datetime.utcnow(),
            payload=message
        )

    async def _compile_frame(
        self,
        actor_entry: contracts.ActorRegistryEntry,
        message: contracts.Message
    ) -> Frame:
        return Frame(
            payload=message,
            context=await self._build_context(actor_entry, message)
        )

    async def _build_context(
        self,
        actor_entry: contracts.ActorRegistryEntry,
        message: contracts.Message
    ) -> contracts.Context | None:
        if actor_entry.parameters.definitive.context:
            for actor_entry in self._actor_registry.get(actor_entry.parameters.definitive.context):
                return await self._execute_actor(
                    actor_entry=actor_entry,
                    data=message
                )
