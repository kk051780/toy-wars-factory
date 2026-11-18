#!/usr/bin/env python3
"""Non-destructive Real64 candidate -> official Real63 successor Real65 intake.

Only the preexisting Host/Combat/Invul singleton sources may change, and only
by a conflict-free diff3 from official Real62.  All 63 real official sources
(including basic attack and dodge) are preserved except those three owners.
No Roblox publishing, Store mutation, payment, or second HP/Remote owner.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose_real63 import from_xml, flatten, put_project, sha

CURRENT = "ad602cebafc1a9d8caed078ab86c7a58b0fbbbef"
HOST = ("ServerScriptService", "EGGRUMBLE_LobbyCastleModesPreview")
COMBAT = ("ServerScriptService", "EGGRUMBLE_SevenRoleCombat")
INVUL = ("ServerScriptService", "EGGRUMBLE_InvulRuntime")
HUD = ("StarterPlayer", "StarterPlayerScripts", "EGGRUMBLE_HudIntelRuntime")
BASIC = ("ServerScriptService", "EGGRUMBLE_BasicMobilityPolicy")
VIRAL = ("StarterPlayer", "StarterPlayerScripts", "GQ8_ViralCapture")
COUNTER = ("ServerScriptService", "EGGRUMBLE_InvulCounterNeutral")
MODIFIED = {HOST, COMBAT, INVUL}
ADDED = {VIRAL, COUNTER}

def diff3(base: bytes, current: bytes, author: bytes, route: tuple) -> bytes:
    if base == author:
        raise ValueError("RED_EMPTY_AUTHOR_CHANGE_" + "/".join(route))
    if current == base:
        return author
    with tempfile.TemporaryDirectory(prefix="gq8real65-") as d:
        root = Path(d)
        for name, body in (("current", current), ("base", base), ("author", author)):
            (root / name).write_bytes(body)
        p = subprocess.run(
            ["git", "merge-file", "-p", "--diff3",
             str(root/"current"), str(root/"base"), str(root/"author")],
            check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0 or b"<<<<<<<" in p.stdout or b">>>>>>>" in p.stdout:
        raise ValueError("RED_AUTHORITY_MERGE_CONFLICT_" + "/".join(route))
    if p.stdout in (base, current):
        raise ValueError("RED_AUTHOR_PATCH_LOST_" + "/".join(route))
    return p.stdout

def run(base62_path: Path, official63_path: Path, receipt63_path: Path,
        candidate64_path: Path, out: Path) -> None:
    rc = json.loads(receipt63_path.read_text(encoding="utf8"))
    if not (
        rc.get("candidate_git_head") == CURRENT
        and rc.get("official_rc_adopted") is True
        and rc.get("candidate_sources") == 63
        and rc.get("native") == "PASS"
        and rc.get("rojo") == "PASS"
        and rc.get("place_sha256") == sha(official63_path.read_bytes())
    ):
        raise ValueError("RED_FORMAL63_RECEIPT_NOT_SAME_HEAD")
    formal62 = from_xml(base62_path)
    formal63 = from_xml(official63_path)
    doc, candidate64 = flatten(candidate64_path)
    if len(formal62) != 62 or len(formal63) != 63 or len(candidate64) != 64:
        raise ValueError("RED_SOURCE_COUNTS_62_63_64")
    if set(formal63) != set(formal62) | {BASIC} or set(candidate64) != set(formal62) | ADDED:
        raise ValueError("RED_SOURCE_ROUTES_CHANGED")
    if formal63[HOST][0] != "Script" or formal63[BASIC][0] != "ModuleScript":
        raise ValueError("RED_ORIGINAL_HOST_OR_BASIC_CLASS")
    if formal63[HUD] == formal62[HUD] or formal63[COMBAT] == formal62[COMBAT]:
        raise ValueError("RED_REAL63_OPERATIONAL_FIX_ABSENT")
    for route in formal62:
        if route not in {COMBAT, HUD} and formal63[route] != formal62[route]:
            raise ValueError("RED_REAL63_UNRELATED_SOURCE_CHANGED_" + "/".join(route))
        if route not in MODIFIED and candidate64[route] != formal62[route]:
            raise ValueError("RED_CANDIDATE64_OVERWRITE_" + "/".join(route))
    result = dict(formal63)
    for route in MODIFIED:
        original = formal62[route]
        current = formal63[route]
        author = candidate64[route]
        if (original[0], current[0], author[0]) != (current[0],)*3:
            raise ValueError("RED_SINGLETON_CLASS_DRIFT_" + "/".join(route))
        result[route] = (current[0], diff3(original[1], current[1], author[1], route))
    for route in ADDED:
        result[route] = candidate64[route]
    if len(result) != 65:
        raise ValueError("RED_REAL65_TOTAL")
    for route in formal63:
        if route not in MODIFIED and result[route] != formal63[route]:
            raise ValueError("RED_FORMAL63_SOURCE_LOSS_" + "/".join(route))
    combat = result[COMBAT][1]
    for token in (b"EGGRUMBLE_BASIC_ATTACK", b"EGGRUMBLE_DODGE_STEP",
                  b"EGGRUMBLE_BasicMobilityPolicy"):
        if token not in combat:
            raise ValueError("RED_REAL63_GAMEPLAY_LOST")
    if result[HOST][0] != "Script":
        raise ValueError("RED_HOST_NOT_AUTOSTART")
    if out.exists():
        raise ValueError("RED_REFUSE_OVERWRITE")
    out.mkdir(parents=True)
    on = put_project(doc, result, out/"on65")
    off = put_project(doc, formal63, out/"off63")
    if flatten(on)[1] != result or flatten(off)[1] != formal63:
        raise ValueError("RED_NEW_PROJECT_SOURCE_MISMATCH")
    on.rename(on.with_name("EGGRUMBLE_REAL65.project.json"))
    off.rename(off.with_name("EGGRUMBLE_OFF63.project.json"))
    receipt = {
        "schema": "GQ8_REAL65_FORMAL63_NONOVERLAP_V1",
        "latest_formal_head": CURRENT,
        "official_rc_adopted": False,
        "parent_actual_source_count": 63,
        "candidate_actual_source_count": 65,
        "original_official63_unchanged": 60,
        "changed_existing_singletons": ["/".join(x) for x in sorted(MODIFIED)],
        "added_sources": ["/".join(x) for x in sorted(ADDED)],
        "retained_original_basic_and_dodge": True,
        "retained_original_trade3_and_hud": True,
        "host_script_autostart": True,
        "new_store_or_damage_owner": False,
        "published": False,
        "paid_trade": False,
        "studio_2client": "NOT_TESTED",
        "android15": "NOT_TESTED",
        "fun": "NOT_TESTED",
        "rollback": "OFF63 full byte-exact original current official Real63 Studio Place",
        "sources": [
            {"route": "/".join(k), "class": cls, "bytes":len(body),
             "sha256": sha(body)}
            for k,(cls,body) in sorted(result.items())
        ]
    }
    (out/"REAL65_INTAKE_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True)+"\n",
        encoding="utf8")
    print("REAL65_OFFICIAL63_PRESERVED_60_OF_63_PLUS_VIRAL_COUNTER_2")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    for key in ("base62", "official63", "receipt63", "candidate64", "out"):
        p.add_argument("--"+key, type=Path, required=True)
    a=p.parse_args()
    run(a.base62, a.official63, a.receipt63, a.candidate64, a.out)
