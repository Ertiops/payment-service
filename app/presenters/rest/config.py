from dataclasses import dataclass, field
from os import environ

from app.adapters.database.config import DatabaseConfig
from app.application.config import AppConfig, SecretConfig


@dataclass
class RestConfig:
    host: str = field(default_factory=lambda: environ.get("APP_REST_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: int(environ.get("APP_REST_PORT", 8000)))

    app: AppConfig = field(default_factory=lambda: AppConfig())
    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig())
    secret: SecretConfig = field(default_factory=lambda: SecretConfig())
