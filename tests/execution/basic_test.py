import datetime
import uuid
import dataclasses

import pytest
from zorge.implementation.container import Container as DIContainer

from pancho.implementation import Executor
from pancho.implementation.registry import ActorRegistry

from ..definitions import messages


def create_employee_usecase(employee: messages.CreateEmployee) -> messages.EmployeeCreated:
    return messages.EmployeeCreated(id=uuid.uuid4(), **dataclasses.asdict(employee))


def employee_creation_auditor(employee: messages.CreateEmployee):
    return employee


def employee_creation_writer(employee: messages.EmployeeCreated):
    pass


@pytest.fixture(scope="module")
def di_container():
    return DIContainer()


@pytest.fixture(scope="module")
def actor_registry():
    actor_registry = ActorRegistry()
    actor_registry.add(employee_creation_writer)
    actor_registry.add(employee_creation_auditor)
    actor_registry.add(create_employee_usecase)
    return actor_registry


@pytest.mark.asyncio
async def test_executor(actor_registry, di_container):
    executor = Executor(di_container, actor_registry)
    stream = await executor.run(
        messages.CreateEmployee(
            first_name="Alex",
            last_name="Petrov",
            phone="123456789",
            birth_date=datetime.date(1998, 3, 4)
        )
    )
    assert [m.__class__.__name__ for m in stream] == [
        'CreateEmployee',
        'EmployeeCreated'
    ]
