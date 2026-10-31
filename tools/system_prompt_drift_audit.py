"""Offline, non-authorizing audit of exported *untrusted* Automations snapshots.

Never contacts the provider, starts a task, mutates a prompt, or certifies that
JSON came from Automations.peek. A connected trusted caller must get fresh task
observations independently, and must not treat this report as authorisation.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

REPO = "kk051780/toy-wars-factory"
COORDINATOR = "twf-repair-coordinator"
ROLES = {
    "WORKER": {
        "task_id": "6adbf0d6a7d881918ce181dff2468867",
        "compacted_utf16_chars": 7346,
        "schedule": "BEGIN:VEVENT\nDTSTART:20261024T050504Z\nRRULE:FREQ=HOURLY\nEND:VEVENT",
    },
    "META": {
        "task_id": "6add445e4138819197d9cf2b1a02534d",
        "compacted_utf16_chars": 6577,
        "schedule": "BEGIN:VEVENT\nDTSTART;TZID=Asia/Tokyo:20261030T074500\nRRULE:FREQ=HOURLY\nEND:VEVENT",
    },
    "REVIEWER": {
        "task_id": "6add6aaceb4c8191b1666fe15f97cd88",
        "compacted_utf16_chars": 7438,
        "schedule": "BEGIN:VEVENT\nDTSTART;TZID=Asia/Tokyo:20261025T122500\nRRULE:FREQ=HOURLY\nEND:VEVENT",
    },
}
# These are *textual review hints*, NOT proof of policy compliance or negation.
# A human/security reviewer must examine complete effective task instructions.
ANCHORS = {
    "repo": (REPO,),
    "coordinator": (COORDINATOR,),
    "fresh_run": ("PEEK",),
    "fenced_write": ("CAS",),
    "independent_review": ("REVIEWER", "independent"),
    "quality_check": ("CI",),
    "gemini_incident": ("Gemini",),
    "roblox_release_hold": ("Roblox",),
    "spending_boundary": ("spend", "budget", "cost", "fee"),
    "publication_boundary": ("publish", "publication", "public release"),
}
RUN_STATUSES = frozenset({"in_progress", "completed", "failed", "no_update"})
HEX_UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
FLAGS = {
    "write_allowed": False,
    "start_now_allowed": False,
    "takeover_allowed": False,
    "dispatch_allowed": False,
    "merge_allowed": False,
    "publish_allowed": False,
    "external_spend_allowed": False,
    "prompt_edit_allowed": False,
}


class UnsafeSnapshot(ValueError):
    pass


def _exact(value: Any, keys: set[str], name: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != keys:
        raise UnsafeSnapshot("invalid " + name + " fields")
    return value


def _time(value: Any, name: str) -> datetime:
    if type(value) is not str:
        raise UnsafeSnapshot("missing " + name)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise UnsafeSnapshot("malformed " + name) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise UnsafeSnapshot("naive " + name)
    return parsed.astimezone(timezone.utc)


def utf16_units(s: str) -> int:
    # Same length unit as JavaScript String.length and saved-task observations.
    return len(s.encode("utf-16-le")) // 2


def _run(item: Any, observed: datetime) -> tuple[str, list[str]]:
    if item is None:
        return "unknown", ["MISSING_LAST_RUN"]
    _exact(item, {"id", "recorded_status", "started_at", "completed_at", "chat_ref"}, "run")
    if type(item["id"]) is not str or not HEX_UUID.fullmatch(item["id"]):
        raise UnsafeSnapshot("invalid run UUID")
    if type(item["recorded_status"]) is not str or item["recorded_status"] not in RUN_STATUSES:
        raise UnsafeSnapshot("invalid run status")
    started = _time(item["started_at"], "started_at")
    if started > observed:
        raise UnsafeSnapshot("run starts after observation")
    done = item["completed_at"]
    if done is not None:
        completed = _time(done, "completed_at")
        if completed < started or completed > observed:
            raise UnsafeSnapshot("invalid completion chronology")
    if (item["recorded_status"] == "in_progress") != (done is None):
        raise UnsafeSnapshot("inconsistent in-progress/terminal result")
    chat = item["chat_ref"]
    if chat is not None:
        _exact(chat, {"type", "id"}, "chat reference")
        if chat["type"] not in ("chatgpt", "codex") or type(chat["id"]) is not str or not chat["id"]:
            raise UnsafeSnapshot("invalid chat reference")
    warnings = []
    status = item["recorded_status"]
    if status == "no_update":
        warnings.append("LAST_RUN_NO_UPDATE_CAUSE_UNKNOWN")
    if status == "failed":
        warnings.append("LAST_RUN_FAILED_CAUSE_UNKNOWN")
    if status == "in_progress":
        warnings.append("RUN_IN_PROGRESS_NO_PROMPT_MUTATION")
    return status, warnings


def audit(data: Any) -> dict[str, Any]:
    """Return only a read-only diagnostic. Never turns supplied JSON into auth."""
    base = {"schema": 1, "mode": "READ_ONLY_REPORT", "verification": "NOT_VERIFIED",
            "source_authority": "CALLER_SUPPLIED_SNAPSHOTS", "authority": dict(FLAGS),
            "changes_applied": False}
    try:
        root = _exact(data, {"schema", "repository", "observed_at", "snapshots"}, "root")
        if type(root["schema"]) is not int or root["schema"] != 1 or root["repository"] != REPO:
            raise UnsafeSnapshot("incorrect schema or repository")
        observed = _time(root["observed_at"], "observed_at")
        rows = root["snapshots"]
        if type(rows) is not list or len(rows) != 3:
            raise UnsafeSnapshot("exact three role snapshots required")
        seen: set[str] = set()
        report = []
        for row in rows:
            _exact(row, {"role", "task_id", "is_enabled", "schedule", "prompt", "last_run"}, "task")
            role = row["role"]
            if type(role) is not str or role not in ROLES or role in seen:
                raise UnsafeSnapshot("duplicate or unknown role")
            seen.add(role)
            conf = ROLES[role]
            if type(row["task_id"]) is not str or row["task_id"] != conf["task_id"]:
                raise UnsafeSnapshot("foreign task ID for " + role)
            if type(row["is_enabled"]) is not bool:
                raise UnsafeSnapshot("invalid enabled value")
            prompt = row["prompt"]
            if type(prompt) is not str or not prompt or utf16_units(prompt) > 65536:
                raise UnsafeSnapshot("missing or excessive task prompt")
            if type(row["schedule"]) is not str or len(row["schedule"]) > 2048:
                raise UnsafeSnapshot("invalid schedule")
            length = utf16_units(prompt)
            before = conf["compacted_utf16_chars"]
            delta = length - before
            warnings = []
            if not row["is_enabled"]:
                warnings.append("TASK_DISABLED")
            if row["schedule"] != conf["schedule"]:
                warnings.append("SCHEDULE_CHANGED_FROM_COMPACTED_BASELINE")
            if delta >= 500 or delta / before >= 0.10:
                warnings.append("PROMPT_REGROWTH_REVIEW")
            if length < before * 0.3:
                warnings.append("UNUSUALLY_SHORT_PROMPT_REVIEW")
            lower = prompt.casefold()
            absent = sorted(name for name, options in ANCHORS.items()
                            if not any(opt.casefold() in lower for opt in options))
            if absent:
                warnings.append("TEXTUAL_SAFETY_ANCHORS_MISSING_REVIEW")
            status, run_warnings = _run(row["last_run"], observed)
            warnings.extend(run_warnings)
            report.append({"role": role, "task_id": conf["task_id"],
                           "prompt_utf16_chars": length, "compacted_baseline_chars": before,
                           "regrowth_chars": delta, "regrowth_pct": round(100 * delta / before, 2),
                           "prompt_sha256": sha256(prompt.encode("utf-8")).hexdigest(),
                           "last_run_status": status, "missing_text_anchors": absent,
                           "warnings": warnings})
        if seen != set(ROLES):
            raise UnsafeSnapshot("missing role")
        report.sort(key=lambda x: list(ROLES).index(x["role"]))
        base.update({"status": "REVIEW_REQUIRED" if any(r["warnings"] for r in report) else "BASELINE_WITHIN_THRESHOLD_UNVERIFIED",
                     "observed_at": root["observed_at"],
                     "total_baseline_chars": sum(r["compacted_baseline_chars"] for r in report),
                     "total_observed_chars": sum(r["prompt_utf16_chars"] for r in report),
                     "total_regrowth_chars": sum(r["regrowth_chars"] for r in report),
                     "roles": report})
    except (UnsafeSnapshot, UnicodeError, OverflowError) as exc:
        base.update({"status": "INVALID_INPUT", "error": str(exc), "roles": []})
    return base


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    out = {}
    for k, v in pairs:
        if k in out:
            raise UnsafeSnapshot("duplicate JSON key")
        out[k] = v
    return out


def _reject_nonfinite(token: str) -> None:
    raise UnsafeSnapshot("invalid numeric value")


def main() -> None:
    parser = argparse.ArgumentParser(description="Offline-only task prompt growth audit; never grants execution")
    parser.add_argument("observation_json", type=Path, help="Locally exported three-role snapshots (UNTRUSTED)")
    args = parser.parse_args()
    try:
        if args.observation_json.stat().st_size > 300000:
            raise UnsafeSnapshot("oversized observation")
        value = json.loads(args.observation_json.read_text("utf-8"),
                           object_pairs_hook=_no_duplicate_keys,
                           parse_constant=_reject_nonfinite)
        output = audit(value)
    except (OSError, UnicodeError, json.JSONDecodeError, UnsafeSnapshot) as exc:
        output = {"schema": 1, "status": "INVALID_INPUT", "error": str(exc),
                  "mode": "READ_ONLY_REPORT", "verification": "NOT_VERIFIED",
                  "authority": dict(FLAGS), "changes_applied": False, "roles": []}
    print(json.dumps(output, ensure_ascii=False, sort_keys=True, indent=2))
    if output["status"] == "INVALID_INPUT":
        raise SystemExit(2)


if __name__ == "__main__":
    main()