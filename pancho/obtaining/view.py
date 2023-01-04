import abc
import typing

from ..definitions import contracts
from tacitus.definitions import contracts as data_vendor_contract


class View:
    def __init__(self, data_vendor: contracts.DefaultDataVendor):
        self._data_vendor = data_vendor

    def _query(self) -> contracts.vendoring.Query:
        ...

    @abc.abstractmethod
    async def __call__(self, *args, **kwargs): ...


class ListView(View):
    async def __call__(
        self,
        filters: contracts.FilterSchema | None = None,
        sort: contracts.SortSchema | None = None,
        pagination: contracts.PaginationSchema | None = None
    ) -> contracts.LiteralViewData:
        query = self._query()
        return await self._get_data(query, filters, sort, pagination)

    async def _get_data(
        self,
        query: contracts.vendoring.Query,
        filters: contracts.FilterSchema | None = None,
        sort: contracts.SortSchema | None = None,
        pagination: contracts.PaginationSchema | None = None
    ):
        if filters:
            query = filters.apply(query)
        if sort:
            query = sort.apply(query)
        if pagination:
            query = pagination.apply(query)
        result_proxy = await self._data_vendor.get(query=query)

        result = dict(data=result_proxy.get_all())
        if pagination:
            result |= {'total': result_proxy.get_total()}
        return result


class EntryView(View):
    async def __call__(
        self,
        id: contracts.IdentifierType
    ) -> contracts.EntryViewData:
        query = self._query()
        return await self._get_data(query, id)

    async def _get_data(
        self,
        query: contracts.vendoring.Query,
        id: contracts.IdentifierType
    ):
        query.root_node.filter = (query.root_node.filter or {}) | {'id': id}
        result_proxy = await self._data_vendor.get(query=query)
        return dict(
            data=result_proxy.get_one(),
        )


class LiteralView(View):
    async def __call__(
        self,
        field_name: str,
        filters: contracts.FilterSchema | None = None
    ) -> contracts.LiteralViewData:
        return await self._get_data(field_name, filters)

    async def _get_data(
        self,
        field_name: str,
        filters: contracts.FilterSchema | None = None,
    ) -> typing.Any | None:
        relation_name, field_name = field_name.split('.')
        query = data_vendor_contract.Query(
            root_node=data_vendor_contract.Node(
                relation=relation_name,
                fields=[
                    data_vendor_contract.Field(name=field_name)
                ]
            )
        )
        if filters:
            query = filters.apply(query)
        result_proxy = await self._data_vendor.get(query=query)

        result = result_proxy.get_one()
        return dict(
            data=(result or {}).get(field_name)
        )
