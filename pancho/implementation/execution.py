import zorge
from ..definition import contracts
from .processing import CQProcessor


class ExpectedErrorOccurred(Exception):
    pass


class TaskExecutor:
    def __init__(
        self,
        di_container: zorge.Container,
        actor_registry: contracts.ActorRegistry
    ):
        self._di_container = di_container
        self._actor_registry = actor_registry

    async def run(
        self,
        task: contracts.Task,
        execution_context: contracts.ExecutionContext | None = None
    ) -> list[contracts.Message]:
        resolver_context = (execution_context,) if execution_context else ()
        stream = []
        try:
            async with self._di_container.get_resolver(*resolver_context) as resolver:
                processor = CQProcessor(self._actor_registry, resolver)(task)
                async for message in processor:
                    stream.append(message)
                    if isinstance(message, contracts.Error):
                        raise ExpectedErrorOccurred  # raise error just for informing context manager
        except ExpectedErrorOccurred:
            pass  # supress this artificial error
        return stream
