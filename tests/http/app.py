import uvicorn
import uuid
import datetime
import fastapi

from pancho.markup.schema import FilterSchema, SortSchema, PaginationSchema
from tacitus.definitions import contracts as vendor

from tacitus.adapters.sqlalchemy.vendoring import SqlAlchemyVendor
from tacitus.adapters.sqlalchemy.registration import Registry
from tacitus.definitions.contracts import DataVendorConnection, DataFrameRegistry
from tacitus.adapters.sqlalchemy.connecting import SqlalchemyConnectionPool
from pancho.bootstraping.registering import DependencyRegistry
from pancho.definitions import contracts
from pancho.obtaining.view import View, ListView, EntryView
from pancho.obtaining.factory import ViewFactory
from ext.schema import db_metadata


class DefaultVendor(SqlAlchemyVendor):
    pass


class ContentView(View):
    def _query(self) -> contracts.vendoring.Query:
        return vendor.Query(
            root_node=vendor.Node(
                relation="content",
                fields=[
                    vendor.Field(name="caption"),
                    vendor.Field(name="id")
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


class MaterialFilterSchema(FilterSchema):
    id: str = fastapi.Query(None, value_type=uuid.UUID)
    caption: str = fastapi.Query(None, value_type=str)
    preview: str = fastapi.Query(None, value_type=str)
    author_id: str = fastapi.Query(None, value_type=uuid.UUID)
    published_at: str = fastapi.Query(None, value_type=datetime.datetime)
    author__first_name: str = fastapi.Query(None, value_type=str)


app = fastapi.FastAPI()
app.view_factory = bootstrap_app('postgresql+asyncpg://postgres:123@localhost:5432/alchemy_graph')


@app.get("/")
async def get_list(
    request: fastapi.Request,
    filters: MaterialFilterSchema = fastapi.Depends(),
    sort: SortSchema = fastapi.Depends(),
    pagination: PaginationSchema = fastapi.Depends()
):
    async with request.app.view_factory(ContentListView) as view:
        result = await view(filters=filters, sort=sort, pagination=pagination)
    return result


@app.get("/{entity_id}")
async def get_one(
    request: fastapi.Request,
    entity_id: contracts.IdentifierType,
):
    async with request.app.view_factory:
        view = await request.app.view_factory.get(ContentEntryView)
        result = await view(id=entity_id)
    return result


if __name__ == "__main__":
    uvicorn.run(app, port=5004, log_level="info")
