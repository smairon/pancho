import abc
import typing

import zodchy

ActorIdType: typing.TypeAlias = int


class PanchoException(Exception):
    pass


class CannotRegisterActor(PanchoException):
    def __init__(self, actor: zodchy.codex.cqea.Actor):
        self._actor = actor
        super().__init__(self.message())

    @abc.abstractmethod
    def message(self):
        return f'Cannot register actor: {self._actor}'


class CannotDeriveActorPurpose(PanchoException):
    def __init__(self, actor: zodchy.codex.cqea.Actor):
        self._actor = actor
        super().__init__(self.message())

    def message(self):
        return f'Cannot derive actor type: {self._actor}'


class CannotDefineActorParameter(PanchoException):
    def __init__(self, actor: zodchy.codex.cqea.Actor):
        self._actor = actor
        super().__init__(self.message())

    def message(self):
        return f'Cannot define actor parameter: {self._actor}'


class CannotResolveActorParameter(PanchoException):
    def __init__(self, actor_id: ActorIdType, param_name: str):
        self._actor_id = actor_id
        self._param_name = param_name
        super().__init__(self.message())

    def message(self):
        return f'Cannot resolve actor parameter: {self._param_name} of {self._actor_id}'


class CannotProcessActorResult(PanchoException):
    def __init__(self, actor_id: ActorIdType):
        self._actor_id = actor_id
        super().__init__(self.message())

    def message(self):
        return f'Cannot process actor result: {self._actor_id}'


class ActorSemanticDefinitionFailed(PanchoException):
    def __init__(self, actor_name: str):
        self._name = actor_name
        super().__init__(self.message())

    def message(self):
        return f'Actor semantic definition failed: {self._name}'
