from .. import messages, depends
from ..messages import EmployeeStored


async def employee_writer(
    employee_created: messages.EmployeeCreated,
    email_generated: messages.EmployeeWorkEmailGenerated,
    employee_repository: depends.EmployeeRepositoryContract
) -> messages.EmployeeStored:
    return EmployeeStored(
        id=employee_repository.save(employee_created.first_name, employee_created.last_name)['id'],
        email=email_generated.email
    )
