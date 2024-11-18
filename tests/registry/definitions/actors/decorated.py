from pancho.aux.wrappers import semantic
from ....definitions import messages, context


@semantic('auditor')
def audit_employee(employee: messages.CreateEmployee) -> messages.CreateEmployee:
    pass


@semantic('usecase')
def create_employee(employee: messages.CreateEmployee) -> messages.EmployeeCreated:
    pass


@semantic('writer')
async def save_employee(employee: messages.EmployeeCreated):
    pass


@semantic('reader')
async def get_employee(query: messages.GetEmployee):
    pass


@semantic('context')
async def get_employee_context(employee: messages.CreateEmployee) -> context.CreateEmployeeContext:
    pass
