#!/usr/bin/env python3
"""P0 two-writer SHADOW registry: proposal and fake-host CAS only.

Inputs, times, actor UUIDs and callbacks are UNTRUSTED. This is NOT a
provider-authenticated lease, a GitHub writer grant or a deployed migration.
The old exclusive coordinator remains authoritative. No host/network client.
"""
from __future__ import annotations
import copy
from datetime import datetime, timedelta
import re
from system_parallel_scope_admission import _scope, compare_claims

HEX = re.compile(r"[0-9a-f]{40}\Z")
UUID = re.compile(r"[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\Z")
KEY = "shadow_parallel_leases"
MAX_AGE = timedelta(minutes=30)

def require(cond, why):
    if not cond:
        raise ValueError(why)

def instant(value):
    require(type(value) is str and len(value) <= 40, "timestamp type")
    d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(d.tzinfo is not None and d.utcoffset() == timedelta(0), "UTC required")
    return d

def uuid(value):
    require(type(value) is str and UUID.fullmatch(value) is not None, "UUID required")

def scope(value, repo, main):
    s = _scope(value)
    require(s["repo"] == repo and s["base"] == main and
            s["status"] == "ACTIVE", "scope repository/base/status")
    require(not s["exclusive"], "protected write needs legacy exclusive lane")
    return s

def inspect(snapshot):
    require(type(snapshot) is dict and set(snapshot) ==
            {"repository", "main_sha", "ref_sha", "state"}, "snapshot shape")
    repo, main, ref = (snapshot[k] for k in ("repository", "main_sha", "ref_sha"))
    require(type(repo) is str and type(main) is str and HEX.fullmatch(main) and
            type(ref) is str and HEX.fullmatch(ref), "ref or repository")
    state = snapshot["state"]
    require(type(state) is dict and state.get("schema") == 1 and
            type(state.get("epoch")) is int and state["epoch"] >= 0 and
            "holder" in state, "legacy state shape")
    reg = state.get(KEY, {"schema": 1, "entries": []})
    require(type(reg) is dict and set(reg) == {"schema", "entries"} and
            reg["schema"] == 1 and type(reg["entries"]) is list and
            len(reg["entries"]) <= 2, "registry shape")
    ids, runs, owners, nonces, branches = set(), set(), set(), set(), set()
    for entry in reg["entries"]:
        require(type(entry) is dict and set(entry) ==
                {"scope", "owner_id", "run_id", "nonce", "lease_epoch",
                 "acquired_at", "expires_at"}, "entry shape")
        for k in ("owner_id", "run_id", "nonce"):
            uuid(entry[k])
        s = scope(entry["scope"], repo, main)
        require(type(entry["lease_epoch"]) is int and
                0 < entry["lease_epoch"] <= state["epoch"], "lease epoch")
        start, until = instant(entry["acquired_at"]), instant(entry["expires_at"])
        require(timedelta(0) < until - start <= MAX_AGE, "lease age")
        require(s["id"] not in ids and s["branch"] not in branches and
                entry["owner_id"] not in owners and entry["run_id"] not in runs and
                entry["nonce"] not in nonces, "duplicate identity")
        ids.add(s["id"])
        branches.add(s["branch"])
        owners.add(entry["owner_id"])
        runs.add(entry["run_id"])
        nonces.add(entry["nonce"])
    return state, reg["entries"]

def answer(decision, new=None, expected=None):
    return {"decision": decision, "state": new, "expected_sha": expected,
            "may_write": False, "may_dispatch": False,
            "github_authenticated": False, "parallel_real": False}

def claim(snapshot, req, now):
    """Advisory CAS state proposal; NEVER authorizes worker execution."""
    try:
        state, entries = inspect(snapshot)
        require(state["holder"] is None, "legacy holder is active")
        require(type(req) is dict and set(req) ==
                {"scope", "owner_id", "run_id", "nonce", "expires_at"}, "request shape")
        for k in ("owner_id", "run_id", "nonce"):
            uuid(req[k])
        current, until = instant(now), instant(req["expires_at"])
        require(timedelta(0) < until - current <= MAX_AGE, "requested expiry")
        s = scope(req["scope"], snapshot["repository"], snapshot["main_sha"])
        for e in entries:
            old = scope(e["scope"], snapshot["repository"], snapshot["main_sha"])
            if old["id"] == s["id"]:
                return answer("JOIN_UNVERIFIED" if
                              e["scope"] == req["scope"] and
                              all(e[k] == req[k] for k in ("owner_id", "run_id", "nonce"))
                              else "WAIT_WORK_ID_OWNED")
        require(all(e[k] != req[k] for e in entries
                    for k in ("owner_id", "run_id", "nonce")), "actor reused")
        require(all(instant(e["acquired_at"]) <= current <
                    instant(e["expires_at"]) for e in entries),
                "expired leases need authenticated recovery")
        result = compare_claims([e["scope"] for e in entries], req["scope"])
        if result["decision"] != "PROPOSE_DISJOINT":
            return answer(result["decision"])
        new = copy.deepcopy(state)
        new.setdefault(KEY, {"schema": 1, "entries": []})
        new["epoch"] += 1
        new[KEY]["entries"].append({
            "scope": copy.deepcopy(req["scope"]),
            **{k: req[k] for k in ("owner_id", "run_id", "nonce")},
            "lease_epoch": new["epoch"], "acquired_at": now,
            "expires_at": req["expires_at"]})
        return answer("SHADOW_CLAIM_CAS_PROPOSAL", new, snapshot["ref_sha"])
    except (KeyError, TypeError, ValueError) as error:
        return answer("WAIT_INVALID_" + str(error)[:70])

