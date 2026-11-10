"""Offline-only oracle for the pure Luau ProgressViewModel contract.

No persistence or awards; server ownership is a prerequisite enforced by the caller.
"""
from __future__ import annotations
import math
import re
from typing import Any

VALID_ID = re.compile(r"^[a-zA-Z0-9_.-]+$")
MAX_XP = 1_000_000_000
MAX_EPOCH = 1_000_000_000


def valid_id(value: Any, maximum: int) -> bool:
    return isinstance(value, str) and 0 < len(value) <= maximum and bool(VALID_ID.fullmatch(value))


def strict_integer(value: Any, lo: int, hi: int) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value) and value.is_integer() and lo <= value <= hi


def valid_progress(xp: Any, required: Any, at_max: bool) -> bool:
    if not strict_integer(xp, 0, MAX_XP) or not strict_integer(required, 0, MAX_XP):
        return False
    if at_max:
        return xp == required == 0
    return required > 0 and xp < required


def project(snapshot: Any, viewer_id: Any, match_id: Any, epoch: Any, approved_job_ids: Any):
    if not valid_id(viewer_id, 96) or not valid_id(match_id, 96) or not strict_integer(epoch, 0, MAX_EPOCH):
        return None, "INVALID_CONTEXT"
    if not isinstance(approved_job_ids, list) or len(approved_job_ids) != 7 or any(not valid_id(job_id, 32) for job_id in approved_job_ids) or len(set(approved_job_ids)) != 7:
        return None, "INVALID_JOB_ALLOWLIST"
    if not isinstance(snapshot, dict) or snapshot.get("authority") != "SERVER" or snapshot.get("playerId") != viewer_id or snapshot.get("matchId") != match_id or snapshot.get("epoch") != epoch or snapshot.get("roundActive") is not True:
        return None, "INVALID_SNAPSHOT_IDENTITY"
    if not strict_integer(snapshot.get("level"), 1, 25) or not isinstance(snapshot.get("mastery"), dict):
        return None, "INVALID_PROGRESSION"
    maxed = snapshot["level"] == 25
    if not valid_progress(snapshot.get("levelXp"), snapshot.get("levelRequiredXp"), maxed):
        return None, "INVALID_LEVEL_XP"
    mastery = snapshot["mastery"]
    if any(j not in approved_job_ids for j in mastery):
        return None, "UNKNOWN_JOB"
    if set(mastery) != set(approved_job_ids):
        return None, "INVALID_JOB_COUNT"
    result_jobs = []
    for job_id in approved_job_ids:
        entry = mastery[job_id]
        if not isinstance(entry, dict) or not strict_integer(entry.get("level"), 0, 5):
            return None, "INVALID_MASTERY"
        max_job = entry["level"] == 5
        if not valid_progress(entry.get("xp"), entry.get("requiredXp"), max_job):
            return None, "INVALID_MASTERY_XP"
        result_jobs.append({
            "jobId": job_id, "label": f"{job_id} 熟練 {int(entry['level'])}/5",
            "level": entry["level"], "xp": entry["xp"], "requiredXp": entry["requiredXp"],
            "fraction": 1 if max_job else entry["xp"] / entry["requiredXp"], "maxed": max_job,
        })
    view = {
        "playerId": viewer_id, "matchId": match_id, "epoch": epoch,
        "level": snapshot["level"], "levelLabel": f"Lv {int(snapshot['level'])}/25",
        "levelXp": snapshot["levelXp"], "levelRequiredXp": snapshot["levelRequiredXp"],
        "levelFraction": 1 if maxed else snapshot["levelXp"] / snapshot["levelRequiredXp"],
        "maxLevel": maxed, "jobs": result_jobs, "jobCount": 7,
        "sessionOnly": snapshot.get("sessionOnly") is True,
        "saved": snapshot.get("saved") is True,
        "grantsGameplayStats": False,
    }
    return view, None
