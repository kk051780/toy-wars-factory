#!/usr/bin/env python3
"""Source-exact real OFF36 -> optional ON39 physical stage annex.

Real official RBXLX from same pinned formal RC is the sole 36-source baseline.
Not a second Game/Combat/Host/Swarm/weather/remote authority, not formal RC CAS.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "gq8_lss_real31_20261117"))
from rehydrate_real31 import CLASSES, flat_project, tree_scripts, verify_built  # noqa: E402

ORIGINAL_STAGE_BLOB = "696d2312ef7408e26b03281caede7606472c155b"
RC_HEAD = "f77b4d4393d9e9b19b65566413432a7a9f13962b"
STAGE = ("ServerScriptService", "EGGRUMBLE_StageManifestPolicy")
PLAN = ("ServerScriptService", "EGGRUMBLE_StagePhysicalPlan")
SERVER = ("ServerScriptService", "EGGRUMBLE_StagePhysicalAnnex")
EXTENSIONS = {STAGE: ".luau", PLAN: ".luau", SERVER: ".server.luau"}
KEY_OLD = {
    ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview"),
    ("ServerScriptService", "EGGRUMBLE_SwarmCombat"),
    ("ServerScriptService", "EGGRUMBLE_SevenRoleCombat"),
    ("ServerScriptService", "EGGRUMBLE_LandSeaSkyTraversal"),
    ("ServerScriptService", "EGGRUMBLE_RealmBattleCore"),
    ("ServerScriptService", "EGGRUMBLE_NaturalRegen"),
}
FILE_NAME = "EGGRUMBLE_V3_CORE36_PRIVATE_RC.rbxlx"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], text=True).strip()


def source_paths():
    root = Path(__file__).resolve().parent
    return {
        STAGE: root / "EGGRUMBLE_StageManifestPolicy.luau",
        PLAN: root / "EGGRUMBLE_StagePhysicalPlan.luau",
        SERVER: root / "EGGRUMBLE_StagePhysicalAnnex.server.luau",
    }


def compose(place: Path, template: Path, receipt: Path, out: Path, official_head: str):
    if not re.fullmatch(r"[0-9a-f]{40}", official_head) or official_head != RC_HEAD:
        raise ValueError("RED_NOT_FIXED_FORMAL_CORE36_HEAD")
    info = json.loads(receipt.read_text(encoding="utf-8"))
    if (info.get("build_sha") != official_head
        or info.get("selected_in_formal_rc_branch") is not True
        or info.get("source_count") != 36
        or info.get("place_sha256") != digest(place)):
        raise ValueError("RED_NOT_FORMAL_SAMEHEAD_CORE36_PLACE")
    original = tree_scripts(ET.parse(place).getroot())
    if len(original) != 36 or not KEY_OLD.issubset(original):
        raise ValueError("RED_NOT_REAL_CORE36_WITH_SINGLE_AUTHORITIES")
    names = {p[-1] for p in original}
    if len(names) != 36 or names & {x[-1] for x in EXTENSIONS}:
        raise ValueError("RED_SOURCE_COLLISION")
    proto = json.loads(template.read_text(encoding="utf-8"))
    routes = flat_project(proto)
    if set(routes) != set(original):
        raise ValueError("RED_OFFICIAL_TEMPLATE_SOURCE_ROUTE_DRIFT")
    adds = source_paths()
    if git_blob(adds[STAGE]) != ORIGINAL_STAGE_BLOB:
        raise ValueError("RED_ORIGINAL_STAGE_AUTHOR_DRIFT")
    script = adds[SERVER].read_text(encoding="utf-8")
    assert "if not RunService:IsStudio() then return end" in script
    for snippet in ("StageManifest.validate(manifest)", "PhysicalPlan.plan(manifest,frame)",
                    'SCENE_NAME="EGGRUMBLE_STAGE_PHYSICAL_ANNEX"',
                    "occupied[world]=true", "world.Destroying:Connect"):
        if snippet not in script:
            raise ValueError("RED_UNWIRED_PHYSICAL_STAGE_"+snippet)
    for banned in ('Instance.new("RemoteEvent")', "DataStoreService",
                   "TeleportService", "workspace.Gravity=", "TakeDamage(", "BreakJoints("):
        if banned in script:
            raise ValueError("RED_SECOND_AUTHORITY_"+banned)
    if out.exists():
        raise ValueError("RED_REFUSE_REBUILD_OVERWRITE")
    out.mkdir(parents=True)
    srcdir = out / "sources"
    srcdir.mkdir()
    on_model = copy.deepcopy(proto)
    off_model = copy.deepcopy(proto)
    for route, (kind, source) in sorted(original.items()):
        path = srcdir / (route[-1] + CLASSES[kind])
        if path.exists():
            raise ValueError("RED_FILENAME_COLLISION")
        path.write_text(source, encoding="utf-8", newline="\n")
        node_on = flat_project(on_model)[route]
        node_off = flat_project(off_model)[route]
        node_on["$path"] = "sources/" + path.name
        node_off["$path"] = "sources/" + path.name
    for route, ext in EXTENSIONS.items():
        origin = adds[route]
        dest = srcdir / (route[-1] + ext)
        if dest.exists():
            raise ValueError("RED_ADDITIONAL_SOURCE_FILENAME_COLLISION")
        dest.write_bytes(origin.read_bytes())
        node = on_model["tree"]
        for token in route:
            node = node.setdefault(token, {})
        if "$path" in node:
            raise ValueError("RED_ADDITIONAL_SOURCE_ROUTE_COLLISION")
        node["$path"] = "sources/" + dest.name
    on_model["name"] = "GQ802_PHYSICAL_ANNEX_ON39_PRIVATE_NO_RC"
    off_model["name"] = "GQ802_PHYSICAL_ANNEX_OFF36_FORMAL_EXACT"
    on = out / "ON39.project.json"
    off = out / "OFF36.project.json"
    on.write_text(json.dumps(on_model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    off.write_text(json.dumps(off_model, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert len(flat_project(on_model)) == 39
    assert len(flat_project(off_model)) == 36
    receipt_out = {
        "feature_id": "GQ802_STAGE_PHYSICAL_ANNEX_V1",
        "formal_rc_head": official_head,
        "formal_rc_36_source_place_sha256": digest(place),
        "added_exact_script_count": 3,
        "on39_source_count": 39,
        "off36_original_byte_exact": True,
        "stage_original_git_blob": ORIGINAL_STAGE_BLOB,
        "original_36_source_sha256": {"/".join(k): hashlib.sha256(v.encode()).hexdigest()
                                      for k, (_, v) in sorted(original.items())},
        "new_authorities": 0,
        "official_rc_adopted": False,
        "studio_2client": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "fun_art": "NOT_TESTED",
        "rollback": "OFF36 exact unchanged, omit all three additive Studio-only scripts",
    }
    (out / "GQ802_SOURCE_SELECTION_RECEIPT.json").write_text(
        json.dumps(receipt_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GQ802_OFFICIAL36_TO39_SOURCE_EXACT_SELECTED", len(original), len(flat_project(on_model)))


def verify(on: Path, off: Path, original_place: Path, selected_place: Path,
           off_place: Path, receipt: Path):
    verify_built(on, selected_place, 39)
    verify_built(off, off_place, 36)
    old = tree_scripts(ET.parse(original_place).getroot())
    selected = tree_scripts(ET.parse(selected_place).getroot())
    rollback = tree_scripts(ET.parse(off_place).getroot())
    if rollback != old or {k: selected[k] for k in old} != old:
        raise ValueError("RED_CORE36_SOURCE_CLASS_MUTATED")
    if set(selected) - set(old) != set(EXTENSIONS):
        raise ValueError("RED_ADDITIONAL_RUNTIME_WRITERS")
    report = json.loads(receipt.read_text(encoding="utf-8"))
    report["candidate_place_bytes"] = selected_place.stat().st_size
    report["candidate_place_sha256"] = digest(selected_place)
    report["rollback_off36_place_bytes"] = off_place.stat().st_size
    report["rollback_off36_place_sha256"] = digest(off_place)
    report["real_rojo_source_class_39"] = True
    report["real_rojo_off36_originals"] = True
    receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GQ802_REAL39_SOURCE_CLASS_EXACT_AND_OFF36_ROLLBACK_GREEN")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("action", choices=["compose", "verify"])
    p.add_argument("--place", type=Path, required=True)
    p.add_argument("--template", type=Path)
    p.add_argument("--receipt", type=Path, required=True)
    p.add_argument("--out", type=Path)
    p.add_argument("--head", default=RC_HEAD)
    p.add_argument("--on", type=Path)
    p.add_argument("--off", type=Path)
    p.add_argument("--on-place", type=Path)
    p.add_argument("--off-place", type=Path)
    a = p.parse_args()
    if a.action == "compose":
        compose(a.place, a.template, a.receipt, a.out, a.head)
    else:
        verify(a.on, a.off, a.place, a.on_place, a.off_place, a.receipt)
