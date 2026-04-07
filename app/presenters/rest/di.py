from dishka import Provider, Scope, from_context
from starlette.requests import Request


class FastAPIProvider(Provider):
    request = from_context(
        provides=Request,
        scope=Scope.REQUEST,
    )
