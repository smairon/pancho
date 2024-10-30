from .. import messages, context


def create_employee_context(employee: messages.CreateEmployee) -> context.CreateEmployeeContext:
    return context.CreateEmployeeContext(
        is_exists=employee.first_name == 'Alexander' and employee.last_name == 'Petrov'
    )


def generate_supervised_employee_email_context(
    employee: messages.EmployeeCreated
) -> context.GenerateEmployeeEmailContext:
    if employee.birth_date.year < 1991:
        server = "example.su"
    else:
        server = "example.ru"
    return context.GenerateEmployeeEmailContext(server=server)
