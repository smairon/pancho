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


def default_exception(
    e: Exception,
    message: str = "Something goes wrong",
    include_exception_message: bool = False,
    include_traceback: bool = False
) -> Error:
    details = {}
    if include_exception_message:
        details["message"] = str(e)
    if include_traceback:
        details["trace"] = traceback.format_exception(e.__traceback__)
    return Error(
        status_code=500,
        message=message,
        details=details or None
    )
