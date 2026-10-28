"""Portable dual-origin idea intake and comparison for Studio Autopilot.

No provider access, scheduled execution, or write/merge/publication authorization.
Validated data is NOT evidence of player-market performance or an immutable server log.
Only a provider-backed audit can attest the original GitHub issue/commit origin.

Adapted from manual PR110 b74cace762f671dff268d2109b0dfd47b22d8184.
Its graph traversal and heuristic are retained, not claimed as new META inventions.
Repository/task declarations and hashes are consistency checks, never credentials.
"""
from __future__ import annotations

from collections import deque
from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
import json
import re
from typing import Any
from urllib.parse import urlsplit

VERSION = 2
ORIGINS = {"OWNER_ORIGINAL_IDEA", "WEB_RESEARCH_IDEA", "DERIVED"}
STAGES = ("CAPTURED", "RESEARCHED", "COMPARED", "EXPERIMENT_DESIGNED")
CLOSED = {"DEFERRED", "REJECTED", "FAILED", "WITHDRAWN"}
PROTECTED = {"PROTOTYPE_PR", "OFFLINE_VERIFIED", "INDEPENDENT_APPROVED",
             "MERGED_MAIN_QA", "ENGINE_VERIFIED", "PLAYER_MEASURED", "ADOPTED"}
PROJECT = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
IDENTIFIER = re.compile(r"[A-Z][A-Z0-9_-]{3,79}\Z")
BENEFIT = ("acquisition", "retention", "strategy", "originality")
EFFORT = ("engineering", "qa", "performance")
ROLES = {"WORKER", "META", "REVIEWER"}
SOURCE_KINDS = {"PRIMARY_OFFICIAL", "COMMUNITY_REACTION", "DEVELOPER_CASE",
                "SECONDARY_REPORT", "UNCLASSIFIED"}
METRICS = ("playthrough", "first_play_bounce_lt60s", "first_play_bounce_61_180s",
           "play_days_D2_D7", "play_days_D8_D28", "playtime", "D1", "D7",
           "first_production_funnel", "fun", "originality", "frame_time_p95",
           "engineering_effort", "qa_effort", "regression_risk")
RECORD_KEYS = {"schema", "idea_id", "project_id", "origin", "original_text",
               "original_sha256", "provenance_sha256", "source_ref",
               "captured_at", "owner_priority", "observations",
               "derived_from", "stage", "events", "scope", "domain",
               "variant_of", "duplicate_of"}

class IdeaValidationError(ValueError):
    pass

def require(condition: bool, detail: str) -> None:
    if not condition:
        raise IdeaValidationError(detail)

def _timestamp(value: str) -> datetime:
    require(type(value) is str, "timestamp must be text")
    try:
        value_dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        require(value_dt.tzinfo is not None, "timestamp needs timezone")
        return value_dt.astimezone(timezone.utc)
    except ValueError:
        raise IdeaValidationError("timestamp invalid") from None

def _url(value: str) -> bool:
    try:
        v = urlsplit(value)
        return (v.scheme == "https" and bool(v.hostname)
                and v.username is None and v.password is None
                and v.fragment == "" and not any(x.isspace() for x in value))
    except (TypeError, ValueError):
        return False

def _publication(value, checked_at):
    if value == "NOT_AVAILABLE":
        return
    if type(value) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        try:
            published = datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            raise IdeaValidationError("invalid publication date") from None
        require(published <= _timestamp(checked_at).date(), "publication after check")
    else:
        require(_timestamp(value) <= _timestamp(checked_at), "publication after check")

def _plain(data: Any) -> Any:
    """JSON round trip rejects NaN, functions and nonfinite candidate values."""
    try:
        return json.loads(json.dumps(data, ensure_ascii=False, allow_nan=False))
    except (ValueError, TypeError, OverflowError):
        raise IdeaValidationError("not finite JSON data") from None

def _provenance_hash(record):
    payload = {k: v for k, v in record.items()
               if k not in {"provenance_sha256", "stage", "events"}}
    return sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()

def _scope(scope):
    require(type(scope) is dict and set(scope) == {"repository", "tasks"}, "scope required")
    repo = scope["repository"]
    require(type(repo) is str and re.fullmatch(r"[a-z0-9][a-z0-9_.-]*/[a-z0-9][a-z0-9_.-]*", repo), "canonical repository")
    tasks = scope["tasks"]
    require(type(tasks) is dict and set(tasks) == ROLES, "three registered roles required")
    require(all(type(x) is str and re.fullmatch(r"[0-9a-f]{32}", x) for x in tasks.values())
            and len(set(tasks.values())) == 3, "separate canonical role task IDs")
    return scope

