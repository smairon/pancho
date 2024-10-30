import typing


class ConnectionContract(typing.Protocol):
    def execute(self, query: str) -> str: ...


class ConnectionPoolContract(typing.Protocol):
    def get_connection(self) -> ConnectionContract: ...


class EmployeeRepositoryContract(typing.Protocol):
    def save(self, first_name: str, last_name: str) -> dict: ...
