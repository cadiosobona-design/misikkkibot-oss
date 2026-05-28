from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from misikkki_core.models import utc_now
from misikkki_security.redaction import redact_payload


@dataclass(frozen=True)
class AuditEvent:
    id: str
    session_id: str
    event_type: str
    ts: datetime
    payload: dict[str, Any]

    def as_record(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "event_type": self.event_type,
            "ts": self.ts.isoformat(),
            "payload": self.payload,
        }


class AppendOnlyAuditLog:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(
        self,
        session_id: str,
        event_type: str,
        payload: dict[str, Any],
        *,
        ts: datetime | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            id=str(uuid4()),
            session_id=session_id,
            event_type=event_type,
            ts=ts or utc_now(),
            payload=redact_payload(payload),
        )
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event.as_record(), sort_keys=True) + "\n")
        return event
