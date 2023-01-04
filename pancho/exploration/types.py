import typing


def search_for_subtype(given_type: type[typing.Any], desired_type: type[typing.Any]):
    if not given_type or not desired_type:
        return
    if hasattr(given_type, '__mro__') and desired_type in given_type.__mro__:
        return given_type
    for _type in typing.get_args(given_type):
        if result := search_for_subtype(_type, desired_type):
            return result
