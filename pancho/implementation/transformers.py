from collections.abc import Callable
from types import ModuleType
import inspect

import zodchy

type AdapterType = Callable[[type[Exception]], zodchy.codex.cqea.Error]


class ExceptionTransformer:
    def __init__(self):
        self._storage = {}

    def register_adapter(self, adapter: AdapterType):
        signature = inspect.signature(adapter)
        for param in signature.parameters.values():
            if Exception in param.annotation.__mro__:
                if param.annotation in self._storage:
                    raise ValueError(
                        f"Adapter for {param.annotation} already registered"
                    )
                self._storage[param.annotation] = adapter
            else:
                raise ValueError(f"{param.annotation} is not an Exception")

    def register_module(self, module: ModuleType):
        for e in inspect.getmembers(module):
            entity = e[1]
            if inspect.ismodule(entity) and module.__name__ in entity.__name__:
                self.register_module(entity)
            elif inspect.isfunction(entity) and not entity.__name__.startswith("_"):
                self.register_adapter(entity)

    def __call__(self, exception: Exception) -> zodchy.codex.cqea.Error:
        adapter = self._storage.get(type(exception))
        if adapter:
            result = adapter(exception)
            if (
                result is not None
                and zodchy.codex.cqea.Error in result.__class__.__mro__
            ):
                return result
        raise exception