def capture(*, idea_id: str, project_id: str, origin: str, original_text: str,
            source_ref: str, captured_at: str, owner_priority: int = 3,
            observations: list[dict] | None = None,
            derived_from: list[str] | None = None, scope: dict | None = None,
            domain: str = "GAME", variant_of: str | None = None,
            duplicate_of: str | None = None) -> dict:
    """Preserve raw owner wording separately from derived and Web ideas."""
    obj = {
        "schema": VERSION, "idea_id": idea_id, "project_id": project_id,
        "origin": {"OWNER": "OWNER_ORIGINAL_IDEA", "WEB_RESEARCH": "WEB_RESEARCH_IDEA"}.get(origin, origin),
        "original_text": original_text,
        "original_sha256": sha256(original_text.encode("utf-8")).hexdigest()
                           if type(original_text) is str else "",
        "source_ref": source_ref, "captured_at": captured_at,
        "owner_priority": owner_priority, "observations": deepcopy(observations) if observations is not None else [],
        "derived_from": deepcopy(derived_from) if derived_from is not None else [],
        "stage": "CAPTURED", "events": [], "scope": deepcopy(scope),
        "domain": domain, "variant_of": variant_of, "duplicate_of": duplicate_of,
    }
    _scope(obj["scope"])
    obj["provenance_sha256"] = _provenance_hash(obj)
    validate_record(obj)
    return obj

def validate_record(record: dict) -> dict:
    require(type(record) is dict and set(record) == RECORD_KEYS, "record schema mismatch")
    require(type(record["schema"]) is int and record["schema"] == VERSION, "schema version")
    require(type(record["idea_id"]) is str and IDENTIFIER.fullmatch(record["idea_id"]) is not None, "idea ID")
    require(type(record["project_id"]) is str and PROJECT.fullmatch(record["project_id"]) is not None, "project ID")
    require(type(record["origin"]) is str and record["origin"] in ORIGINS, "idea origin")
    _scope(record["scope"])
    require(type(record["domain"]) is str and record["domain"] in {"GAME", "SYSTEM"}, "idea domain")
    for key in ("variant_of", "duplicate_of"):
        value = record[key]
        require(value is None or (type(value) is str and IDENTIFIER.fullmatch(value)
                                  and value != record["idea_id"]), "invalid variant/duplicate link")
    text = record["original_text"]
    require(type(text) is str and 5 <= len(text) <= 12000, "original text missing/oversized")
    require(record["original_sha256"] == sha256(text.encode("utf-8")).hexdigest(), "original words were modified")
    source = record["source_ref"]
    require(type(source) is str and (source == "NOT_AVAILABLE" or _url(source)), "source URL/provenance")
    baseline = _timestamp(record["captured_at"])
    require(record["provenance_sha256"] == _provenance_hash(record), "original provenance modified")
    require(type(record["owner_priority"]) is int and 1 <= record["owner_priority"] <= 5, "owner priority")
    require(type(record["observations"]) is list and len(record["observations"]) <= 20, "observations")
    for obs in record["observations"]:
        require(type(obs) is dict and set(obs) == {"source_url", "checked_at", "observed_fact", "limitation", "source_kind", "published_at"}, "observation schema")
        require(_url(obs["source_url"]), "research source must be HTTPS")
        _timestamp(obs["checked_at"])
        require(type(obs["source_kind"]) is str and obs["source_kind"] in SOURCE_KINDS, "research source class")
        _publication(obs["published_at"], obs["checked_at"])
        require(all(type(obs[k]) is str and 3 <= len(obs[k]) <= 2000 for k in ("observed_fact", "limitation")), "observation fact/limitation")
    if record["origin"] == "WEB_RESEARCH_IDEA":
        require(len(record["observations"]) >= 1, "research idea requires dated actual source")
    require(type(record["derived_from"]) is list and len(record["derived_from"]) <= 20
            and all(type(x) is str and IDENTIFIER.fullmatch(x) for x in record["derived_from"])
            and len(set(record["derived_from"])) == len(record["derived_from"])
            and record["idea_id"] not in record["derived_from"], "idea derivation")
    require(type(record["stage"]) is str and (record["stage"] in STAGES or record["stage"] in CLOSED), "unsupported/untrusted lifecycle stage")
    require(type(record["events"]) is list and len(record["events"]) <= 100, "events")
    last = "CAPTURED"
    for e in record["events"]:
        require(type(e) is dict and set(e) == {"actor", "occurred_at", "from", "to", "reason", "evidence_refs"}, "event schema")
        require(type(e["from"]) is str and type(e["to"]) is str and e["from"] == last and e["to"] in STAGES + tuple(CLOSED), "event chain mismatch")
        require(type(e["actor"]) is str and 2 <= len(e["actor"]) <= 100, "actor")
        require(type(e["reason"]) is str and 8 <= len(e["reason"]) <= 2000, "reason")
        require(type(e["evidence_refs"]) is list and len(e["evidence_refs"]) <= 20
                and all(type(v) is str and (v == "NOT_AVAILABLE" or _url(v)) for v in e["evidence_refs"]), "event evidence refs")
        observed = _timestamp(e["occurred_at"])
        require(observed >= baseline, "event predates capture/earlier event")
        baseline = observed
        if e["to"] in STAGES:
            require(last in STAGES, "already archived")
            require(STAGES.index(e["to"]) == STAGES.index(last) + 1, "stage skipping")
        else:
            require(last in STAGES, "already archived")
        last = e["to"]
    if record["origin"] == "DERIVED":
        require(len(record["derived_from"]) > 0, "derived ideas require source parents")
    require(record["stage"] == last, "record stage disagrees with events")
    _plain(record)
    return record

