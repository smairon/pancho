import collections.abc

import zorge
import zodchy

from . import registry, processing


class ExpectedErrorOccurred(Exception):
    pass


class TaskExecutor:
    def __init__(
        self,
        di_container: zorge.Container,
        actor_registry: registry.ActorRegistry,
        error_wrapper: collections.abc.Callable[[Exception], zodchy.codex.cqea.Error] | None = None
    ):
        self._di_container = di_container
        self._actor_registry = actor_registry
        self._error_wrapper = error_wrapper

    async def run(
        self,
        task: zodchy.codex.cqea.Task,
        execution_context: registry.ExecutionContext | None = None
    ) -> list[zodchy.codex.cqea.Message]:
        resolver_context = (execution_context,) if execution_context else ()
        stream = []
        try:
            async with self._di_container.get_resolver(*resolver_context) as resolver:
                processor = processing.CQProcessor(self._actor_registry, resolver)(task)
                async for message in processor:
                    stream.append(message)
                    if isinstance(message, zodchy.codex.cqea.Error):
                        raise ExpectedErrorOccurred  # raise error just for informing context manager
        except ExpectedErrorOccurred:
            pass  # supress this artificial error
        except Exception as e:
            if self._error_wrapper:
                stream.append(self._error_wrapper(e))
            else:
                raise e
        return stream
