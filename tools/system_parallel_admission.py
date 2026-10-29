"""Read-only fail-closed cross-chat advisory admission planner.

This is *not* a lease, identity attestation, or permission to write GitHub.
Untrusted chat descriptions cannot attest task/run provenance or authorize a merge.
Owner's design contract: kk051780/toy-wars-factory, Issue #123.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{1,63}\Z")
WORK_ID = re.compile(r"[A-Z][A-Z0-9_-]{3,79}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
REPOSITORY = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?/[A-Za-z0-9_.-]{1,100}\Z")
RESTRICTED_ROOTS = (
    "AGENTS.md", "PROJECT_STATE.json", "config/", ".github/", "ops/",
    "history/", "status/", ".gitmodules", ".gitattributes", ".gitignore",
    "tools/",
)
VALID_MODES = frozenset({"READ_ONLY", "SOURCE_WRITE"})


def _decision(status: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, "mode": "READ_ONLY_ADMISSION", "verification": "NOT_VERIFIED",
            "may_write": False, "may_run_now": False, "github_cas_performed": False,
            "authority": {key: False for key in ("write_allowed", "start_now_allowed",
                "takeover_allowed", "dispatch_allowed", "merge_allowed", "publish_allowed",
                "external_spend_allowed", "safe_to_next_schedule")}, **extra}


class UnsafeInput(ValueError):
    """Input cannot safely be interpreted as an admission declaration."""


def _exact_string(value: Any, pattern: re.Pattern[str], name: str) -> str:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise UnsafeInput(f"invalid {name}")
    return value


def canonical_path(raw: Any) -> str:
    """Conservative Git POSIX file path; unknown/ambiguous paths fail closed."""
    if not isinstance(raw, str) or not raw or len(raw) > 256:
        raise UnsafeInput("invalid path")
    if (not raw.isascii() or raw != unicodedata.normalize("NFC", raw) or raw.startswith("/")
            or "\\" in raw or "%" in raw or "\x00" in raw
            or any(ord(ch) < 32 for ch in raw)):
        raise UnsafeInput("ambiguous path")
    parts = raw.split("/")
    if any(not p or re.fullmatch(r"[A-Za-z0-9_.-]+", p) is None
           or p in {".", ".."} or p.endswith((".", " "))
           or any(ch in "*?[]{}" for ch in p) or p.casefold() == ".git"
           for p in parts):
        raise UnsafeInput("unsafe path component")
    return "/".join(p.casefold() for p in parts)


def _paths(value: Any, *, allow_empty: bool = False) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 300 or (not allow_empty and not value):
        raise UnsafeInput("invalid file path manifest")
    paths = tuple(canonical_path(p) for p in value)
    if len(paths) != len(set(paths)):
        raise UnsafeInput("duplicated or case-aliased paths")
    return paths


def _resources(value: Any) -> tuple[str, ...]:
    if not isinstance(value, list) or len(value) > 100:
        raise UnsafeInput("invalid resource manifest")
    resources = []
    for x in value:
        if not isinstance(x, str) or not re.fullmatch(r"[a-z][a-z0-9_.:-]{0,79}", x):
            raise UnsafeInput("invalid shared resource")
        resources.append(x)
    if len(resources) != len(set(resources)):
        raise UnsafeInput("duplicate shared resource")
    return tuple(resources)


def _validate(item: Any) -> dict[str, Any]:
    if not isinstance(item, dict) or set(item) != {
        "project_id", "repository", "work_id", "goal_sha256", "mode",
        "write_paths", "shared_resources", "complete_manifest", "origin"
    }:
        raise UnsafeInput("invalid work declaration keys")
    project = _exact_string(item["project_id"], PROJECT_ID, "project_id")
    repo = _exact_string(item["repository"], REPOSITORY, "repository")
    if repo.split("/")[1] in (".", "..") or repo.casefold().endswith(".git"):
        raise UnsafeInput("ambiguous repository identity")
    work = _exact_string(item["work_id"], WORK_ID, "work_id")
    goal = _exact_string(item["goal_sha256"], HEX64, "goal hash")
    mode = item["mode"]
    if not isinstance(mode, str) or mode not in VALID_MODES:
        raise UnsafeInput("invalid mode")
    if type(item["complete_manifest"]) is not bool:
        raise UnsafeInput("invalid manifest attestation")
    paths = _paths(item["write_paths"], allow_empty=mode == "READ_ONLY")
    resources = _resources(item["shared_resources"])
    if mode == "READ_ONLY" and (paths or resources):
        raise UnsafeInput("read-only work declares writable resources")
    if not isinstance(item["origin"], str) or item["origin"] not in {"CHAT_UNVERIFIED", "REGISTERED_TASK_CLAIMED"}:
        raise UnsafeInput("unknown origin")
    return dict(project=project, repository=repo.casefold(), work=work,
                goal=goal, mode=mode, paths=paths, resources=resources,
                complete=item["complete_manifest"], origin=item["origin"])


def _overlap(a: tuple[str, ...], b: tuple[str, ...]) -> tuple[str, ...]:
    collisions = set()
    for left in a:
        for right in b:
            if left == right or left.startswith(right + "/") or right.startswith(left + "/"):
                collisions.add(left if len(left) <= len(right) else right)
    return tuple(sorted(collisions))


def _protected(paths: tuple[str, ...]) -> bool:
    # canonical_path() casefolds all input, so policy roots MUST use the same
    # canonical representation. Otherwise AGENTS.md / PROJECT_STATE.json
    # silently bypass the protected-file gate.
    roots = tuple(root.casefold().rstrip("/") for root in RESTRICTED_ROOTS)
    # Unknown hidden paths and all control-plane tools stay exclusive. A
    # declared directory also includes protected descendants, not just itself.
    return (any(part.startswith(".") for p in paths for part in p.split("/"))
            or bool(_overlap(paths, roots)))


def _scope(item: dict[str, Any]) -> tuple[Any, ...]:
    return item["goal"], item["mode"], tuple(sorted(item["paths"])), tuple(sorted(item["resources"]))


def advise(candidate: Any, active: Any) -> dict[str, Any]:
    """Produce a *non-authoritative* decision; never grants GitHub writes.

    Active work must be fetched from authenticated GitHub coordinator/issue state
    by the caller; this pure function cannot establish that trust. An explicit
    empty list is a supplied declaration, never proof that GitHub has no work.
    Goal hashes only match declared bytes: no semantic deduplication, source
    attestation, symlink/tree validation, persistent registration or lease API.
    """
    try:
        x = _validate(candidate)
        if not isinstance(active, list) or len(active) > 200:
            raise UnsafeInput("invalid active ledger")
        jobs = [_validate(row) for row in active]
        known = {}
        for job in jobs:
            key = job["repository"], job["project"], job["work"]
            if key in known and known[key] != _scope(job):
                raise UnsafeInput("contradictory active work identity")
            known[key] = _scope(job)
    except UnsafeInput as ex:
        return _decision("BLOCKED_UNSAFE_INPUT", reason=str(ex))
    matches = []
    for j in jobs:
        if j["repository"] == x["repository"] and j["project"] == x["project"]:
            if j["work"] == x["work"] and _scope(j) != _scope(x):
                return _decision("BLOCKED_WORK_ID_CONFLICT")
            if j["work"] == x["work"] or j["goal"] == x["goal"]:
                matches.append(j["work"])
    if matches:
        return _decision("JOIN_EXISTING", existing_work_ids=sorted(set(matches)))
    if x["mode"] == "READ_ONLY":
        return _decision("READ_ONLY_PARALLEL")
    if not x["complete"] or any(not j["complete"] and j["repository"] == x["repository"] for j in jobs):
        return _decision("WAIT_INCOMPLETE_MANIFEST")
    if x["origin"] != "REGISTERED_TASK_CLAIMED":
        return _decision("WAIT_UNATTESTED_AUTHOR")
    if _protected(x["paths"]):
        return _decision("WAIT_PROTECTED_SCOPE")
    for j in jobs:
        if j["mode"] == "READ_ONLY":
            continue
        # Different project_id values can still touch the same physical repository.
        if j["repository"] != x["repository"]:
            continue
        conflicts = _overlap(x["paths"], j["paths"])
        resources = set(x["resources"]) & set(j["resources"])
        if conflicts or resources:
            return _decision("WAIT_CONFLICT", with_work_id=j["work"],
                             path_collisions=list(conflicts), resource_collisions=sorted(resources))
    return _decision("CANDIDATE_FOR_AUTHENTICATED_CAS",
                     reason="Advisory only: externally verify canonical work, actual tree/dependencies, registered run and existing exclusive CAS; no extra writer admitted")
