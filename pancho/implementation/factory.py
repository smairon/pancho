import collections.abc
import typing
from contextlib import asynccontextmanager

from ..definition import contracts
from .processing import CQProcessor


class CQRSFactory:
    def __init__(
        self,
        di_container: contracts.DIContainer,
        actor_registry: contracts.ActorRegistry
    ):
        self._di_container = di_container
        self._actor_registry = actor_registry

    @asynccontextmanager
    async def get_processor(
        self,
        context: collections.abc.Mapping[typing.Any, typing.Any] | None = None
    ):
        async with self._di_container.get_resolver() as di_resolver:
            yield CQProcessor(
                actor_registry=self._actor_registry,
                di_resolver=_add_context(di_resolver, context)
            )


def _add_context(
    di_resolver: contracts.DIResolver,
    context: collections.abc.Mapping[typing.Any, typing.Any] | None
) -> contracts.DIResolver:
    if context:
        for contract, data in context.items() or {}:
            di_resolver.add_context(contract, data)
    return di_resolver
