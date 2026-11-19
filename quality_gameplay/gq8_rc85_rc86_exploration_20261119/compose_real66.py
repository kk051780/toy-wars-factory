#!/usr/bin/env python3
"""Single-runtime V3 REAL65 + one legacy RC85/86 exploration Script.
All 65 official selected original byte/class/source routes must survive.
This writes a reversible PRIVATE candidate; never updates the official branch.
"""
from __future__ import annotations
import argparse, copy, hashlib, json, shutil, os
from pathlib import Path

ROUTE = "ServerScriptService/EGGRUMBLE_LegacyExplorationBridge"
REL = "sources/ServerScriptService/EGGRUMBLE_LegacyExplorationBridge.server.luau"
FEATURE = "GQ8_LEGACY_RC85_86_EXPLORATION_INTAKE_20261119"

def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()

def all_source_nodes(project: dict):
    def walk(x, prefix=()):
        if "$path" in x:
            yield ("/".join(prefix), x["$path"])
            return
        for key, child in x.items():
            if not key.startswith("$") and isinstance(child, dict):
                yield from walk(child, (*prefix, key))
    return dict(walk(project["tree"]))

def require(ok: bool, marker: str) -> None:
    if not ok:
        raise ValueError("RED_GQ8_LEGACY_66_" + marker)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--source", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--official-sha", required=True)
    a = p.parse_args()
    require(not a.out.exists(), "NO_OVERWRITE")
    receipt = json.loads((a.base / "REAL65_INTAKE_RECEIPT.json").read_text())
    base_project = json.loads((a.base / "EGGRUMBLE_REAL65.project.json").read_text())
    base_files = all_source_nodes(base_project)
    require(len(base_files) == 65, "REAL65_COUNT")
    require(len(receipt["sources"]) == 65, "REAL65_RECEIPT_COUNT")
    require(ROUTE not in base_files, "DUPLICATE_BRIDGE")
    require(receipt["new_selected_source_count"] == 65, "REAL65_SOURCE_COUNT")
    require(receipt.get("formal_rc_adopted") is (os.environ.get("GITHUB_REF") == "refs/heads/rc/p0d-s1-kids-rc01"), "BASE_EVENT_MISMATCH")
    require(receipt.get("candidate_head") == a.official_sha, "HEAD_MISMATCH")
    require((a.base / "EGGRUMBLE_REAL65_PRIVATE.rbxlx").is_file(), "OFF65_PLACE_MISSING")
    for row in receipt["sources"]:
        route = row["route"]
        require(route in base_files, "RECEIPT_PATH_" + route)
        data = (a.base / base_files[route]).read_bytes()
        require(len(data) == row["bytes"] and sha(data) == row["sha256"], "EXACT65_" + route)
    require(set(base_files) == {row["route"] for row in receipt["sources"]}, "ROUTE_SET65")
    bridge = a.source.read_bytes()
    require(b"GQ8_LEGACY_RC85_86_EXPLORATION_INTAKE_20261119" in bridge, "FEATURE_MARKER")
    require(bridge.startswith(b"--!strict"), "STRICT")
    require(bridge.count(b'"REALM",') == 4 and bridge.count(b'"SHARD",') == 6, "COUNTS")
    require(b"RunService:IsStudio()" in bridge, "STUDIO_ONLY")
    shutil.copytree(a.base, a.out)
    (a.out / REL).parent.mkdir(parents=True, exist_ok=True)
    (a.out / REL).write_bytes(bridge)
    project = copy.deepcopy(base_project)
    project["name"] = "EGGRUMBLE_REAL66_RC85_RC86_REAL65_SINGLE_PRIVATE_STUDIO"
    project["tree"]["ServerScriptService"]["EGGRUMBLE_LegacyExplorationBridge"] = {"$path":REL}
    selected = all_source_nodes(project)
    require(len(selected) == 66 and set(selected) - set(base_files) == {ROUTE}, "ONLY_ONE_NEW")
    for route, path in base_files.items():
        require(selected[route] == path and (a.out / path).read_bytes() == (a.base / path).read_bytes(), "65_LOST_" + route)
    (a.out / "EGGRUMBLE_REAL66.project.json").write_text(json.dumps(project, ensure_ascii=False, indent=2, sort_keys=True) + "\n")
    newreceipt = {
        "schema":"GQ8_LEGACY_REAL66_SINGLE_RUNTIME_PRIVATE_V1",
        "feature_id":FEATURE,
        "official_parent_head":a.official_sha,
        "parent_profile":"REAL65",
        "candidate_selected_count":66,
        "parent_original_exact":65,
        "added_script_count":1,
        "new_route":ROUTE,
        "new_class":"Script",
        "new_path":REL,
        "new_bytes":len(bridge),
        "new_sha256":sha(bridge),
        "original65":[{"route":r,"path":base_files[r],"sha256":sha((a.base/base_files[r]).read_bytes())} for r in sorted(base_files)],
        "off65_parent_place_sha256":sha((a.base/"EGGRUMBLE_REAL65_PRIVATE.rbxlx").read_bytes()),
        "formal_adopted":os.environ.get("GITHUB_REF") == "refs/heads/rc/p0d-s1-kids-rc01",
        "roblox_publish":False,
        "studio_2client":"NOT_TESTED",
        "android":"NOT_TESTED",
        "owner_fun":"NOT_TESTED",
        "rollback":"Drop only ServerScriptService/EGGRUMBLE_LegacyExplorationBridge; original exact OFF65 Place is in artifact",
    }
    (a.out/"REAL66_LEGACY_INTAKE_RECEIPT.json").write_text(json.dumps(newreceipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
    print("GQ8_LEGACY_66_REAL65_BASE_65_OF_65_BYTE_EXACT_PASS")
    print("GQ8_LEGACY_66_NEW_SCRIPT_ONLY_ROUTE_CLASS_PASS")
if __name__ == "__main__":
    main()
