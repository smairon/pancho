import collections.abc


class PanchoException(Exception):
    def __init__(
        self,
        contract: type = None,
        message: str = None,
        context: collections.abc.Mapping | None = None
    ):
        self.contract = contract
        self.message = message
        self.context = context
        super().__init__()


class MarkupException(PanchoException):
    pass


class ActorException(PanchoException):
    pass


class ActorInitializationException(ActorException):
    pass


class ActorMessageProcessingException(ActorException):
    pass


class DependencyException(PanchoException):
    pass


class ContextException(PanchoException):
    pass


class LoadContextException(ContextException):
    pass


class StateException(PanchoException):
    pass


class CommitStateException(StateException):
    pass
