import typing
import uuid

IdentifierType = uuid.UUID


class IdentifierFactory(typing.Protocol):
    @staticmethod
    def produce_random(): ...

    def produce_message_id(self) -> uuid.UUID: ...

    def produce_actor_id(self) -> uuid.UUID: ...

    def produce_derived(self, value: typing.Hashable): ...
