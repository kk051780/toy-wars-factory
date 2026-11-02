"""Advisory timing audit for a manual DISPATCH and a ChatGPT WORKER run.

Never authenticates a run_now request, host origin, or GitHub writer. Original
provider-bound correlation is REQUIRED before any adoption/write decision.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import re
import uuid

WORKER_TASK = "6adbf0d6a7d881918ce181dff2468867"
TICKET_KEYS = {"epoch", "owner_id", "acquired_at", "expires_at"}
RUN_KEYS = {"task_id", "id", "scheduled_for", "started_at", "completed_at", "recorded_status", "chat_ref"}
TERMINAL = {"completed", "failed", "no_update"}


class EvidenceError(ValueError):
    """Fixed, non-sensitive evidence validation error."""


def _need(check, code):
    if not check:
        raise EvidenceError(code)


def _instant(value):
    _need(type(value) is str and len(value) <= 48 and
          re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,6})?(?:Z|[+-]\d\d:\d\d)", value),
          "INVALID_INSTANT")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
        _need(result.tzinfo is not None, "INVALID_INSTANT")
        return result.astimezone(timezone.utc)
    except (ValueError, OverflowError):
        raise EvidenceError("INVALID_INSTANT") from None


def _uuid(value):
    try:
        _need(type(value) is str and str(uuid.UUID(value)) == value, "INVALID_UUID")
    except (ValueError, AttributeError):
        raise EvidenceError("INVALID_UUID") from None


def audit(ticket, run):
    """Return NON-AUTHORIZING observation, never a dispatch causation proof.

    All observations are caller supplied. A completed-run chat_ref also cannot
    retrospectively prove the execution's in-run provider binding.
    """
    _need(type(ticket) is dict and set(ticket) == TICKET_KEYS, "INVALID_TICKET_SHAPE")
    _need(type(run) is dict and set(run) == RUN_KEYS, "INVALID_RUN_SHAPE")
    _need(type(ticket["epoch"]) is int and ticket["epoch"] > 0, "INVALID_EPOCH")
    _uuid(ticket["owner_id"])
    _uuid(run["id"])
    _need(run["task_id"] == WORKER_TASK, "WRONG_TASK")
    _need(type(run["recorded_status"]) is str and run["recorded_status"] in TERMINAL, "RUN_NOT_TERMINAL")
    _need(run["chat_ref"] is None or
          (type(run["chat_ref"]) is dict and set(run["chat_ref"]) == {"type", "id"} and
           run["chat_ref"]["type"] == "chatgpt" and
           type(run["chat_ref"]["id"]) is str and len(run["chat_ref"]["id"]) <= 128),
          "INVALID_CHAT_REF")
    acq, exp = _instant(ticket["acquired_at"]), _instant(ticket["expires_at"])
    due, started, ended = (_instant(run[k]) for k in ("scheduled_for", "started_at", "completed_at"))
    _need(exp - acq == timedelta(seconds=120), "INVALID_DISPATCH_TTL")
    _need(started <= ended, "INVALID_RUN_CHRONOLOGY")
    if due < acq:
        state = "SCHEDULED_BEFORE_DISPATCH"
    elif started >= exp:
        state = "STARTED_AFTER_EXPIRY"
    elif started < acq:
        state = "STARTED_BEFORE_DISPATCH"
    else:
        state = "WITHIN_TTL_BUT_UNATTRIBUTED"
    return {"schema": 1, "state": state, "attribution": "UNATTRIBUTED",
            "cause": "INDETERMINATE", "provider_run_binding_verified": False,
            "may_adopt": False, "may_write": False, "may_extend_ticket": False,
            "may_recover_foreign": False, "may_dispatch": False}
