#!/usr/bin/env python3
"""Verify a REAL latest-parent 69-source Rojo Place; never self-certify Studio."""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET
import compose_fb015_art_motion as mod


def check(parent: Path, dist: Path, place: Path, receipt: Path):
    # -O / PYTHONOPTIMIZE erases Python 'assert'. Fail closed BEFORE writing
    # any source-exact receipt; optimised runs are never certified.
    if not __debug__:
        raise RuntimeError("P0D_ROJO69_OPTIMIZED_VALIDATOR_REFUSED")
    parent, dist, place, receipt = (p.resolve() for p in (parent,dist,place,receipt))
    mod.check_output(parent, dist)  # independently pinned parent68 full tree
    sources = mod.source_map(dist)
    assert len(sources) == 69, "REPIN_MOTION69_WRONG_SOURCE_COUNT"
    expected = collections.Counter(raw.decode("utf8") for raw in sources.values())
    embedded = collections.Counter()
    names = collections.Counter()
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        if item.get("class") not in ("Script", "ModuleScript", "LocalScript"):
            continue
        text = item.find("./Properties/string[@name='Source']")
        if text is None:
            continue
        embedded[text.text or ""] += 1
        name = item.find("./Properties/string[@name='Name']")
        if name is not None:
            names[item.get("class"),name.text] += 1
    assert embedded == expected, "REPIN_MOTION69_ROJO_EXACT_EMBEDDED_69_FAILED"
    for key in (
        ("Script","Game"),("ModuleScript","MusouHorde"),
        ("Script","ArtMinionSilhouette"),("LocalScript","ArtCombatSlash"),
        ("LocalScript","P0DNeutralMotion"),
    ):
        assert names[key] == 1, ("MOTION69_UNEXPECTED_AUTHORITY_OR_MISSING_ART",key,names[key])
    source_lock = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
    feature_lock = json.loads((dist / "RC_FEATURE_LOCK.json").read_text("utf8"))
    pins = {name:mod.blob(raw) for name,raw in sorted(sources.items())}
    assert source_lock["total_scripts"] == feature_lock["total_sources"] == 69
    assert source_lock["blobs"] == feature_lock["source_gitblobs"] == pins
    parent_pins=json.loads((parent/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]
    parent_fingerprint=hashlib.sha256(json.dumps(
        parent_pins,sort_keys=True,separators=(",",":")).encode("utf8")).hexdigest()
    print("P0D_FB015_PINNED_PARENT68_ALL_68_SOURCE_MAP_SHA256",parent_fingerprint)
    assert feature_lock["feature_flags"][mod.FLAG] is True
    assert pins[mod.DEST] == mod.PIN
    assert pins["server/MusouHorde.luau"] == mod.ORIGINAL_HORDE
    assert pins["server/ArtMinionSilhouette.server.luau"] == mod.ORIGINAL_MINION
    assert sources["server/Game.server.luau"].count(
        b"remote.OnServerEvent:Connect(") == 1, "MULTIPLE_GAME_AUTHORITIES"
    raw = place.read_bytes()
    result = {
        "result": "P0D_FB015_LATEST_PARENT_REAL_ROJO69_SOURCE_EXACT_PASS",
        "candidate": "PRIVATE_NOT_OFFICIAL",
        "source_count": 69,
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True).strip(),
        "parent_horde_blob":mod.ORIGINAL_HORDE,
        "parent_minion_blob":mod.ORIGINAL_MINION,
        "parent68_full_source_map_sha256":parent_fingerprint,
        "motion_blob":mod.PIN,
        "place_bytes": len(raw),
        "place_sha256":hashlib.sha256(raw).hexdigest(),
        "official_rc_adopted":False,
        "studio":"NOT_TESTED",
        "android":"NOT_TESTED",
        "sourcery_signoff":"PENDING",
        "owner_fun":"ART_NO_GO",
    }
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    for name,item in (("SOURCE_LOCK.json",source_lock),
                      ("RC_FEATURE_LOCK.json",feature_lock)):
        (receipt.parent/name).write_text(
            json.dumps(item,ensure_ascii=False,indent=2)+"\n","utf8")
    print(result)


if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    p.add_argument("--receipt",type=Path,required=True)
    args=p.parse_args()
    check(args.parent,args.dist,args.place,args.receipt)
