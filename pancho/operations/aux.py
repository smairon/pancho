import typing
import datetime
import functools
from ..definitions import contracts, exceptions


def expected_events(
    success_event_type: type[contracts.InfoEvent] | None = None,
    failure_event_type: type[contracts.ExceptionEvent] | None = None
):
    def method_wrapper(method: typing.Callable):
        @functools.wraps(method)
        def method_surrogate(*args, **kwargs):
            try:
                result = method(*args, **kwargs)
                if success_event_type:
                    return success_event_type(
                        created_at=datetime.datetime.utcnow(),
                        **(result or {})
                    )
                return result
            except exceptions.ActorException as exc:
                if failure_event_type:
                    return failure_event_type(
                        created_at=datetime.datetime.utcnow(),
                        code=exc.code,
                        message=exc.message,
                        details=exc.details
                    )
                raise exc
            except Exception as exc:
                if failure_event_type:
                    return failure_event_type(
                        created_at=datetime.datetime.utcnow(),
                        code=500,
                        message=str(exc)
                    )

        return method_surrogate

    return method_wrapper
