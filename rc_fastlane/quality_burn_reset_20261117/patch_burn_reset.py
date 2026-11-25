#!/usr/bin/env python3
"""GQ8: clear only the old-round burn-reapply lock during RoundReplay.resetHuman.
Run AFTER GQ8 all-shield selection, never replace the original #686 cleanup.
Current31 module selection, exact inverse, 30 untouched modules, real Rojo check.
"""
import argparse
import copy
import hashlib
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "quality_shield_cleanup_20261117"))
from select_shield import mapping

FEATURE = "GQ8_BURN_REPLAY_RESET_20261117"
MODULE = "EGGRUMBLE_RoundReplay"
ANCHOR = ' hum:SetAttribute("EGGRUMBLE_MarkedUntil",nil)\n'
PATCH = (
    ANCHOR
    + " -- GQ8_BURN_REPLAY_RESET_20261117: clear old-round burn reapply lock.\n"
    + ' hum:SetAttribute("EGGRUMBLE_BurnUntil",nil)\n'
)
SOURCE_NAME = "EGGRUMBLE_RoundReplay_GQ8_BURN_RESET.luau"
RECEIPT = "GQ8_BURN_RESET_RECEIPT.json"
SHIELD_OWNER = "GQ8_MULTI_SHIELD_REPLAY_CLEANUP_END"


def patch(src: str) -> str:
    if SHIELD_OWNER not in src:
        raise ValueError("RED_SHIELD_OWNER_BASE_NOT_SELECTED")
    if src.count(ANCHOR) != 1 or FEATURE in src or "EGGRUMBLE_BurnUntil" in src:
        raise ValueError("RED_REPLAY_BURN_ANCHOR_DRIFT")
    if src.count("function Replay.resetHuman(") != 1 or src.count("function Replay.captureWalkBaseline(") != 1:
        raise ValueError("RED_REPLAY_OWNER_DRIFT")
    out = src.replace(ANCHOR, PATCH, 1)
    if unpatch(out) != src:
        raise ValueError("RED_BURN_OFF_NOT_BYTE_EXACT")
    return out


def unpatch(src: str) -> str:
    if src.count(PATCH) != 1:
        raise ValueError("RED_BURN_OFF_ANCHOR_DRIFT")
    return src.replace(PATCH, ANCHOR, 1)


def load_pair(base: Path, out: Path):
    _, original, key = mapping(base)
    _, current, now_key = mapping(out)
    if key != now_key or set(original) != set(current) or len(original) != 31:
        raise ValueError("RED_SCRIPT_COUNT_OR_OWNER_CHANGED")
    before = original[key].read_text(encoding="utf-8")
    after = current[key].read_text(encoding="utf-8")
    if patch(before) != after or unpatch(after) != before:
        raise ValueError("RED_BURN_PATCH_OR_ROLLBACK_CHANGED")
    changes = [k for k in original if original[k].read_bytes() != current[k].read_bytes()]
    if changes != [key]:
        raise ValueError("RED_OTHER30_GAME_SOURCES_CHANGED")
    return current, key, before, after


def prepare(base: Path, out: Path) -> None:
    base = base.resolve(strict=True)
    out = out.resolve()
    if out.exists() or out.parent != base.parent:
        raise ValueError("RED_OUTPUT_COLLISION_OR_DIRECTORY")
    project, originals, key = mapping(base)
    original = originals[key].read_text(encoding="utf-8")
    changed = patch(original)
    file = out.parent / SOURCE_NAME
    receipt = out.parent / RECEIPT
    if file.exists() or receipt.exists():
        raise ValueError("RED_SOURCE_COLLISION")
    file.write_text(changed, encoding="utf-8")
    new_project = copy.deepcopy(project)
    node = new_project["tree"]
    for segment in key:
        node = node[segment]
    node["$path"] = SOURCE_NAME
    out.write_text(json.dumps(new_project, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _, _, before, after = load_pair(base, out)
    receipt.write_text(json.dumps({
        "feature_id": FEATURE, "source_count": 31, "existing_module": MODULE,
        "base_project": base.name, "selected_project": out.name,
        "changed_existing_script_count": 1, "other30_exact": True,
        "rollback_source_exact": True, "new_game_remote_store": 0,
        "base_round_replay_sha256": hashlib.sha256(before.encode()).hexdigest(),
        "selected_round_replay_sha256": hashlib.sha256(after.encode()).hexdigest(),
        "original_owner": "GQ8_MULTI_SHIELD_REPLAY_CLEANUP_20261117",
        "native": "PENDING", "rojo": "PENDING",
        "studio_android_owner": "NOT_TESTED"
    }, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ8_BURN_PREP_31_ONE_ROUNDREPLAY_30_IDENTICAL_OFF_EXACT_PASS")


def verify(base: Path, out: Path, place: Path) -> None:
    current, _, before, after = load_pair(base.resolve(strict=True), out.resolve(strict=True))
    actual = {}
    for entry in ET.parse(place).getroot().iter("Item"):
        klass = entry.get("class")
        if klass not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = entry.find("Properties")
        if props is None:
            raise ValueError("RED_MISSING_SCRIPT_PROPERTIES")
        name = props.findtext("string[@name='Name']")
        src = props.findtext("ProtectedString[@name='Source']")
        if src is None:
            src = props.findtext("string[@name='Source']")
        if not name or src is None or name in actual:
            raise ValueError("RED_DUPLICATE_OR_MISSING_ROJO_SOURCE")
        actual[name] = (klass, src.replace("\r\n", "\n"))
    if len(actual) != 31 or set(actual) != {key[-1] for key in current}:
        raise ValueError("RED_NOT_CANONICAL31")
    for key, file in current.items():
        klass = ("Script" if file.name.endswith(".server.luau") else
                 "LocalScript" if file.name.endswith(".client.luau") else "ModuleScript")
        if actual[key[-1]] != (klass, file.read_text(encoding="utf-8").replace("\r\n", "\n")):
            raise ValueError("RED_SOURCE_CLASS_MISMATCH_" + key[-1])
    receipt = out.parent / RECEIPT
    info = json.loads(receipt.read_text(encoding="utf-8"))
    if info["base_round_replay_sha256"] != hashlib.sha256(before.encode()).hexdigest():
        raise ValueError("RED_SOURCE_LOCK")
    if info["selected_round_replay_sha256"] != hashlib.sha256(after.encode()).hexdigest():
        raise ValueError("RED_SELECTED_LOCK")
    info.update(native="31/31", rojo="31/31",
                place_bytes=place.stat().st_size,
                place_sha256=hashlib.sha256(place.read_bytes()).hexdigest())
    receipt.write_text(json.dumps(info, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print("GQ8_BURN_REAL_ROJO31_30_IDENTICAL_OFF_EXACT_PASS", info["place_bytes"])


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("command", choices=("prepare", "verify"))
    p.add_argument("--base", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--place", type=Path)
    args = p.parse_args()
    if args.command == "prepare":
        prepare(args.base, args.out)
    else:
        if args.place is None:
            p.error("--place is required for verify")
        verify(args.base, args.out, args.place)
