import typing
import functools


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
