#!/usr/bin/env python3
"""FB019: assert source-exact 80 Luau scripts in isolated Studio Rojo Place."""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from apply_fb019_attack_cue import source_map, blob, TARGET, FEATURE

def verify(dist: Path, place: Path, receipt: Path):
    sources = source_map(dist)
    assert len(sources) == 80 and TARGET in sources
    pins = {p: blob(raw) for p, raw in sorted(sources.items())}
    sl = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
    fl = json.loads((dist / "RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["blobs"] == fl["source_gitblobs"] == pins
    assert sl["total_scripts"] == fl["total_sources"] == 80
    assert fl["feature_flags"][FEATURE] is True
    assert fl["fb019_attack_input"]["other79_byte_exact"] is True
    expected = collections.Counter(raw.decode("utf8") for raw in sources.values())
    actual = collections.Counter()
    names = collections.Counter()
    for item in ET.parse(place).iter("Item"):
        if item.get("class") not in ("Script", "LocalScript", "ModuleScript"):
            continue
        props = item.find("Properties")
        if props is None:
            continue
        src = props.find("string[@name='Source']")
        if src is not None:
            actual[src.text or ""] += 1
        name = props.find("string[@name='Name']")
        if name is not None:
            names[(item.get("class"), name.text)] += 1
    assert expected == actual and sum(actual.values()) == 80, "PLACE_SOURCE_MISMATCH"
    assert names[("Script", "Game")] == 1
    assert names[("LocalScript", "TrapRaidersHUD")] == 1
    text = sources[TARGET].decode("utf8")
    assert text.count('if kind == "ATTACK" then fb019ShowAttemptedSwing() end') == 1
    assert text.count('remote:FireServer({action = kind, role = role, seq = seq})') == 1
    assert 'FB019_AttackInput_CosmeticOnly' in text
    result = {
        "feature": FEATURE, "status": "PRIVATE_SOURCE_QA_ONLY",
        "total_luau": 80, "source_exact": True,
        "one_game": True, "one_existing_remote_path": True,
        "only_client_hud_changed": True, "other_79_unchanged": True,
        "attack_visual_attempt_only": True, "server_damage_not_repaired": True,
        "place_bytes": place.stat().st_size,
        "place_sha256": hashlib.sha256(place.read_bytes()).hexdigest(),
        "pc_studio": "NOT_TESTED", "android": "NOT_TESTED",
        "owner_accepted": False, "official_rc_adopted": False
    }
    receipt.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", "utf8")
    print("FB019_PRIVATE80_EXACT_ATTACK_ATTEMPT_CUE_PASS", result["place_bytes"])

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--dist", type=Path, required=True)
    p.add_argument("--place", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    verify(a.dist, a.place, a.receipt)
