import collections.abc
import typing


class ListViewData(typing.TypedDict):
    data: collections.abc.Sequence[collections.abc.Mapping]
    total: int


class EntryViewData(typing.TypedDict):
    data: collections.abc.Mapping


class LiteralViewData(typing.TypedDict):
    data: typing.Any


class View(typing.Protocol):
    async def __call__(self, *args, **kwargs) -> LiteralViewData | EntryViewData | LiteralViewData: ...


class ViewFactory(typing.Protocol):
    async def __aenter__(self, view_contract: type[View] | None = None): ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    async def __call__(self, view_contract: type[View]) -> typing.AsyncGenerator[View, None]: ...

    async def get(self, view_contract: type[View]) -> View: ...
