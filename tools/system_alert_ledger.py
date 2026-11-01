"""Pure, bounded alert-ledger proposal; no storage, provider, sender or authority.

Feed a fresh accepted runtime/idle frame (previous=None at observation time).
The host must obtain the prior ledger and its digest independently from an
immutable GitHub blob, and bind a current owned META/REVIEWER fence. Matching
JSON/digests are integrity checks, NEVER provider authentication or a lease.
After this function the host must reread live source/lease/ref and use fenced
expected_sha + force=False. No function here performs that write or delivery.
Ledger history is bounded by the accepted replay window/capacity; expiration
requires independent archival/review, never silent deletion or fake recovery.
"""
from copy import deepcopy
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools")]
from tools import system_runtime_alerts as runtime

need, moment, EvidenceError = runtime.need, runtime.moment, runtime.EvidenceError
digest = runtime._digest
LEDGER = {"schema", "mode", "verification", "game_id", "repository", "roles",
          "created_at", "revision", "last_observation_digest", "frame", "delivery",
          "recovery_verification", "a12_verified", "authority"}
FENCE = {"repository", "coordination_ref", "expected_ref_sha", "observed_at", "epoch",
         "actor_role", "actor_task_id", "actor_run_id", "holder", "previous_digest"}
HOLDER = {"kind", "owner_id", "task_id", "epoch", "acquired_at", "expires_at",
          "base_main_sha", "work_branch", "origin"}
SERVICE_KINDS = runtime.KINDS - {"CONNECTOR_UNAVAILABLE", "INDETERMINATE", "CI_TIMEOUT",
                               "MAIN_QA_FAILED", "PR_QA_FAILED", "EXPIRED_LEASE_UNRELEASED"}


def _scope(project, frame, now):
    runtime._validate_frame(frame, now)
    need(all(frame[k] == project[k] for k in ("game_id", "repository", "roles")), "FOREIGN_LEDGER_FRAME")
    need(frame["services"] or (len(frame["alerts"]) == 1 and
         frame["alerts"][0]["identity"]["kind"] == "CONNECTOR_UNAVAILABLE"), "MISSING_SERVICE_OBSERVATION")
    need(len({r["run_id"] for r in frame["services"]}) == len(frame["services"]), "CROSS_ROLE_RUN_REUSE")
    for row in frame["services"]:
        need(row["state"] != "OBSERVED_COMPLETED" or row["latest_result_binding"] == "CURRENT_RUN",
             "PREVIOUS_RESULT_IS_NOT_CURRENT_SUCCESS")
    required = {(r["state"], digest({k:r[k] for k in ("role", "task_id", "run_id")}))
                for r in frame["services"] if r["state"] in SERVICE_KINDS}
    required |= {(r["state"], digest({k:v for k,v in r.items() if k not in ("state", "age_seconds")}))
                 for r in frame["ci"] if r["state"] in runtime.KINDS}
    lease = frame["lease"]
    if lease and lease["state"] == "EXPIRED_LEASE_UNRELEASED":
        required.add((lease["state"], digest({k:v for k,v in lease.items() if k != "state"})))
    actual = set()
    for a in frame["alerts"]:
        ident = a["identity"]; kind, subject = ident["kind"], ident["subject"]
        key = (kind, digest(subject)); actual.add(key)
        if kind == "CONNECTOR_UNAVAILABLE":
            need(not frame["services"] and not frame["ci"] and lease is None, "CONTRADICTORY_OUTAGE")
        elif key not in required:
            # Accepted idle observer also flags a terminal owner retaining a lease.
            need(kind == "STALE_OR_NO_RESULT" and lease is not None and
                 lease["owner_run_id"] == subject["run_id"] and any(
                     all(row.get(k) == v for k,v in subject.items()) and
                     row["state"] != "IN_PROGRESS_NOT_YET_STALE" for row in frame["services"]),
                 "ALERT_NOT_BOUND_TO_OBSERVATION")
    need(required <= actual, "MISSING_REQUIRED_INCIDENT")


def _fresh(frame):
    value = deepcopy(frame)
    value["recovery_candidates"] = []
    for a in value["alerts"]:
        a.update(first_seen=value["observed_at"], last_seen=value["observed_at"], repeats=1)
    return value


def _fence(project, fence, now):
    need(type(fence) is dict and set(fence) == FENCE and fence["repository"] == project["repository"] and
         fence["coordination_ref"] == project["coordination_ref"], "INVALID_LEDGER_FENCE")
    runtime.github.sha(fence["expected_ref_sha"])
    role = fence["actor_role"]
    need(role in ("meta", "reviewer") and fence["actor_task_id"] == project["roles"][role], "UNREGISTERED_LEDGER_ACTOR")
    runtime.service.run_id(fence["actor_run_id"])
    h = fence["holder"]
    need(type(h) is dict and set(h) == HOLDER and h["kind"] == runtime.service.ROLES[role] and
         h["owner_id"] == fence["actor_run_id"] and h["task_id"] == fence["actor_task_id"] and
         runtime.github.integer(fence["epoch"], 0) and type(h["epoch"]) is int and h["epoch"] == fence["epoch"],
         "FENCE_NOT_OWNED")
    acquired, expires, at = moment(h["acquired_at"]), moment(h["expires_at"]), moment(fence["observed_at"])
    need(acquired <= at <= now < expires and 0 < (expires-acquired).total_seconds() <= 1800 and
         (now-at).total_seconds() <= 120, "EXPIRED_OR_STALE_LEDGER_FENCE")
    runtime.github.sha(h["base_main_sha"])
    need(type(h["work_branch"]) is str and 0 < len(h["work_branch"]) <= 200 and
         runtime.github.re.fullmatch(r"[A-Za-z0-9_./-]+", h["work_branch"]) and
         not h["work_branch"].startswith("/") and ".." not in h["work_branch"] and
         h["origin"] == role and (h["work_branch"] == "main" if role == "reviewer" else
         h["work_branch"].endswith(fence["actor_run_id"])), "INVALID_LEDGER_LANE")


