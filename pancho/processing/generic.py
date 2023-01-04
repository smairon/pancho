import dataclasses
import typing
import collections.abc

from pancho.definitions import contracts


class MessageQueue:
    def __init__(
        self,
        frames: collections.abc.Iterable[contracts.MessageFrame] | None = None
    ):
        self._data = frames or []
        self._index = 0

    def enqueue(
        self,
        data: contracts.MessageFrame
    ) -> typing.NoReturn:
        self._data.append(data)

    def dequeue(self) -> contracts.MessageFrame | None:
        if self._index >= len(self._data):
            return
        result = self._data[self._index]
        self._index += 1
        return result

    def get_stream(self) -> contracts.MessageStreamType:
        return (m.message for m in self._data)


@dataclasses.dataclass
class ProcessorSettings:
    register_events: bool = True
    auto_commit: bool = True
