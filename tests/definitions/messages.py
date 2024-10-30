import dataclasses
import uuid

import zodchy
import datetime


@dataclasses.dataclass
class GetEmployee(zodchy.codex.cqea.Query):
    id: int


@dataclasses.dataclass
class CreateEmployee(zodchy.codex.cqea.Command):
    first_name: str
    last_name: str
    phone: str
    birth_date: datetime.date


@dataclasses.dataclass
class EmployeeDuplicated(zodchy.codex.cqea.Error):
    first_name: str
    last_name: str


@dataclasses.dataclass
class EmailDuplicated(zodchy.codex.cqea.Error):
    email: str


@dataclasses.dataclass
class EmployeeCreated(zodchy.codex.cqea.Event):
    id: uuid.UUID
    first_name: str
    last_name: str
    phone: str
    birth_date: datetime.date


@dataclasses.dataclass
class EmployeeWorkEmailGenerated(zodchy.codex.cqea.Event):
    email: str


@dataclasses.dataclass
class EmployeeStored(zodchy.codex.cqea.Event):
    id: uuid.UUID
    email: str