def _prior(project, previous, expected, now):
    if previous is None:
        need(expected is None, "MISSING_PREVIOUS_LEDGER")
        return
    need(type(expected) is str and runtime.github.re.fullmatch(r"[0-9a-f]{64}", expected) and
         digest(previous) == expected, "PREVIOUS_LEDGER_DIGEST_MISMATCH")
    need(type(previous) is dict and set(previous) == LEDGER and type(previous["schema"]) is int and
         previous["schema"] == 1 and previous["mode"] == "PROVISIONAL_ALERT_LEDGER" and
         previous["verification"] == "NOT_VERIFIED" and previous["delivery"] == "NOT_ATTEMPTED" and
         previous["recovery_verification"] == "NOT_VERIFIED" and previous["a12_verified"] is False and
         runtime.github.integer(previous["revision"]) and previous["revision"] <= 10000 and
         all(previous[k] == project[k] for k in ("game_id", "repository", "roles")), "FORGED_PREVIOUS_LEDGER")
    runtime._denied(previous["authority"])
    frame = previous["frame"]
    _scope(project, frame, now)
    need(previous["last_observation_digest"] == digest(_fresh(frame)) and
         moment(previous["created_at"]) <= moment(frame["observed_at"]) and
         frame["alerts"] + frame["recovery_candidates"], "FORGED_LEDGER_CHECKPOINT")
    for a in frame["alerts"] + frame["recovery_candidates"]:
        need(a["repeats"] <= previous["revision"] and moment(previous["created_at"]) <= moment(a["first_seen"]),
             "FORGED_LEDGER_COUNTER_OR_TIME")


def reduce(projects, previous, current, fence, observed_at):
    """Validate supplied data, propose JSON only. Duplicate input returns no change.

    previous_digest is a host-side immutable-blob anchor, not an authentication
    label; if caller controls both prior JSON and anchor, origin is NOT_VERIFIED.
    Exceptions contain only fixed error codes; malformed input never looks green.
    """
    try:
        return _reduce(deepcopy(projects), deepcopy(previous), deepcopy(current), deepcopy(fence), moment(observed_at))
    except EvidenceError:
        raise
    except Exception:
        raise EvidenceError("INVALID_LEDGER_INPUT") from None


def _reduce(projects, previous, current, fence, now):
    games = runtime.service.scheduler._validated_games(projects)
    need(type(current) is dict, "INVALID_LEDGER_FRAME")
    chosen = [p for p in games if p["game_id"] == current.get("game_id")]
    need(len(chosen) == 1, "UNKNOWN_LEDGER_PROJECT")
    project = chosen[0]
    _scope(project, current, now)
    need(not current["recovery_candidates"] and current == _fresh(current) and
         (now-moment(current["observed_at"])).total_seconds() <= current["thresholds"]["max_observation_age_seconds"],
         "FRESH_UNRECONCILED_FRAME_REQUIRED")
    _fence(project, fence, now)
    _prior(project, previous, fence["previous_digest"], now)
    fingerprint = digest(current)
    if previous is not None and fingerprint == previous["last_observation_digest"]:
        ledger, reason = previous, "DUPLICATE_OBSERVATION"
        changed = False
    elif previous is None and not current["alerts"]:
        ledger, changed, reason = None, False, "NO_INCIDENT_OBSERVED"
    else:
        merged = runtime.reconcile(None if previous is None else previous["frame"], current)
        ledger = {"schema": 1, "mode": "PROVISIONAL_ALERT_LEDGER", "verification": "NOT_VERIFIED",
                  "game_id": project["game_id"], "repository": project["repository"], "roles": project["roles"],
                  "created_at": current["observed_at"] if previous is None else previous["created_at"],
                  "revision": 1 if previous is None else previous["revision"]+1,
                  "last_observation_digest": fingerprint, "frame": merged, "delivery": "NOT_ATTEMPTED",
                  "recovery_verification": "NOT_VERIFIED", "a12_verified": False, "authority": deepcopy(runtime.DENIED)}
        need(ledger["revision"] <= 10000, "LEDGER_REVIEW_REQUIRED")
        _prior(project, ledger, digest(ledger), now)
        changed, reason = True, "VALIDATED_PROVISIONAL_CHANGE"
    uncertain = any(a["identity"]["kind"] in ("CONNECTOR_UNAVAILABLE", "INDETERMINATE") for a in current["alerts"])
    return {"schema": 1, "mode": "PURE_LEDGER_REDUCER", "verification": "NOT_VERIFIED", "changed": changed,
            "reason": reason, "observation": "UNASSESSABLE" if uncertain else "OBSERVED",
            "ledger": ledger, "proposal": None if not changed else {
                "coordination_ref": project["coordination_ref"], "expected_sha": fence["expected_ref_sha"],
                "force": False, "epoch": fence["epoch"], "actor_task_id": fence["actor_task_id"],
                "actor_run_id": fence["actor_run_id"], "previous_digest": fence["previous_digest"],
                "content_digest": digest(ledger), "requirement": "HOST_LIVE_SOURCE_LEASE_REF_REREAD_AND_FENCED_CAS"},
            "delivery": "NOT_ATTEMPTED", "recovery_verification": "NOT_VERIFIED", "a12_verified": False,
            "authority": deepcopy(runtime.DENIED)}
