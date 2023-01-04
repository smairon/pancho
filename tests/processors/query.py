import asyncio
import uuid

from tacitus.adapters.sqlalchemy.vendoring import SqlAlchemyVendor
from tacitus.adapters.sqlalchemy.registration import Registry
from tacitus.definitions.contracts import DataVendorConnection, DataFrameRegistry, Query, Node, Field
from tacitus.adapters.sqlalchemy.connecting import SqlalchemyConnectionPool
from pancho.bootstraping.registering import DependencyRegistry
from pancho.definitions import contracts
from pancho.obtaining.view import View, EntryView, ListView
from pancho.obtaining.factory import ViewFactory
from ext.schema import db_metadata


class DefaultVendor(SqlAlchemyVendor):
    pass


class ContentView(View):
    def _query(self) -> contracts.vendoring.Query:
        return Query(
            root_node=Node(
                relation="content",
                fields=[
                    Field(name="caption"),
                    Field(name="id"),
                    Node(
                        relation="tags",
                        fields=[
                            Field(name="id"),
                            Field(name="name")
                        ]
                    )
                ]
            )
        )


class ContentEntryView(ContentView, EntryView):
    pass


class ContentListView(ContentView, ListView):
    pass


def bootstrap_dependency_registry(
    connection_pool: SqlalchemyConnectionPool
) -> DependencyRegistry:
    dr = DependencyRegistry()
    dr.register_connection_context(
        open_callback=connection_pool.get_connection,
        close_success_callback=connection_pool.commit,
        close_failure_callback=connection_pool.commit,
        contract=DataVendorConnection
    )
    dr.register_registry(
        instance=Registry(*db_metadata.tables.values()),
        contract=DataFrameRegistry
    )
    dr.register_data_vendor(
        instance=DefaultVendor,
        contract=contracts.DefaultDataVendor
    )
    dr.register_view(ContentListView)
    dr.register_view(ContentEntryView)
    return dr


def bootstrap_app(
    rdbs_dsn: str
) -> ViewFactory:
    return ViewFactory(
        dependency_registry=bootstrap_dependency_registry(
            connection_pool=SqlalchemyConnectionPool(
                dsn=rdbs_dsn,
                auto_commit=True
            )
        )
    )


async def main():
    factory = bootstrap_app(rdbs_dsn='postgresql+asyncpg://postgres:123@localhost:5432/alchemy_graph')
    async with factory:
        view = await factory.get(ContentListView)
        k = await view()
        view = await factory.get(ContentEntryView)
        l = await view(id=uuid.UUID('94b8d68c-1082-41d4-89d0-69d037dc6965'))


asyncio.run(main(), debug=True)
