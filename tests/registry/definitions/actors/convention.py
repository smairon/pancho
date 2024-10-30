from ....definitions import messages, context


def create_employee_auditor(employee: messages.CreateEmployee) -> messages.CreateEmployee:
    pass


def create_employee_usecase(employee: messages.CreateEmployee) -> messages.EmployeeCreated:
    pass


async def employee_creation_writer(employee: messages.EmployeeCreated):
    pass


async def employee_reader(query: messages.GetEmployee):
    pass


async def employee_creation_context(employee: messages.CreateEmployee) -> context.CreateEmployeeContext:
    pass
