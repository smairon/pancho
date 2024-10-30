import datetime
import uuid

import pytest
from zorge.implementation.container import Container as DIContainer

from pancho.implementation.processing import CQProcessor
from pancho.implementation.registry import ActorRegistry

from ..definitions import messages, actors, depends


class Connection:
    def __init__(self, connection_id: int):
        self._connection_id = connection_id

    def execute(self, query: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, query + str(self._connection_id)))


class ConnectionPool:
    def __init__(self):
        self._counter = 0

    def get_connection(self) -> depends.ConnectionContract:
        self._counter += 1
        return Connection(self._counter)


class EmployeeRepository:
    def __init__(self, pool: depends.ConnectionPoolContract):
        self._connection_pool = pool

    def save(self, first_name: str, last_name: str) -> dict:
        return {
            'id': self._connection_pool.get_connection().execute(f'{first_name} {last_name}')
        }


@pytest.fixture(scope="module")
def di_container():
    container = DIContainer()
    container.register_dependency(
        implementation=ConnectionPool,
        contract=depends.ConnectionPoolContract
    )
    container.register_dependency(
        implementation=EmployeeRepository,
        contract=depends.EmployeeRepositoryContract
    )
    return container


@pytest.fixture(scope="module")
def actor_registry():
    actor_registry = ActorRegistry()
    actor_registry.add(actors.employee_creation_auditor)
    actor_registry.add(actors.create_employee_usecase)
    actor_registry.add(actors.generate_work_email_usecase)
    actor_registry.add(actors.create_employee_context)
    actor_registry.add(actors.generate_supervised_employee_email_context)
    actor_registry.add(actors.employee_writer)
    return actor_registry


@pytest.mark.asyncio
async def test_happy_path(di_container, actor_registry):
    async with di_container.get_resolver() as resolver:
        processor = CQProcessor(actor_registry, resolver)
        stream = []
        async for message in processor(
            messages.CreateEmployee(
                first_name="John",
                last_name="Doe",
                phone="123456789",
                birth_date=datetime.date(1978, 3, 4)
            )
        ):
            stream.append(message)
    assert [m.__class__.__name__ for m in stream] == [
        'CreateEmployeeContext',
        'CreateEmployee',
        'EmployeeCreated',
        'GenerateEmployeeEmailContext',
        'EmployeeWorkEmailGenerated',
        'EmployeeStored'
    ]
    assert stream[-1].id == 'c0298842-0d8c-5065-ba71-8059b9b63d09'


@pytest.mark.asyncio
async def test_audit_error(di_container, actor_registry):
    async with di_container.get_resolver() as resolver:
        processor = CQProcessor(actor_registry, resolver)
        stream = []
        async for message in processor(
            messages.CreateEmployee(
                first_name="Alexander",
                last_name="Petrov",
                phone="123456789",
                birth_date=datetime.date(1998, 3, 4)
            )
        ):
            stream.append(message)
    assert [m.__class__.__name__ for m in stream] == [
        'CreateEmployeeContext',
        'EmployeeDuplicated',
    ]