def release(snapshot, req, now):
    """Releases own shadow row only, never steals/recovers other leases."""
    try:
        state, entries = inspect(snapshot)
        require(state["holder"] is None, "legacy holder active")
        require(type(req) is dict and set(req) ==
                {"work_id", "owner_id", "run_id", "nonce"}, "release shape")
        for k in ("owner_id", "run_id", "nonce"):
            uuid(req[k])
        matches = [e for e in entries if e["scope"]["work_id"] == req["work_id"]]
        require(len(matches) == 1, "work id not found")
        own = matches[0]
        require(all(own[k] == req[k] for k in ("owner_id", "run_id", "nonce")),
                "foreign release")
        require(instant(own["acquired_at"]) <= instant(now) <
                instant(own["expires_at"]), "expired requires service evidence")
        new = copy.deepcopy(state)
        new[KEY]["entries"] = [e for e in entries if e is not own]
        # Deep-copy identity means old 'own' objects are not in new. Re-select by ID.
        new[KEY]["entries"] = [e for e in new[KEY]["entries"]
                                if e["scope"]["work_id"] != req["work_id"]]
        new["epoch"] += 1
        return answer("SHADOW_RELEASE_CAS_PROPOSAL", new, snapshot["ref_sha"])
    except (KeyError, TypeError, ValueError) as error:
        return answer("WAIT_INVALID_" + str(error)[:70])

def apply_once(snapshot, proposal, *, read, cas, clock, requested_at):
    """Single injected fake-host CAS + double readback; no trusted provider."""
    def wait(reason, attempted=False):
        return {"status": reason, "cas_attempted": attempted, "may_write": False,
                "github_authenticated": False, "parallel_real": False}
    action = proposal.get("decision")
    if action not in ("SHADOW_CLAIM_CAS_PROPOSAL", "SHADOW_RELEASE_CAS_PROPOSAL"):
        return wait("WAIT_NOT_PROPOSED")
    try:
        require(read() == read() == snapshot, "pre-CAS drift")
        previous, oldrows = inspect(snapshot)
        now = instant(clock())
        require(instant(requested_at) <= now <=
                instant(requested_at) + MAX_AGE, "clock not fresh")
        require(previous["holder"] is None, "legacy holder active")
        require(all(now < instant(e["expires_at"]) for e in oldrows),
                "prior lease expired")
        next_state = proposal["state"]
        require(type(next_state) is dict and
                next_state["epoch"] == previous["epoch"] + 1, "epoch increment")
        require(set(next_state) == set(previous) | {KEY}, "foreign field")
        require(all(next_state[k] == previous[k] for k in previous
                    if k not in ("epoch", KEY)), "foreign state mutated")
        _, newrows = inspect({**snapshot, "state": next_state})
        if action == "SHADOW_CLAIM_CAS_PROPOSAL":
            require(newrows[:-1] == oldrows and len(newrows) == len(oldrows) + 1,
                    "claim changed incumbent")
            added = newrows[-1]
            require(added["lease_epoch"] == next_state["epoch"] and
                    instant(added["acquired_at"]) <= now <
                    instant(added["expires_at"]), "new claim expired")
            require(compare_claims([e["scope"] for e in oldrows],
                                   added["scope"])["decision"] == "PROPOSE_DISJOINT",
                    "claim scope changed")
        else:
            require(len(oldrows) == len(newrows) + 1 and
                    all(newrows.count(e) == oldrows.count(e) for e in newrows),
                    "release modified other row")
    except Exception:
        return wait("WAIT_PRECAS_UNCONFIRMED")
    try:
        newref = cas(proposal["expected_sha"], copy.deepcopy(next_state))
    except Exception:
        return wait("WAIT_CAS_ACK_UNKNOWN", True)
    if type(newref) is not str or HEX.fullmatch(newref) is None or newref == proposal["expected_sha"]:
        return wait("WAIT_CAS_CONFLICT_OR_BAD_ACK", True)
    try:
        a, b = read(), read()
        require(a == b and a["ref_sha"] == newref and a["state"] == next_state and
                a["repository"] == snapshot["repository"] and
                a["main_sha"] == snapshot["main_sha"], "post-CAS drift")
    except Exception:
        return wait("WAIT_CAS_READBACK_UNKNOWN", True)
    return wait("MOCK_CAS_READBACK_ONLY_NO_AUTHORITY", True)
