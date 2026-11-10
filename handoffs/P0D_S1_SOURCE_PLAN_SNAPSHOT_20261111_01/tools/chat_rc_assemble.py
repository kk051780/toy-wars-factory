#!/usr/bin/env python3
"""P0-D CHAT-FIRST deterministic source assembly and preflight.

No GitHub write, Roblox Studio actions, protected branch updates, or network access.
The resulting artifact is CHAT_BUILD_READY, never STUDIO_PASS or release approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import zipfile

FORMAT = "P0D_CHAT_RELEASE_PLAN_V1"
PIN = re.compile(r"^[0-9a-f]{40}$")
HASH = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[a-zA-Z0-9_.-]{1,96}$")
MANDATORY_S1 = frozenset({"match_lifecycle", "team_spawn", "input_mobile", "capture_objective", "combat_damage", "victory_defeat", "client_hud", "map_art", "entrypoint"})
UNIQUE_AUTH = frozenset({"round", "event_chooser", "damage", "persistence", "reward", "matchmaker"})


class GateError(ValueError):
    pass


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(data: object) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def safe_rel(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value or "%" in value or ":" in value:
        raise GateError("INVALID_PATH")
    p = PurePosixPath(value)
    if p.is_absolute() or str(p) != value or any(x in (".", "..") for x in value.split("/")):
        raise GateError("PATH_TRAVERSAL_OR_NONCANONICAL")
    return value


def read_local(root: Path, rel: str) -> bytes:
    parts = safe_rel(rel).split("/")
    current = root
    for part in parts:
        current = current / part
        if current.is_symlink():
            raise GateError("SYMLINK_FORBIDDEN")
    if not current.is_file():
        raise GateError("MISSING_SOURCE " + rel)
    if current.stat().st_size > 12_000_000:
        raise GateError("SOURCE_TOO_LARGE")
    return current.read_bytes()


def validate(plan: dict, source_root: Path) -> tuple[list[dict], dict[str, bytes]]:
    if not isinstance(plan, dict) or plan.get("format") != FORMAT or plan.get("game_id") != "TRAP_RAIDERS" or plan.get("work_id") != "p0d-siege-v19":
        raise GateError("INVALID_GAME_CONTRACT")
    if plan.get("phase") != "CHAT_BUILD_READY" or not IDENT.fullmatch(str(plan.get("release_id", ""))):
        raise GateError("NOT_CHAT_BUILD_READY")
    units = plan.get("units")
    if not isinstance(units, list) or not units or len(units) > 1000:
        raise GateError("MISSING_UNITS")
    ids, targets, owners, variants, payload = set(), set(), {}, {}, {}
    for u in units:
        if not isinstance(u, dict) or not IDENT.fullmatch(str(u.get("unit_id", ""))):
            raise GateError("BAD_UNIT_ID")
        unit = u["unit_id"]
        if unit in ids:
            raise GateError("DUPLICATE_UNIT")
        ids.add(unit)
        if not PIN.fullmatch(str(u.get("source_commit", ""))):
            raise GateError("UNPINNED_SOURCE " + unit)
        src = safe_rel(u.get("source_path"))
        dest = safe_rel(u.get("target_path"))
        if not (dest.startswith("src/") or dest.startswith("assets/") or dest == "default.project.json"):
            raise GateError("INVALID_DESTINATION")
        if dest in targets:
            raise GateError("COLLIDING_DESTINATION")
        targets.add(dest)
        if not HASH.fullmatch(str(u.get("sha256", ""))):
            raise GateError("MISSING_SOURCE_SHA")
        # Compatible with the V2 singular role, while allowing one real source
        # unit (e.g. Game.server.luau) to own several *distinct* roles.
        if "authority" in u and "authorities" in u:
            raise GateError("AUTHORITY_AMBIGUOUS_FIELDS")
        if "authorities" in u:
            roles = u["authorities"]
            if not isinstance(roles, list) or not roles or any(not isinstance(x, str) for x in roles):
                raise GateError("INVALID_AUTHORITIES_LIST")
            if len(roles) > len(UNIQUE_AUTH) or "none" in roles:
                raise GateError("INVALID_AUTHORITY")
            if len(roles) != len(set(roles)):
                raise GateError("DUPLICATE_AUTHORITY_IN_UNIT")
        else:
            auth = u.get("authority", "none")
            if not isinstance(auth, str):
                raise GateError("INVALID_AUTHORITY")
            roles = [] if auth == "none" else [auth]
        for auth in roles:
            if auth not in UNIQUE_AUTH:
                raise GateError("INVALID_AUTHORITY")
            if auth in owners:
                raise GateError("DUPLICATE_AUTHORITY " + auth)
            owners[auth] = unit
        family = u.get("variant_family", "none")
        if family != "none":
            if not IDENT.fullmatch(str(family)):
                raise GateError("BAD_VARIANT_FAMILY")
            if family in variants:
                raise GateError("ORIGINAL_CLEANROOM_OR_VARIANT_COLLISION " + family)
            if u.get("variant_kind") not in ("original", "cleanroom", "new"):
                raise GateError("VARIANT_ORIGIN_REQUIRED")
            variants[family] = unit
        b = read_local(source_root, src)
        if digest(b) != u["sha256"]:
            raise GateError("SOURCE_SHA_MISMATCH " + unit)
        payload[dest] = b
    for u in units:
        deps = u.get("depends_on", [])
        if not isinstance(deps, list) or len(set(deps)) != len(deps):
            raise GateError("BAD_DEPENDENCIES")
        if any(x not in ids or x == u["unit_id"] for x in deps):
            raise GateError("UNKNOWN_DEPENDENCY")
    graph = {u["unit_id"]: u.get("depends_on", []) for u in units}
    visited, visiting = set(), set()
    def walk(n: str):
        if n in visiting:
            raise GateError("CIRCULAR_DEPENDENCY")
        if n in visited:
            return
        visiting.add(n)
        for d in graph[n]:
            walk(d)
        visiting.remove(n)
        visited.add(n)
    for node in graph:
        walk(node)
    if not MANDATORY_S1.issubset(set(plan.get("capabilities", []))):
        raise GateError("S1_PLAYABLE_CAPABILITIES_MISSING")
    if "event_chooser" not in owners or "round" not in owners or "damage" not in owners:
        raise GateError("MISSING_CANONICAL_SERVER_AUTHORITIES")
    if "default.project.json" not in payload:
        raise GateError("NO_STUDIO_PROJECT_MAPPING")
    try:
        project = json.loads(payload["default.project.json"])
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise GateError("INVALID_STUDIO_PROJECT_JSON") from e
    if not isinstance(project, dict) or "tree" not in project:
        raise GateError("MISSING_STUDIO_PROJECT_TREE")
    tests = plan.get("offline_checks")
    if not isinstance(tests, list) or not tests:
        raise GateError("NO_OFFLINE_EVIDENCE")
    for t in tests:
        if not isinstance(t, dict) or t.get("status") != "PASS":
            raise GateError("OFFLINE_EVIDENCE_NOT_PASS")
        evidence = safe_rel(t.get("log_path"))
        if not HASH.fullmatch(str(t.get("sha256", ""))):
            raise GateError("EVIDENCE_SHA_REQUIRED")
        if digest(read_local(source_root, evidence)) != t["sha256"]:
            raise GateError("EVIDENCE_SHA_MISMATCH")
    if plan.get("studio_status") != "NOT_TESTED" or plan.get("publish_approved") is not False:
        raise GateError("STUDIO_OR_RELEASE_CLAIM_NOT_ALLOWED")
    return sorted(units, key=lambda x: x["unit_id"]), payload


def assemble(plan_file: Path, source_root: Path, out_dir: Path) -> dict:
    if out_dir.exists() or out_dir.is_symlink():
        raise GateError("OUTPUT_MUST_BE_NEW")
    if not source_root.is_dir():
        raise GateError("SOURCE_DIRECTORY_MISSING")
    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    units, payload = validate(plan, source_root)
    # All checks pass BEFORE first output mutation.
    receipt = {
        "format": "P0D_CHAT_SOURCE_ASSEMBLY_RECEIPT_V1",
        "game_id": "TRAP_RAIDERS", "work_id": "p0d-siege-v19",
        "release_id": plan["release_id"], "source_plan_sha256": digest(plan_file.read_bytes()),
        "source_units": [{"unit_id": x["unit_id"], "source_commit": x["source_commit"],
                          "target_path": x["target_path"], "sha256": x["sha256"],
                          "authorities": x["authorities"] if "authorities" in x
                                         else ([] if x.get("authority", "none") == "none"
                                               else [x["authority"]])} for x in units],
        "assembly_status": "CHAT_BUILD_READY__OFFLINE_EVIDENCE_ONLY",
        "studio_status": "NOT_TESTED", "release_approved": False,
        "contents": [{"path": path, "sha256": digest(blob), "size": len(blob)} for path, blob in sorted(payload.items())]
    }
    out_dir.mkdir(parents=True)
    for target, blob in sorted(payload.items()):
        p = out_dir / target
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(blob)
        if p.read_bytes() != blob:
            raise GateError("OUTPUT_READBACK_FAILED")
    (out_dir / "CHAT_RC_RECEIPT.json").write_bytes(canonical_json(receipt))
    return receipt


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Offline Chat release candidate source assembler (not Studio validation)")
    p.add_argument("--plan", type=Path, required=True)
    p.add_argument("--source-root", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args(argv)
    try:
        r = assemble(args.plan, args.source_root, args.out)
        print("CHAT_BUILD_READY (STUDIO NOT TESTED):",r["release_id"],len(r["contents"]),"files")
        return 0
    except (GateError, OSError, json.JSONDecodeError) as e:
        print("CHAT_BUILD_HOLD:",str(e),file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
