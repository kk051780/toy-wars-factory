#!/usr/bin/env python3
"""Read-only independent TRAP_RAIDERS S1 source/project wiring acceptance gate.

This checks bytes, Rojo project paths and role placement, NOT Luau execution or Studio.
Only Python standard library is required. No network, no shell, no Roblox action.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any

HASH = re.compile(r"^[0-9a-f]{64}$")
PIN = re.compile(r"^[0-9a-f]{40}$")
MANDATORY = {
    "match_lifecycle", "team_spawn", "input_mobile", "capture_objective",
    "combat_damage", "victory_defeat", "client_hud", "map_art", "entrypoint",
}
AUTHORITIES = {"round", "event_chooser", "damage", "persistence", "reward", "matchmaker"}
RECEIPT = "P0D_CHAT_SOURCE_ASSEMBLY_RECEIPT_V1"
PLAN = "P0D_CHAT_RELEASE_PLAN_V1"
MAX_FILES = 5000
MAX_FILE_BYTES = 12_000_000


class QAError(ValueError):
    pass


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise QAError("JSON_DUPLICATE_KEY:" + key)
        result[key] = value
    return result


def read_json(p: Path) -> dict:
    try:
        obj = json.loads(p.read_text(encoding="utf-8"), object_pairs_hook=unique_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as e:
        raise QAError("INVALID_JSON:" + p.name) from e
    if not isinstance(obj, dict):
        raise QAError("JSON_OBJECT_REQUIRED:" + p.name)
    return obj


def path_ok(rel: Any) -> str:
    if not isinstance(rel, str) or not rel or len(rel) > 400 or "\\" in rel or "\x00" in rel or ":" in rel or "%" in rel:
        raise QAError("INVALID_PATH")
    p = PurePosixPath(rel)
    if p.is_absolute() or p.as_posix() != rel or any(v in ("", ".", "..") for v in rel.split("/")):
        raise QAError("PATH_TRAVERSAL:" + rel)
    return rel


def all_files(root: Path) -> dict[str, Path]:
    if not root.is_dir() or root.is_symlink():
        raise QAError("RC_ROOT_NOT_PLAIN_DIRECTORY")
    out: dict[str, Path] = {}
    folded: dict[str, str] = {}
    folded_dirs: dict[str, str] = {}
    for where, dirs, files in os.walk(root, topdown=True, followlinks=False):
        for d in dirs:
            p = Path(where) / d
            rel_d = path_ok(p.relative_to(root).as_posix())
            key_d = rel_d.casefold()
            if key_d in folded_dirs and folded_dirs[key_d] != rel_d:
                raise QAError("CASE_COLLISION_DIRECTORY:" + rel_d)
            folded_dirs[key_d] = rel_d
            if p.is_symlink():
                raise QAError("SYMLINK_FORBIDDEN:" + rel_d)
        for name in files:
            p = Path(where) / name
            if p.is_symlink() or not p.is_file():
                raise QAError("SYMLINK_OR_NONFILE:" + str(p.relative_to(root)))
            rel = path_ok(p.relative_to(root).as_posix())
            low = rel.casefold()
            if low in folded and folded[low] != rel:
                raise QAError("CASE_COLLISION:" + rel)
            folded[low] = rel
            if p.stat().st_size > MAX_FILE_BYTES:
                raise QAError("FILE_TOO_LARGE:" + rel)
            out[rel] = p
            if len(out) > MAX_FILES:
                raise QAError("TOO_MANY_FILES")
    return out


def project_mappings(project: dict) -> list[tuple[str, str]]:
    root = project.get("tree")
    if not isinstance(root, dict):
        raise QAError("PROJECT_TREE_MISSING")
    found: list[tuple[str, str]] = []

    def walk(value: dict, ancestry: tuple[str, ...]) -> None:
        at = value.get("$path")
        if at is not None:
            found.append(("/".join(ancestry), path_ok(at)))
        for k, v in value.items():
            if k.startswith("$"):
                continue
            if isinstance(v, dict):
                walk(v, ancestry + (k,))
    walk(root, tuple())
    if not found:
        raise QAError("PROJECT_NO_SOURCE_PATHS")
    return found


def exists_mapping(rel: str, files: dict[str, Path]) -> bool:
    return rel in files or any(p.startswith(rel + "/") for p in files)


def is_executable(rel: str) -> bool:
    return rel.endswith((".lua", ".luau", ".model.json", ".rbxmx", ".rbxm", ".rbxlx", ".rbxl"))


def is_reachable(src: str, mapped: str) -> bool:
    return src == mapped or src.startswith(mapped + "/")


def test_project(root: Path, files: dict[str, Path], known: set[str]) -> int:
    if "default.project.json" not in known:
        raise QAError("PROJECT_NOT_IN_SOURCE_RECEIPT")
    project = read_json(root / "default.project.json")
    mappings = project_mappings(project)
    for ancestry, mapped in mappings:
        if not (mapped.startswith("src/") or mapped == "src" or mapped.startswith("assets/") or mapped == "assets"):
            raise QAError("PROJECT_PATH_OUTSIDE_SOURCE:" + mapped)
        if not exists_mapping(mapped, files):
            raise QAError("PROJECT_MAPPING_NOT_FOUND:" + mapped)
        if not any(is_reachable(f, mapped) and is_executable(f) for f in files):
            raise QAError("PROJECT_MAPPING_EMPTY_OR_NON_ASSET:" + mapped)
        parts = ancestry.split("/")
        server_side = "ServerScriptService" in parts or "ServerStorage" in parts
        client_side = "StarterPlayer" in parts or "StarterGui" in parts
        for p in files:
            if not is_reachable(p, mapped):
                continue
            if p.endswith((".server.lua", ".server.luau")) and not server_side:
                raise QAError("SERVER_SCRIPT_OUTSIDE_SERVER:" + p)
            if p.endswith((".client.lua", ".client.luau")) and not client_side:
                raise QAError("CLIENT_SCRIPT_OUTSIDE_CLIENT:" + p)
    # A script mounted twice is executed twice by Rojo, even if the source
    # manifest contains just one copy. This can silently duplicate damage and
    # event authority in the actual Roblox DataModel.
    mounted = {}
    for ancestry, mapped in mappings:
        for rel in files:
            if is_executable(rel) and is_reachable(rel, mapped):
                if rel in mounted:
                    raise QAError("DUPLICATE_PROJECT_MAPPING:" + rel)
                mounted[rel] = ancestry
    for p in known:
        if not p.startswith("src/"):
            continue
        if p.endswith((".lua", ".luau")) and p not in mounted:
            raise QAError("SOURCE_LUAU_NOT_MOUNTED:" + p)
    return len(mappings)


def audit(rc: Path, plan_path: Path) -> dict:
    """Raise QAError on a failed source/build gate. No mutation of candidate."""
    files = all_files(rc)
    if "CHAT_RC_RECEIPT.json" not in files:
        raise QAError("RECEIPT_NOT_FOUND")
    receipt = read_json(files["CHAT_RC_RECEIPT.json"])
    plan_bytes = plan_path.read_bytes()
    plan = read_json(plan_path)
    if receipt.get("format") != RECEIPT or plan.get("format") != PLAN:
        raise QAError("WRONG_SCHEMA")
    for x in (receipt, plan):
        if x.get("game_id") != "TRAP_RAIDERS" or x.get("work_id") != "p0d-siege-v19":
            raise QAError("WRONG_GAME")
    if receipt.get("release_id") != plan.get("release_id"):
        raise QAError("RELEASE_ID_MISMATCH")
    if receipt.get("source_plan_sha256") != sha(plan_bytes):
        raise QAError("SOURCE_PLAN_BYTES_MISMATCH")
    if receipt.get("assembly_status") != "CHAT_BUILD_READY__OFFLINE_EVIDENCE_ONLY":
        raise QAError("NOT_AN_ASSEMBLED_CANDIDATE")
    if receipt.get("studio_status") != "NOT_TESTED" or receipt.get("release_approved") is not False:
        raise QAError("STUDIO_OR_LIVE_RELEASE_CLAIM_FORBIDDEN")
    if plan.get("studio_status") != "NOT_TESTED" or plan.get("publish_approved") is not False:
        raise QAError("PLAN_STUDIO_OR_PUBLISH_CLAIM_FORBIDDEN")
    if plan.get("phase") != "CHAT_BUILD_READY" or not MANDATORY.issubset(set(plan.get("capabilities", []))):
        raise QAError("PLAN_S1_CAPABILITY_GATE_MISSING")
    content = receipt.get("contents")
    units = receipt.get("source_units")
    p_units = plan.get("units")
    if not isinstance(content, list) or not content or not isinstance(units, list) or not units or not isinstance(p_units, list):
        raise QAError("SOURCE_UNIT_LIST_MISSING")
    if len(content) > MAX_FILES:
        raise QAError("TOO_MANY_RECEIPT_FILES")
    known: set[str] = set()
    indexed: dict[str, tuple[str, int]] = {}
    for row in content:
        if not isinstance(row, dict):
            raise QAError("BAD_CONTENT_ROW")
        p = path_ok(row.get("path"))
        if p in known:
            raise QAError("DUPLICATE_CONTENT_PATH:" + p)
        known.add(p)
        if not (p.startswith("src/") or p.startswith("assets/") or p == "default.project.json"):
            raise QAError("OUT_OF_TREE_CONTENT:" + p)
        h = row.get("sha256")
        size = row.get("size")
        if not isinstance(h, str) or not HASH.fullmatch(h) or type(size) is not int or size < 0:
            raise QAError("BAD_RECEIPT_HASH_OR_SIZE:" + p)
        actual = files.get(p)
        if actual is None:
            raise QAError("RECEIPT_FILE_MISSING:" + p)
        data = actual.read_bytes()
        if sha(data) != h or len(data) != size:
            raise QAError("CONTENT_BYTES_MISMATCH:" + p)
        indexed[p] = (h, size)
    actual_source = {p for p in files if p.startswith("src/") or p.startswith("assets/") or p == "default.project.json"}
    if actual_source != known:
        raise QAError("UNTRACKED_OR_UNRECEIPTED_SOURCE:" + str(sorted(actual_source ^ known)[:3]))
    if len(units) != len(p_units) or len(units) != len(known):
        raise QAError("SOURCE_UNIT_COUNT_MISMATCH")
    r_ids = set()
    r_destinations = set()
    for row in units:
        if not isinstance(row, dict):
            raise QAError("BAD_RECEIPT_UNIT")
        uid = row.get("unit_id")
        dest = path_ok(row.get("target_path"))
        pin = row.get("source_commit")
        if not isinstance(uid, str) or not uid or uid in r_ids or not isinstance(pin, str) or not PIN.fullmatch(pin):
            raise QAError("RECEIPT_UNIT_ID_OR_SHA_INVALID")
        if dest in r_destinations or dest not in known or row.get("sha256") != indexed[dest][0]:
            raise QAError("RECEIPT_UNIT_TARGET_INVALID:" + dest)
        r_ids.add(uid)
        r_destinations.add(dest)
    expected = {(r["unit_id"], r["source_commit"], r["target_path"], r["sha256"]): r for r in units}
    owner = {}
    units_seen = set()
    for row in p_units:
        if not isinstance(row, dict):
            raise QAError("BAD_PLAN_UNIT")
        uid, src, dest, h = row.get("unit_id"), row.get("source_commit"), row.get("target_path"), row.get("sha256")
        if not isinstance(uid, str) or uid in units_seen:
            raise QAError("DUPLICATE_PLAN_UNIT")
        units_seen.add(uid)
        match = expected.get((uid, src, dest, h))
        if match is None:
            raise QAError("PLAN_UNIT_NOT_IN_RECEIPT:" + uid)
        # Support the optional Chat-first assembler's authentic multi-authority
        # representation while retaining the original V2 singular schema.
        if "authority" in row and "authorities" in row:
            raise QAError("AUTHORITY_AMBIGUOUS_FIELDS")
        if "authorities" in row:
            roles = row["authorities"]
            if not isinstance(roles, list) or len(roles) == 0 or len(roles) > len(AUTHORITIES):
                raise QAError("INVALID_AUTHORITIES_LIST")
            if any(not isinstance(a, str) or a not in AUTHORITIES for a in roles):
                raise QAError("INVALID_AUTHORITIES_LIST")
            if len(set(roles)) != len(roles):
                raise QAError("DUPLICATE_AUTHORITY_IN_UNIT")
        else:
            auth = row.get("authority", "none")
            if not isinstance(auth, str) or (auth != "none" and auth not in AUTHORITIES):
                raise QAError("INVALID_AUTHORITY")
            roles = [] if auth == "none" else [auth]
        # The compatible assembler emits a role array for each source unit.
        # A forged receipt that omits or changes it must not be treated as proof.
        if "authorities" in match:
            if match["authorities"] != roles:
                raise QAError("RECEIPT_AUTHORITY_MISMATCH:" + uid)
        elif "authorities" in row:
            raise QAError("RECEIPT_AUTHORITIES_NOT_ATTESTED:" + uid)
        for a in roles:
            if a in owner:
                raise QAError("DUPLICATE_OR_INVALID_AUTHORITY:" + a)
            owner[a] = uid
    for a in ("round", "event_chooser", "damage"):
        if a not in owner:
            raise QAError("MISSING_CANONICAL_AUTHORITY:" + a)
    map_count = test_project(rc, files, known)
    return {
        "format": "P0D_S1_INDEPENDENT_SOURCE_WIRING_QA_V1",
        "game_id": "TRAP_RAIDERS", "work_id": "p0d-siege-v19", "release_id": plan["release_id"],
        "result": "PASS_SOURCE_WIRING_ONLY", "source_files_verified": len(known),
        "project_path_mappings_verified": map_count,
        "authority_declarations": owner,
        "engine_luau_parser": "NOT_TESTED", "studio_2client_mobile": "NOT_TESTED",
        "gameplay_scenario_qa": "OUT_OF_SCOPE_OTHER_QA_LANE",
        "publish_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Independent P0-D S1 RC source/Studio-project mapping gate")
    p.add_argument("--rc", type=Path, required=True, help="assembled RC directory; read-only")
    p.add_argument("--plan", type=Path, required=True, help="exact source release plan; read-only")
    args = p.parse_args(argv)
    try:
        result = audit(args.rc, args.plan)
        code = 0
    except (QAError, OSError, UnicodeError, TypeError, KeyError) as e:
        result = {
            "format": "P0D_S1_INDEPENDENT_SOURCE_WIRING_QA_V1",
            "result": "FAIL_SOURCE_WIRING", "defect": str(e),
            "studio_2client_mobile": "NOT_TESTED", "publish_approved": False,
        }
        code = 2
    print(json.dumps(result, indent=2, ensure_ascii=False, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
