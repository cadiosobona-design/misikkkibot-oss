from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any


SECRET_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "secret_key",
    "private_key",
    "token",
    "password",
}


class SecretValue:
    def __init__(self, value: str) -> None:
        self._value = value

    def reveal_for_connector_boundary(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "SecretValue(<redacted>)"


def redact_payload(value: Any) -> Any:
    if isinstance(value, SecretValue):
        return "<redacted>"
    if is_dataclass(value):
        return redact_payload(asdict(value))
    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            if str(key).lower() in SECRET_KEYS:
                redacted[str(key)] = "<redacted>"
            else:
                redacted[str(key)] = redact_payload(item)
        return redacted
    if isinstance(value, (list, tuple, set)):
        return [redact_payload(item) for item in value]
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    return value
