from dataclasses import dataclass, field
from os import environ


@dataclass(frozen=True, kw_only=True, slots=True)
class AuthConfig:
    x_api_key: str = field(default_factory=lambda: environ["APP_X_API_KEY"])
