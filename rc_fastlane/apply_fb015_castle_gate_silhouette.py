#!/usr/bin/env python3
"""FB-015 fortress silhouette V3, 36 large nonblocking decorations, RC80 exact.

Only original CastleDetailArt visual script is touched. No new runtime script,
game authority, HUD, remotes, weapons, egg, score, monetization or persistence.
The studio art screenshot and Android runtime gate remain NOT_TESTED.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

TARGET = "server/CastleDetailArt.server.luau"
BASE_BLOB = "da2bf0544682f72ee02280374a27ce2f4fadb5c2"
BASE_OFFICIAL = "f4e64c9248423f9c021f633b80e554706f7a66e4"
FEATURE = "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3"
ANCHOR = "    -- Gold/stone badges face the field; avoids giant world Billboard labels."
V3 = '''    -- FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3: broad crenels, not tiny cheap neon.
    -- Keep the original gate opening and paths clear; all art is visual-only.
    -- Exactly 18 parts per castle, 36 total; no light, loop, particle or GUI.
    -- Existing gate arch spans z=-14..14. New parapet beams avoid that opening.
    for _, sign in ipairs({-1,1}) do
        ornament(art,"V3_GATE_PARAPET_BEAM_"..sign,
            Vector3.new(3.2,2.7,30),
            Vector3.new(gateX,23.3,sign*31),
            TRIM_STONE,Enum.Material.Cobblestone,"BLOCK")
    end
    for _, z in ipairs({-40,-29,-18,18,29,40}) do
        -- Large stone merlons read as a fortress even on low-res Android.
        ornament(art,"V3_GATE_MERLON_"..z,
            Vector3.new(3.1,4.4,5.0),
            Vector3.new(gateX,26.8,z),
            PALE_STONE,Enum.Material.Limestone,"BLOCK")
        ornament(art,"V3_GATE_MERLON_COPING_"..z,
            Vector3.new(3.6,.8,5.6),
            Vector3.new(gateX,29.35,z),
            BASALT,Enum.Material.Slate,"BLOCK")
    end
    for _, z in ipairs({-39,39}) do
        -- Team-color vertical standards make BLUE and RED readable without text.
        local flag = ornament(art,"V3_TEAM_COLOR_STANDARD_"..z,
            Vector3.new(.6,7.2,4.5),
            Vector3.new(gateX-side*1.9,37,z),
            theme,Enum.Material.Fabric,"WEDGE")
        flag.CastShadow = false
        ornament(art,"V3_TEAM_CREST_ROUND_"..z,
            Vector3.new(.8,2.5,2.5),
            Vector3.new(gateX-side*2.4,34,z),
            GOLD,Enum.Material.Metal,"BALL")
    end
    art:SetAttribute("FortressGateSilhouetteV3",true)
    art:SetAttribute("NewPartsV3",18)
    art:SetAttribute("AdditionalDynamicLightsV3",0)
    art:SetAttribute("NewCollisionPartsV3",0)
    art:SetAttribute("MobileSourceStaticOnly",true)

'''

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read(root: Path) -> dict[str, bytes]:
    assert root.is_dir() and not root.is_symlink(), "INPUT_MISSING_OR_LINKED"
    for path in root.rglob("*"):
        assert not path.is_symlink() and path.resolve().is_relative_to(root.resolve()), (
            "UNSAFE_PARENT_SOURCE_PATH", path)
    src = root/"src"
    assert src.is_dir()
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def patch(source: bytes) -> bytes:
    assert blob(source) == BASE_BLOB, ("CASTLE_AUTHOR_PIN_CHANGED", blob(source))
    text = source.decode("utf8")
    assert FEATURE not in text, "DUPLICATE_ADOPTION"
    assert "if not RunService:IsStudio() then return end" in text
    assert "local MAX_PARTS = 190" in text and "made += 1" in text
    assert "p.CanCollide = false" in text and "p.CanQuery = false" in text
    assert "teamCastle(-1,\"RED\"" in text and "teamCastle(1,\"BLUE\"" in text
    assert text.count(ANCHOR) == 1, "CASTLE_ART_ANCHOR_DRIFT"
    text = text.replace(ANCHOR, V3 + ANCHOR)
    assert text.count('art:SetAttribute("NewPartsV3",18)') == 1
    assert text.count("V3_GATE_MERLON_") == 2  # merlon and coping
    assert 'folder:SetAttribute("DecorativePartCount",made)' in text
    assert 'folder:SetAttribute("OwnerArtAccepted",false)' in text
    for unsafe in ("CanCollide = true", "CanQuery = true", "FireServer(",
                   "OnServerEvent:Connect(", "TakeDamage(", "MarketplaceService",
                   "GetDataStore(", 'Instance.new("ScreenGui")',
                   'Instance.new("BillboardGui")'):
        assert unsafe not in text, ("UNSAFE_CASTLE_V3", unsafe)
    return text.encode("utf8")

def apply(base: Path, out: Path, enabled: bool) -> bool:
    if not enabled:
        assert not out.exists(), "OFF_MUST_BE_ZERO_WRITE"
        print("CASTLE_V3_OFF_ZERO_WRITE_PASS")
        return False
    base = base.resolve()
    out = out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before = read(base)
    assert len(before) == 80 and TARGET in before, "REQUIRE_FULL_OFFICIAL_RC80"
    old_pins = {k: blob(v) for k,v in sorted(before.items())}
    assert old_pins[TARGET] == BASE_BLOB
    sl = json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl = json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"] == fl["total_sources"] == 80
    assert sl["blobs"] == fl["source_gitblobs"] == old_pins, "SOURCE_LOCK_TAMPER"
    for prior in ("FB016_FOLIAGE_PASSAGE_20261114",
                  "FB017_NO_PERSISTENT_BATTLE_GUIDES",
                  "FB018_ACTION_BUTTON_TEXT_INIT",
                  "FB019_RESPONSIVE_ATTACK_INPUT_SWING"):
        assert fl["feature_flags"].get(prior) is True, ("PARENT_REQUIREMENT_MISSING",prior)
    assert FEATURE not in fl["feature_flags"], "V3_ALREADY_ADOPTED"
    after = dict(before)
    after[TARGET] = patch(before[TARGET])
    assert len(after) == 80
    assert {k for k in before if before[k] != after[k]} == {TARGET}
    pins = {k: blob(v) for k,v in sorted(after.items())}
    receipt = {
        "feature_id":FEATURE, "feedback":"FB-015", "type":"ART_ONLY",
        "base_source_head_sha":BASE_OFFICIAL, "status":"A_PREP_PRIVATE_ONLY",
        "script_count":80, "modified_sources":[TARGET],
        "other_79_sources_byte_identical":True,
        "author_blob":BASE_BLOB, "new_blob":pins[TARGET],
        "new_parts_total_both_castles":36,
        "new_dynamic_lights":0, "new_particles":0,
        "new_physics_collision":0, "new_gameplay_scripts":0,
        "mobile_intent":"large distant readable shapes, no texture/GUI/loops",
        "game_logic_unchanged":True,
        "studio_pc":"NOT_TESTED", "android_15min":"NOT_TESTED",
        "owner_art":"ART_NO_GO", "official_rc_adopted":False,
        "rollback":"remove V3 overlay; restore pinned CastleDetailArt author blob",
    }
    sl["blobs"] = pins
    fl["source_gitblobs"] = pins
    sl["fb015_castle_v3"] = receipt
    fl["fb015_castle_v3"] = receipt
    fl["feature_flags"][FEATURE] = True
    scratch = Path(tempfile.mkdtemp(prefix=".p0d_castle_v3_",dir=str(out.parent)))
    stage = scratch/"out"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/TARGET).write_bytes(after[TARGET])
        (stage/"SOURCE_LOCK.json").write_text(
            json.dumps(sl,ensure_ascii=False,indent=2)+"\n", "utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(
            json.dumps(fl,ensure_ascii=False,indent=2)+"\n", "utf8")
        assert read(stage) == after and read(base) == before
        os.replace(stage,out)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    print("FB015_CASTLE_V3_SINGLE_SOURCE_PRIVATE80_OTHER79_EXACT_PASS")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    parser.add_argument("--enabled",required=True,choices=("true","false"))
    a=parser.parse_args()
    apply(a.base,a.out,a.enabled=="true")
