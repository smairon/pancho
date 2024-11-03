import typing
import functools
import traceback

from ..definition.contracts import Error


def semantic(kind: typing.Literal['usecase', 'io', 'auditor', 'context', 'response', 'reader', 'writer']):
    def decorator(func):
        func.__dict__['__semantic__'] = kind

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        return wrapper

    return decorator


def skip(func):
    func.__dict__['__semantic__'] = 'skip'

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)

    return wrapper


def default_exception(e: Exception, add_traceback: bool = False) -> Error:
    return Error(
        status_code=500,
        message=str(e),
        details=''.join(traceback.format_tb(e.__traceback__)) if add_traceback else None
    )
