import pytest

from pancho.implementation.registry import ActorRegistry, ActorSemanticKind, register_module
from .definitions.actors import decorated, convention


@pytest.fixture(scope="function")
def registry():
    return ActorRegistry()


@pytest.mark.parametrize('actor,semantic_kind', [
    (decorated.audit_employee, ActorSemanticKind.AUDIT),
    (decorated.create_employee, ActorSemanticKind.USECASE),
    (decorated.save_employee, ActorSemanticKind.IO),
    (decorated.get_employee, ActorSemanticKind.IO),
    (decorated.get_employee_context, ActorSemanticKind.CONTEXT)
])
def test_actor_decorator(registry, actor, semantic_kind):
    registry.add(actor)
    result = list(registry)
    assert result[0].semantic_kind == semantic_kind


@pytest.mark.parametrize('actor,semantic_kind', [
    (convention.create_employee_auditor, ActorSemanticKind.AUDIT),
    (convention.create_employee_usecase, ActorSemanticKind.USECASE),
    (convention.employee_creation_writer, ActorSemanticKind.IO),
    (convention.employee_reader, ActorSemanticKind.IO),
    (convention.employee_creation_context, ActorSemanticKind.CONTEXT)
])
def test_actor_convention(registry, actor, semantic_kind):
    registry.add(actor)
    result = list(registry)
    assert result[0].semantic_kind == semantic_kind


def test_decorated_module_registration(registry):
    register_module(registry, decorated)
    assert {a.runtime.executable.__name__ for a in registry} == {
        'audit_employee',
        'create_employee',
        'save_employee',
        'get_employee',
        'get_employee_context'
    }


def test_convention_module_registration(registry):
    register_module(registry, convention)
    assert {a.runtime.executable.__name__ for a in registry} == {
        'create_employee_auditor',
        'create_employee_usecase',
        'employee_creation_writer',
        'employee_reader',
        'employee_creation_context'
    }
