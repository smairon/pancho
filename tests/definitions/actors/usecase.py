import uuid
import dataclasses
from .. import messages, context


def create_employee_usecase(employee: messages.CreateEmployee) -> messages.EmployeeCreated:
    return messages.EmployeeCreated(id=uuid.uuid4(), **dataclasses.asdict(employee))


def generate_work_email_usecase(
    employee: messages.EmployeeCreated,
    email_context: context.GenerateEmployeeEmailContext
) -> messages.EmployeeWorkEmailGenerated:
    return messages.EmployeeWorkEmailGenerated(
        email=f"{employee.first_name}.{employee.last_name}@{email_context.server}"
    )
