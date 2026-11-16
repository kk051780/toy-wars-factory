#!/usr/bin/env python3
"""GQ spatial fix generator: ONE locked, isolated V3 host block; never writes original."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHOR = ROOT / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
HOST = AUTHOR / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
ITEMS = AUTHOR / "EGGRUMBLE_RaidItemIntake.luau"
ORIGINAL_GIT_BLOB = "7162b209bf67b74a71553217f3f744e072a0365d"
OLD = (
    '  local ridge=block(session.world,"CentralRidge",root+Vector3.new(-620,15,475),\n'
    '   Vector3.new(54,34,190),Color3.fromRGB(105,103,93))\n'
    '  ridge.Material=Enum.Material.Slate'
)
NEW = (
    '  -- GQ ridge access: preserve the stone shoulders, expose the middle route and SHIELD.\n'
    '  -- The 24-stud clear passage remains wide enough for humans and AI.\n'
    '  local centerPassage=24\n'
    '  local sideWidth=(54-centerPassage)/2\n'
    '  for _,side in ipairs({-1,1}) do\n'
    '   local ridgeOffset=side*(centerPassage/2+sideWidth/2)\n'
    '   local ridge=block(session.world,if side==-1 then "CentralRidge" else "CentralRidgeRight",\n'
    '    root+Vector3.new(-620+ridgeOffset,15,475),Vector3.new(sideWidth,34,190),Color3.fromRGB(105,103,93))\n'
    '   ridge.Material=Enum.Material.Slate\n'
    '  end'
)

def git_blob(text: str) -> str:
    data = text.encode("utf-8")
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()

def patch_author_host(source: str, item_source: str) -> str:
    """Fail closed on original-source drift, duplicate patch and different item geometry."""
    if git_blob(source) != ORIGINAL_GIT_BLOB:
        raise ValueError("RED: original #482 host Git blob changed; do not auto-rebase")
    if source.count(OLD) != 1 or "CentralRidgeRight" in source:
        raise ValueError("RED: expected single original ridge block missing or already patched")
    if item_source.count('{x=0,z=470,kind="SHIELD"}') != 1:
        raise ValueError("RED: original raid item site changed; repeat spatial review")
    if item_source.count('xCenter=if session.mode=="TEAM" then -620 else 620') != 1:
        raise ValueError("RED: source ITEM mode origin changed; repeat spatial review")
    if source.count('if mode=="TEAM" then\n  local ridge=block') != 1:
        raise ValueError("RED: original mode-specific ridge placement changed")
    return source.replace(OLD, NEW)

def collision_report() -> dict:
    """Source geometry, offsets relative to shared root; not an engine physics test."""
    ridge = {"x_min": -647.0, "x_max": -593.0, "y_min": -2.0, "y_max": 32.0,
             "z_min": 380.0, "z_max": 570.0}
    pickup = {"x": -620.0, "y": 1.8, "z": 470.0, "radius": 1.1}
    before_embedded = (
        ridge["x_min"] <= pickup["x"]-pickup["radius"]
        and pickup["x"]+pickup["radius"] <= ridge["x_max"]
        and ridge["z_min"] <= pickup["z"] <= ridge["z_max"]
        and ridge["y_min"] <= pickup["y"] <= ridge["y_max"]
    )
    central_free_half_width = 12.0
    clear_margin = central_free_half_width-pickup["radius"]
    return {
        "mode": "TEAM",
        "site": "SHIELD @ route 2 / x=0,z=470",
        "before_embedded_in_collidable_ridge": before_embedded,
        "after_open_passage_studs": 24.0,
        "after_pickup_edge_margin_each_side_studs": clear_margin,
        "other_modes_changed": False,
        "engine_verified": False,
    }

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="generated private host path (never original)")
    args = parser.parse_args()
    source = HOST.read_text(encoding="utf-8")
    item_source = ITEMS.read_text(encoding="utf-8")
    patched = patch_author_host(source, item_source)
    report = collision_report()
    if not report["before_embedded_in_collidable_ridge"] or report["after_pickup_edge_margin_each_side_studs"] < 8:
        raise SystemExit("RED: geometric clearance assertion failed")
    if args.output:
        out = args.output.resolve()
        if out == HOST.resolve() or HOST.resolve().is_relative_to(out):
            raise SystemExit("RED: refusing output into original author path")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(patched, encoding="utf-8")
        report["generated_private_host"] = str(out)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))

if __name__ == "__main__":
    main()
