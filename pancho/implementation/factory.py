import collections.abc
import typing
from contextlib import asynccontextmanager

from .processing import CQProcessor
from ..definition import contracts


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
        async with self._di_container.get_resolver(context) as di_resolver:
            yield CQProcessor(
                actor_registry=self._actor_registry,
                di_resolver=di_resolver
            )
