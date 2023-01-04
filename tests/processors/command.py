import asyncio
import collections.abc

import datetime
import typing
import uuid

from tacitus.adapters.sqlalchemy.vendoring import SqlAlchemyVendor
from tacitus.adapters.sqlalchemy.registration import Registry
from tacitus.definitions.contracts import DataVendorConnection, DataFrameRegistry
from tacitus.definitions.contracts import Node, Field, Query
from tacitus.adapters.sqlalchemy.connecting import SqlalchemyConnectionPool
from pancho.bootstraping.registering import DependencyRegistry
from pancho.definitions import contracts, exceptions
from pancho.operations import Actor
from pancho.processing import CommandProcessorFactory
from pancho.state import StateKeeper
from pancho.context import ContextCollector
from ext.schema import db_metadata


class DefaultDataVendor(SqlAlchemyVendor):
    pass


class MaterialState(contracts.StateModel):
    id: contracts.IdentifierType
    status: int | None
    caption: str | None
    author_id: contracts.IdentifierType | None
    published_at: datetime.datetime | None
    preview: str | None
    body: str | None
    cover_url: str | None
    tags: list[contracts.IdentifierType] | None


class MaterialContext(contracts.ContextModel):
    id: contracts.IdentifierType
    status: int | None


class EventState(contracts.StateModel):
    state_id: contracts.IdentifierType
    kind: str
    context: dict | None = None


class CreateMaterial(contracts.Command):
    status: int
    caption: str
    preview: str
    body: str
    published_at: datetime.datetime
    cover_url: str | None = None


class UpdateCaption(contracts.Command):
    caption: str


class MaterialUpdated(contracts.InfoEvent):
    caption: str


class MaterialCreated(contracts.InfoEvent):
    pass


class TestActorFailed(contracts.ExceptionEvent):
    pass


class MaterialContextCollector(ContextCollector):
    def __init__(self, data_vendor: contracts.DefaultDataVendor):
        self._data_vendor = data_vendor

    async def general(
        self,
        state_scope: contracts.StateScope,
        message: contracts.Message | None = None
    ) -> collections.abc.Mapping[contracts.IdentifierType, MaterialContext] | None:
        response = await self._data_vendor.get(
            Query(
                root_node=Node(
                    relation='content',
                    fields=[
                        Field('id'),
                        Field('status')
                    ],
                    filter={'id:in': state_scope}
                ),
            )
        )
        return {r.get('id'): MaterialContext(**r) for r in response.get_all() or ()}


class EventActor(Actor):
    def register(self, event: contracts.InfoEvent):
        self._state = event

    def __state__(self) -> EventState:
        return EventState(
            state_id=self.__state_id__(),
            kind=self._state.__class__.__name__,
            context=self._state.context
        )


class MaterialActor(Actor):
    def create(self, message: CreateMaterial, context: MaterialContext | None):
        if context and context.id:
            raise exceptions.ActorException(message="Duplicate", context={'id': context.id})
        self._state = message.dict()
        return MaterialCreated(
            state_id=self.__state_id__(),
            context=message.dict(exclude_unset=True)
        )

    def update_caption(self, message: UpdateCaption):
        self._state = message.dict()

    def __state__(self) -> MaterialState:
        return MaterialState(
            **(self._state | {'id': self.__state_id__()})
        )


class MaterialStateKeeper(StateKeeper):
    def __init__(self, data_vendor: contracts.DefaultDataVendor):
        self._data_vendor = data_vendor

    async def __call__(
        self,
        state: MaterialState | collections.abc.Sequence[MaterialState]
    ) -> typing.NoReturn:
        if isinstance(state, collections.abc.Sequence):
            data = [s.dict(exclude_unset=True) for s in state]
        elif isinstance(state, MaterialState):
            data = state
        else:
            return
        await self._data_vendor.save({
            'content': data
        })


class EventStateKeeper(StateKeeper):
    def __init__(self, data_vendor: contracts.DefaultDataVendor):
        self._data_vendor = data_vendor

    async def __call__(
        self,
        state: EventState | collections.abc.Sequence[EventState]
    ) -> typing.NoReturn:
        if isinstance(state, collections.abc.Sequence):
            data = [self._prepare(s) for s in state]
        elif isinstance(state, EventState):
            data = self._prepare(state)
        else:
            return
        await self._data_vendor.save({
            'events': data
        })

    @staticmethod
    def _prepare(state: EventState):
        return dict(
            id=uuid.uuid4(),
            actor_id=state.state_id,
            event_type=state.kind,
            context=state.context
        )


def bootstrap_dependency_registry(
    connection_pool: SqlalchemyConnectionPool
) -> DependencyRegistry:
    dr = DependencyRegistry()
    dr.register_connection_context(
        open_callback=connection_pool.get_connection,
        close_success_callback=connection_pool.commit,
        close_failure_callback=connection_pool.rollback,
        contract=DataVendorConnection
    )
    dr.register_registry(
        instance=Registry(*db_metadata.tables.values()),
        contract=DataFrameRegistry
    )
    dr.register_data_vendor(
        instance=DefaultDataVendor,
        contract=contracts.DefaultDataVendor
    )
    dr.register_actor(MaterialActor)
    dr.register_actor(EventActor)
    dr.register_state_handler(MaterialStateKeeper)
    dr.register_state_handler(EventStateKeeper)
    dr.register_context_collector(MaterialContextCollector)
    return dr


def bootstrap_app(
    rdbs_dsn: str
) -> CommandProcessorFactory:
    return CommandProcessorFactory(
        dependency_registry=bootstrap_dependency_registry(
            connection_pool=SqlalchemyConnectionPool(
                dsn=rdbs_dsn,
                auto_commit=True
            )
        )
    )


async def main():
    factory = bootstrap_app(rdbs_dsn='postgresql+asyncpg://postgres:123@localhost:5432/alchemy_graph')
    update_command = UpdateCaption(
        caption='asdasd',
    )
    create_command = CreateMaterial(
        caption='asdasd',
        status=1,
        preview="sadasdasdasd",
        body="ddd",
        published_at=datetime.datetime.utcnow()
    )
    async with factory.get_processor() as processor:
        await processor.receive(
            command=create_command,
            state_scope=(
                uuid.UUID('28C3C3DD-E258-4068-9472-B1BAC7B93E5D'),
                uuid.UUID('A625DCC8-64D3-4030-90A7-5A9F430A7706')
            )
        )


asyncio.run(main())
