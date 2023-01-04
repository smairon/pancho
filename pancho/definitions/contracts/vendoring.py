import typing
import collections.abc

FieldName = str
FieldValue = typing.Any
SortDirection = typing.Literal['asc', 'desc']
FilterClause = collections.abc.Mapping[str, typing.Any]
SortClause = collections.abc.Mapping[FieldName, SortDirection]
MutationData = collections.abc.Mapping[str, typing.Any]


class Field(typing.Protocol):
    name: str
    alias: str | None = None
    relation: str | None = None


class Node(typing.Protocol):
    relation: str
    fields: collections.abc.MutableSequence[Field]
    name: str | None = None
    filter: FilterClause | None = None
    sort: SortClause | None = None
    limit: int | None = None
    offset: int | None = None
    modifier: typing.Callable = None


class Query(typing.Protocol):
    root_node: Node
    with_total: bool = False


class QueryResultProxy(typing.Protocol):
    def get_all(self): ...

    def get_one(self): ...

    def get_total(self): ...


class DataVendor(typing.Protocol):
    async def get(
        self,
        query: Query | None = None
    ) -> QueryResultProxy | None: ...

    async def save(
        self,
        data: MutationData
    ) -> typing.NoReturn: ...

    async def insert(
        self,
        data: MutationData
    ) -> typing.NoReturn: ...

    async def update(
        self,
        data: MutationData
    ) -> typing.NoReturn: ...

    async def delete(
        self,
        filter_clause: FilterClause
    ) -> typing.NoReturn: ...


class EventRegistratorDataVendor(DataVendor):
    pass


class DefaultDataVendor(DataVendor):
    pass


EventRegistratorFrameName = str
