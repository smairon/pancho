import datetime
import functools
import typing
import re
import dateutil.parser

import pydantic

from ..definitions.contracts.vendoring import Query
from ..definitions.exceptions import markup

type_casting_map = {
    datetime.datetime: dateutil.parser.parse
}


def interval(field_type: typing.Any, value: str, operations: tuple[str, str]):
    if field_type not in (datetime.datetime, datetime.date, int):
        raise markup.TypeMismatch(f'Interval cannot be calculated for type {field_type}')

    _data = value.split(',')
    if len(_data) == 0 or len(_data) > 2:
        raise markup.RangeException('range must contain strictly two members')

    return tuple(
        (operations[i], type_casting_map.get(field_type, field_type)(v.strip()))
        for i, v in enumerate(_data) if v
    )


def multitude(field_type: typing.Any, value: str, operation: str):
    _data = value.split(',')
    return (
        (
            operation,
            [
                type_casting_map.get(field_type, field_type)(v.strip())
                for v in _data if v
            ]
        ),
    )


def literal(field_type: typing.Any, value: str, operation: str):
    if 'like' in operation and field_type != str:
        raise markup.TypeMismatch(f'{operation} cannot be applied for type {field_type}')

    return (
        (
            operation,
            type_casting_map.get(field_type, field_type)(value.strip())
        ),
    )


class FilterSchema(pydantic.BaseModel):
    def apply(self, query: Query):
        _filter = query.root_node.filter or {}
        for k, v in dict(self.__dict__).items():
            for operation, value in self._discover_pattern(k, v) or ():
                _filter[f'{k.replace("__", ".")}:{operation}'] = value
        query.root_node.filter = _filter
        return query

    @functools.cached_property
    def _field_types(self):
        cls = type(self)
        return {
            name: model.field_info.extra['value_type']
            for name, model in cls.__fields__.items()
        }

    @functools.cached_property
    def _pattern_handler_map(self) -> dict[re.Pattern, typing.Callable]:
        return {
            re.compile('^(null)$'): lambda x, y: (('is', None),),
            re.compile('^(!null)$'): lambda x, y: (('isnot', None),),
            re.compile(r'^\(([\d\-,]+)\)$'): functools.partial(interval, operations=('gt', 'lt')),
            re.compile(r'^\[([\d\-,]+)\)$'): functools.partial(interval, operations=('ge', 'lt')),
            re.compile(r'^\(([\d\-,]+)\]$'): functools.partial(interval, operations=('gt', 'le')),
            re.compile(r'^\[([\d\-,]+)\]$'): functools.partial(interval, operations=('ge', 'le')),
            re.compile(r'^!\{(.*)\}$'): functools.partial(multitude, operation='notin'),
            re.compile(r'^\{(.*)\}$'): functools.partial(multitude, operation='in'),
            re.compile(r'^[~]{2}(.*)$'): functools.partial(literal, operation='like'),
            re.compile(r'^\![~]{2}(.*)$'): functools.partial(literal, operation='notlike'),
            re.compile(r'^\~(.*)$'): functools.partial(literal, operation='ilike'),
            re.compile(r'^\!\~(.*)$'): functools.partial(literal, operation='notilike'),
            re.compile(r'^\!(.*)$'): functools.partial(literal, operation='neq'),
            re.compile(r'(.*)'): functools.partial(literal, operation='eq')
        }

    def _discover_pattern(self, name: str, value: str):
        if not value:
            return
        for pattern, handler in self._pattern_handler_map.items():
            if mo := pattern.search(value.strip().lower()):
                try:
                    return handler(self._field_types[name], mo.group(1))
                except Exception as e:
                    raise markup.FilterException(
                        field_name=name,
                        field_value=value,
                        message=str(e)
                    )


class SortSchema(pydantic.BaseModel):
    sort_by: str | None = None

    def apply(self, query: Query):
        if not self.sort_by:
            return query
        _sort_by = query.root_node.sort or {}
        for v in self.sort_by.split(','):
            field, direction = v.replace('__', '.').split(':')
            _sort_by[field] = direction
        query.root_node.sort = _sort_by
        return query


class PaginationSchema(pydantic.BaseModel):
    page: int | None = None
    items_per_page: int | None = None
    _items_per_page_default: int = pydantic.PrivateAttr(default=10)

    def apply(self, query: Query):
        query.with_total = True
        page = self.page or 1
        query.root_node.limit = self.items_per_page or self._items_per_page_default
        query.root_node.offset = (page - 1) * query.root_node.limit
        return query
