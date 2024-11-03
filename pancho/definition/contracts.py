import dataclasses
import typing

from zodchy import codex


@dataclasses.dataclass(frozen=True)
class Command(codex.cqea.Command):
    pass


@dataclasses.dataclass(frozen=True)
class Query(codex.cqea.Query):
    pass


@dataclasses.dataclass(frozen=True)
class Context(codex.cqea.Context):
    pass


@dataclasses.dataclass(frozen=True)
class Event(codex.cqea.Event):
    pass


@dataclasses.dataclass(frozen=True)
class Error(codex.cqea.Error):
    status_code: int
    message: str
    semantic_code: int | None = None
    details: typing.Any | None = None
