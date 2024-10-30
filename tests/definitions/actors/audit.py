from .. import messages, context


def employee_creation_auditor(
    employee: messages.CreateEmployee,
    employee_context: context.CreateEmployeeContext
) -> messages.CreateEmployee | messages.EmployeeDuplicated:
    if employee_context.is_exists:
        return messages.EmployeeDuplicated(first_name=employee.first_name, last_name=employee.last_name)
    else:
        return employee
