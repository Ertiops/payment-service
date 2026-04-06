class AuthException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class MissingApiKeyException(AuthException): ...


class InvalidApiKeyException(AuthException): ...
