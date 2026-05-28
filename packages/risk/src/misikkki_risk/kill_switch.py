from __future__ import annotations

from datetime import datetime

from misikkki_core.models import utc_now
from misikkki_risk.engine import RiskState


def activate_kill_switch(state: RiskState, reason: str, *, at: datetime | None = None) -> dict[str, str]:
    activated_at = at or utc_now()
    state.kill_switch_active = True
    state.kill_switch_reason = reason
    return {
        "event": "kill_switch_activated",
        "reason": reason,
        "activated_at": activated_at.isoformat(),
    }
