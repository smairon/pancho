import contextlib

from ..definitions import contracts


class ViewFactory:
    def __init__(self, dependency_registry: contracts.DependencyRegistry):
        self._dependency_container = dependency_registry.get_container()
        self._dependency_provider = None

    async def __aenter__(self, view_contract: type[contracts.View] | None = None):
        self._dependency_provider = self._dependency_container.get_provider()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self._dependency_provider.shutdown(exc_type)

    async def get(self, view_contract: type[contracts.View]) -> contracts.View:
        return await self._dependency_provider.resolve(view_contract)

    @contextlib.asynccontextmanager
    async def __call__(self, view_contract: type[contracts.View]) -> contracts.View:
        dependency_provider = self._dependency_container.get_provider()
        exc_type = None
        try:
            yield await dependency_provider.resolve(view_contract)
        except Exception as e:
            exc_type = e
        finally:
            await dependency_provider.shutdown(exc_type)
            if exc_type:
                raise exc_type