def advance(record: dict, to: str, *, actor: str, occurred_at: str,
            reason: str, evidence_refs: list[str] | None = None) -> dict:
    """Advance planning states only; protected implementation needs external gate."""
    validate_record(record)
    require(to not in PROTECTED, "TRUSTED_EXECUTOR_REQUIRED")
    after = deepcopy(record)
    after["events"].append({"actor": actor, "occurred_at": occurred_at,
                            "from": record["stage"], "to": to, "reason": reason,
                            "evidence_refs": evidence_refs or []})
    after["stage"] = to
    validate_record(after)
    return after

def validate_registry(ideas: list[dict]) -> list[dict]:
    """Check same-project parents, timestamps and an acyclic, rooted provenance DAG.

    Iterative topological traversal avoids recursion failure on long idea histories.
    This validation is *not* host authentication of the cited source.
    """
    require(type(ideas) is list and len(ideas) <= 10000, "registry size")
    by_key = {}
    scopes, repos, tasks = {}, {}, {}
    for idea in ideas:
        validate_record(idea)
        project, scope = idea["project_id"], idea["scope"]
        require(project not in scopes or scopes[project] == scope, "project scope changed")
        scopes[project] = scope
        repo = scope["repository"]
        require(repo not in repos or repos[repo] == project, "repository reused by another project")
        repos[repo] = project
        for task in scope["tasks"].values():
            require(task not in tasks or tasks[task] == project, "task reused by another project")
            tasks[task] = project
        key = (idea["project_id"], idea["idea_id"])
        require(key not in by_key, "duplicate idea ID in project")
        by_key[key] = idea
    children = {key: [] for key in by_key}
    indegree = {key: 0 for key in by_key}
    for key, idea in by_key.items():
        refs = set(idea["derived_from"])
        refs.update(idea[k] for k in ("variant_of", "duplicate_of") if idea[k] is not None)
        for parent_id in refs:
            parent_key = (idea["project_id"], parent_id)
            require(parent_key in by_key, "foreign/missing parent")
            require(_timestamp(idea["captured_at"]) >=
                    _timestamp(by_key[parent_key]["captured_at"]),
                    "idea predates its provenance parent")
            children[parent_key].append(key)
            indegree[key] += 1
    queue = deque(key for key, count in indegree.items() if count == 0)
    require(all(by_key[key]["origin"] != "DERIVED" for key in queue),
            "derived idea without original/research root")
    processed = 0
    while queue:
        key = queue.popleft()
        processed += 1
        for child in children[key]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    require(processed == len(by_key), "cyclic idea provenance")
    return ideas

def merge_registry(existing: list[dict], incoming: list[dict]) -> list[dict]:
    """Append stock/events against a caller's pinned baseline; does not persist it.

    The caller must independently obtain/fence that baseline from GitHub. A hash
    regenerated by an untrusted caller cannot authenticate the original words.
    """
    validate_registry(existing)
    require(type(incoming) is list and len(incoming) <= 10000, "incoming registry size")
    rows = {(r["project_id"], r["idea_id"]): deepcopy(r) for r in existing}
    seen = set()
    for row in incoming:
        validate_record(row)
        key = (row["project_id"], row["idea_id"])
        require(key not in seen, "duplicate incoming idea")
        seen.add(key)
        if key in rows:
            before = rows[key]
            immutable = RECORD_KEYS - {"stage", "events"}
            require(all(before[k] == row[k] for k in immutable), "stored original cannot be replaced")
            require(row["events"][:len(before["events"])] == before["events"], "stored events cannot be replaced")
        rows[key] = deepcopy(row)
    result = list(rows.values())
    validate_registry(result)
    return result

