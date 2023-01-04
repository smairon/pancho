import abc
import typing

from .vendoring import Query


class FilterSchema(typing.Protocol):
    @abc.abstractmethod
    def apply(self, query: Query): ...


class SortSchema(typing.Protocol):
    sort_by: str | None = None

    @abc.abstractmethod
    def apply(self, query: Query): ...


class PaginationSchema(typing.Protocol):
    page: int | None = None
    items_per_page: int | None = None

    @abc.abstractmethod
    def apply(self, query: Query): ...
