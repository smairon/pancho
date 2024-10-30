import dataclasses
import zodchy


@dataclasses.dataclass
class CreateEmployeeContext(zodchy.codex.cqea.Context):
    is_exists: bool


@dataclasses.dataclass
class GenerateEmployeeEmailContext(zodchy.codex.cqea.Context):
    server: str
