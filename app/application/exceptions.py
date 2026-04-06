from typing import Any


class AppException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class EntityNotFoundException(AppException):
    def __init__(self, entity: type, entity_id: Any) -> None:
        super().__init__(f"{entity.__name__} with id {entity_id} not found")


class EmptyPayloadException(AppException): ...


class EntityAlreadyExistsException(AppException): ...


class StorageException(AppException):
    def __init__(self, storage_name: str) -> None:
        super().__init__(f"{storage_name} has failed to execute query")
