import typing
import uuid

from ..definitions.contracts.identity import IdentifierFactory


class UUIDIdentifierFactory(IdentifierFactory):
    def __init__(self, namespace: uuid.UUID):
        self._namespace = namespace

    def produce_message_id(self) -> uuid.UUID:
        return self.produce_random()

    def produce_actor_id(self) -> uuid.UUID:
        return self.produce_random()

    @staticmethod
    def produce_random() -> uuid.UUID:
        return uuid.uuid4()

    def produce_derived(self, value: typing.Hashable):
        if isinstance(value, str):
            return uuid.uuid5(self._namespace, value)
        return uuid.UUID(int=hash(value))