def assess_candidates(project_id: str, ideas: list[dict], proposals: list[dict]) -> dict:
    """Heuristic-only comparison; NEVER authorizes a task or claims market impact."""
    validate_registry(ideas)
    require(type(project_id) is str and PROJECT.fullmatch(project_id), "invalid project")
    selected = {x["idea_id"]: x for x in ideas if x["project_id"] == project_id}
    known = set(selected)
    require(bool(selected), "project has no scoped ideas")
    require(type(proposals) is list and 2 <= len(proposals) <= 30, "compare at least two alternatives")
    results, seen, domains = [], set(), set()
    for candidate in proposals:
        require(type(candidate) is dict and set(candidate) == {"candidate_id", "idea_refs", "hypothesis", "test_plan", "falsifier", "benefit", "effort", "confidence", "open_risks"}, "candidate schema")
        cid = candidate["candidate_id"]
        require(type(cid) is str and IDENTIFIER.fullmatch(cid) and cid not in seen and cid != "NO_CHANGE", "candidate ID/duplicate or reserved baseline")
        seen.add(cid)
        refs = candidate["idea_refs"]
        require(type(refs) is list and refs and len(refs) <= 20 and all(type(x) is str for x in refs) and len(set(refs)) == len(refs) and all(x in known for x in refs), "missing/cross-project idea refs")
        domains.update(selected[x]["domain"] for x in refs)
        require(len(domains) == 1, "compare GAME and SYSTEM experiments separately")
        for field in ("hypothesis", "test_plan", "falsifier"):
            require(type(candidate[field]) is str and 12 <= len(candidate[field]) <= 2000, field)
        for key, allowed in (("benefit", BENEFIT), ("effort", EFFORT)):
            obj = candidate[key]
            require(type(obj) is dict and set(obj) == set(allowed) and all(type(obj[k]) is int and 0 <= obj[k] <= 5 for k in allowed), key)
        require(type(candidate["confidence"]) is int and 1 <= candidate["confidence"] <= 3, "confidence")
        require(type(candidate["open_risks"]) is list and len(candidate["open_risks"]) <= 20
                and all(type(x) is str and 5 <= len(x) <= 200 for x in candidate["open_risks"]), "risks")
        b, e = candidate["benefit"], candidate["effort"]
        value = 2*b["acquisition"] + 3*b["retention"] + 2*b["strategy"] + 3*b["originality"]
        costs = 2*e["engineering"] + 2*e["qa"] + 3*e["performance"]
        heuristic = value - costs - (3 - candidate["confidence"])*4 - len(candidate["open_risks"])*2
        results.append({"candidate_id": cid, "idea_refs": deepcopy(refs),
                        "heuristic_score": heuristic, "confidence": candidate["confidence"],
                        "risks": deepcopy(candidate["open_risks"]),
                        "hypothesis": candidate["hypothesis"], "test_plan": candidate["test_plan"],
                        "falsifier": candidate["falsifier"],
                        "measured_effect": "NOT_MEASURED", "review_status": "NOT_REVIEWED"})
    results.sort(key=lambda x: (-x["heuristic_score"], x["candidate_id"]))
    return {"schema": VERSION, "project_id": project_id,
            "ranking": results,
            "scope": deepcopy(next(iter(selected.values()))["scope"]),
            "domain": next(iter(domains)),
            "baseline": {"candidate_id": "NO_CHANGE", "measured_effect": "NOT_MEASURED",
                         "test_plan": "Observe unchanged main with the same cohort, device and exposure window"},
            "metric_status": {k: "NOT_MEASURED" for k in METRICS},
            "engine_status": "NOT_RUN", "player_status": "NOT_MEASURED",
            "lifecycle": list(STAGES) + ["PROTOTYPE_PR", "OFFLINE_VERIFIED", "INDEPENDENT_APPROVED",
                                         "MERGED_MAIN_QA", "ENGINE_VERIFIED", "PLAYER_MEASURED"],
            "blocked_on": "PROVIDER_BACKED_INDEPENDENT_EXECUTION_EVIDENCE_REQUIRED",
            "classification": "HYPOTHESIS_ONLY_NOT_MARKET_PROOF",
            "execution": {"write": False, "dispatch": False, "merge": False,
                          "publish": False, "spend": False},
            "next": "Require independent prototype+offline test, Roblox engine/mobile proof, then opt-in player study before any measured-effect claim"}

def main():
    """Read JSON on stdin, print advisory JSON only; never dispatch or persist."""
    import sys

    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, "duplicate JSON key")
            result[k] = v
        return result

    try:
        raw = sys.stdin.read(2_000_001)
        require(len(raw) <= 2_000_000, "input size")
        data = json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: require(False, "nonfinite JSON"))
        require(type(data) is dict and set(data) == {"project_id", "ideas", "proposals"}, "CLI schema")
        result = assess_candidates(**data)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        print(json.dumps({"error": "INVALID_IDEA_INPUT", "write_authorized": False}))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
