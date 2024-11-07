import collections.abc
import dataclasses
import typing

import zodchy


@dataclasses.dataclass(frozen=True)
class Command(zodchy.codex.cqea.Command):
    pass


@dataclasses.dataclass(frozen=True)
class Query(zodchy.codex.cqea.Query):
    def __iter__(self) -> collections.abc.Iterable[tuple[str, zodchy.codex.query.ClauseBit]]:
        for field in dataclasses.fields(self):
            value = getattr(self, field.name)
            if value is not zodchy.types.Empty:
                yield field.name, value


@dataclasses.dataclass(frozen=True)
class Context(zodchy.codex.cqea.Context):
    pass


@dataclasses.dataclass(frozen=True)
class Event(zodchy.codex.cqea.Event):
    pass


@dataclasses.dataclass(frozen=True)
class Error(zodchy.codex.cqea.Error):
    status_code: int
    message: str
    semantic_code: int | None = None
    details: typing.Any | None = None
