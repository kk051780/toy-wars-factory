"""Read-only P3 bridge from scoped observer reports to the multi-game planner.

The input reports are serializable and can be forged by a caller. This module
*never* certifies provider origin, GitHub CI, an idle lease or execution rights.
It intentionally reserves capacity and marks all snapshots unverified until a
separately trusted host can attest and reconcile full live PR/CI evidence.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re

from studio_autopilot.scheduler import _validated_games, propose

_SHA = re.compile(r"[0-9a-f]{40}\Z")
_UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
_ROLES = ("author", "reviewer", "meta")
_DENIED = {"dispatch_allowed": False, "merge_allowed": False,
           "publish_allowed": False, "external_spend_allowed": False}
_UNKNOWN_SHA = "0" * 40


class BridgeRejected(ValueError):
    """A report is incomplete, ambiguous or foreign to its project."""


def _need(ok, reason):
    if not ok:
        raise BridgeRejected(reason)


def _sha(value):
    return type(value) is str and value != _UNKNOWN_SHA and _SHA.fullmatch(value) is not None


def _uuid(value):
    return type(value) is str and _UUID.fullmatch(value) is not None


def snapshots_from_reports(projects, reports):
    """Bind service-observer shapes, then deliberately fail closed.

    Only outputs of system_provider_transport.observe(collector="service")
    are the intended inputs. Their JSON shape is NOT an origin credential.
    Even a fully consistent fixture MUST result in blocked plans.
    """
    games = _validated_games(projects)
    expected = {p["game_id"] for p in games}
    _need(type(reports) is dict and set(reports) == expected,
          "EXACT_ONE_REPORT_PER_BOUND_PROJECT_REQUIRED")
    seen_runs = set()
    rows = {}
    receipts = {}
    for game in games:
        gid, repo = game["game_id"], game["repository"]
        report = reports[gid]
        _need(type(report) is dict and set(report) ==
              {"observation", "transport", "verification", "authority"},
              "INVALID_TRANSPORT_REPORT")
        obs, transport = report["observation"], report["transport"]
        _need(type(obs) is dict and type(transport) is dict,
              "INVALID_REPORT_PARTS")
        _need(report["verification"] == "NOT_VERIFIED" and
              obs.get("verification") == "NOT_VERIFIED" and
              transport.get("verification") == "NOT_VERIFIED" and
              obs.get("mode") == "ADVISORY_ONLY" and
              transport.get("mode") == "READ_ONLY_INPUT_ADAPTER" and
              transport.get("repository") == repo and
              obs.get("game_id") == gid and obs.get("repository") == repo and
              transport.get("roles_bound_to_pinned_blobs") is True and
              transport.get("closed") is False,
              "FOREIGN_OR_UNBOUND_REPORT")
        _need(type(transport.get("calls")) is int and 0 < transport["calls"] <= 64 and
              type(transport.get("trace")) is list and transport["trace"] and
              type(obs.get("get_trace")) is list and obs["get_trace"] and
              type(obs.get("peek_trace")) is list and obs["peek_trace"],
              "MISSING_OBSERVATION_TRACE")
        _need(type(report["authority"]) is dict and
              all(report["authority"].get(k) is False for k in _DENIED) and
              all(v is False for v in report["authority"].values()) and
              type(obs.get("authority")) is dict and
              all(obs["authority"].get(k) is False for k in _DENIED) and
              all(v is False for v in obs["authority"].values()) and
              type(transport.get("authority")) is dict and
              all(transport["authority"].get(k) is False for k in _DENIED) and
              all(v is False for v in transport["authority"].values()),
              "AUTHORITY_CLAIMED")
        head, coord, services = obs.get("main_sha"), obs.get("coordinator"), obs.get("services")
        _need(_sha(head) and type(coord) is dict and type(services) is dict and
              set(services) == set(_ROLES), "MISSING_BOUND_STATE")
        _need(_sha(coord.get("ref_sha")) and _sha(coord.get("blob_sha")) and
              type(coord.get("epoch")) is int and coord["epoch"] >= 0 and
              (coord.get("holder") is None or type(coord["holder"]) is dict),
              "INVALID_COORDINATOR_BINDING")
        for role in _ROLES:
            svc = services[role]
            _need(type(svc) is dict and svc.get("task_id") == game["roles"][role] and
                  type(svc.get("last_run")) is dict and
                  _uuid(svc["last_run"].get("id")),
                  "WRONG_SERVICE_IDENTITY")
            run_id = svc["last_run"]["id"]
            _need(run_id not in seen_runs, "REPLAYED_OR_CROSS_PROJECT_RUN")
            seen_runs.add(run_id)
        # No provider provenance or exact PR/CI chain is authenticated here.
        # Never synthesize success, available PR slots or an idle lease.
        rows[gid] = {"repository": repo, "main_sha": head, "qa_sha": _UNKNOWN_SHA,
                     "qa": "PENDING", "lease_epoch": coord["epoch"],
                     "holder": "UNVERIFIED_LEASE_STATE", "open_prs": game["safety"]["max_open_prs"],
                     "last_served_cycle": -1, "live_read_claim": False}
        # A digest is a stable local correlation key, NOT a signature.
        receipts[gid] = {"verification": "NOT_VERIFIED", "repository": repo,
                         "main_sha": head, "coordinator_sha": coord["ref_sha"],
                         "coordinator_blob_sha": coord["blob_sha"], "epoch": coord["epoch"],
                         "trace_sha256": sha256(json.dumps(transport["trace"], sort_keys=True).encode()).hexdigest(),
                         "origin_attested": False, "exact_ci_attested": False}
    return {"snapshots": rows, "receipts": receipts,
            "verification": "NOT_VERIFIED", "authority": dict(_DENIED)}


def plan_advisory(projects, reports, signals, *, cycle, max_slots=1, occupied_slots=0):
    prepared = snapshots_from_reports(projects, reports)
    outcome = propose(projects, prepared["snapshots"], signals, cycle=cycle,
                      max_slots=max_slots, occupied_slots=occupied_slots)
    _need(outcome["execution"] == _DENIED and all(
          p["dispatch_allowed"] is False and p["selected"] is False and
          p["merge_allowed"] is False and p["publish_allowed"] is False and
          p["external_spend_allowed"] is False for p in outcome["candidates"]),
          "UNVERIFIED_CANDIDATE_PROMOTED")
    return {"plan": outcome, "receipts": prepared["receipts"],
            "verification": "NOT_VERIFIED", "authority": dict(_DENIED)}
