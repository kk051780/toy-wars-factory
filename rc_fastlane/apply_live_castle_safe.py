#!/usr/bin/env python3
"""#431 LIVE ART first production-compatible decorative castle proof.

OFF returns with no write; ON adds only one NEW visual Script to the REAL
source-locked RC80 (now 81 scripts), leaving all 80 existing bytes untouched.
Never publishes or changes the official RC. B #220 is sole writer.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
AUTHOR=HERE/"features/live_art/P0DLiveCastleArt.server.luau"
AUTHOR_BLOB="63cbac8afae039c23bc1b85a2e59cf88cb7be739"
DEST="server/P0DLiveCastleArt.server.luau"
FEATURE="FB015_LIVE_CASTLE_SAFE_PARITY_V1"
PARENT="1bf25e7e83a38ecbbef588309edd7217b9f39c67"

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read_sources(root: Path) -> dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve())
    src=root/"src"
    assert src.is_dir()
    return {p.relative_to(src).as_posix():p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}

def verify_author(raw:bytes) -> None:
    assert blob(raw)==AUTHOR_BLOB,("LIVE_CASTLE_AUTHOR_BLOB_CHANGED",blob(raw))
    txt=raw.decode("utf8")
    assert 'if not RunService:IsServer() then return end' in txt
    assert 'if RunService:IsStudio() and script:GetAttribute("EnablePrivatePreview") ~= true then' in txt
    assert 'workspace:WaitForChild("TRAP_RAIDERS_S1", 45)' in txt
    assert 'if arena:FindFirstChild("P0D_LIVE_SAFE_CASTLE_ART_V1") then return end' in txt
    assert 'for _, name in ipairs({"RED", "BLUE"}) do' in txt
    assert 'for _, child in ipairs(castle:GetChildren()) do' in txt
    assert 'assert(created == BUDGET' in txt
    assert 'local BUDGET = 36' in txt
    assert 'p.CanCollide = false' in txt and 'p.CanQuery = false' in txt
    assert 'p.CastShadow = false' in txt
    for banned in ('TakeDamage(', 'FireServer(', 'OnServerEvent:Connect(',
                   'GetDataStore(', 'MarketplaceService', 'CanCollide = true',
                   'CanQuery = true', 'Instance.new("ScreenGui")',
                   'Instance.new("BillboardGui")', 'Lighting.ClockTime',
                   'terrain:Fill', 'GrassArena.Size =', 'RemoteEvent'):
        assert banned not in txt,("LIVE_ART_FORBIDDEN_AUTHORITY",banned)

def apply(base:Path, out:Path, enabled:bool) -> bool:
    if not enabled:
        assert not out.exists(),"DISABLED_MUST_NOT_CREATE_OUTPUT"
        print("LIVE_CASTLE_PRIVATE_OFF_ZERO_WRITE")
        return False
    base=base.resolve()
    out=out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read_sources(base)
    assert len(before)==80 and DEST not in before, "REQUIRES_ORIGINAL_80_SOURCES"
    pins={k:blob(v) for k,v in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pj=json.loads((base/"default.project.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==pins,"PARENT_SOURCE_LOCK_DRIFT"
    assert pj["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    assert "server/Game.server.luau" in before
    assert "client/HUD.client.luau" in before
    for flag in ("FB016_FOLIAGE_PASSAGE_20261114",
                 "FB017_NO_PERSISTENT_BATTLE_GUIDES",
                 "FB018_ACTION_BUTTON_TEXT_INIT",
                 "FB019_RESPONSIVE_ATTACK_INPUT_SWING"):
        assert fl["feature_flags"].get(flag) is True,("MISSING_PARENT_FEATURE",flag)
    assert FEATURE not in fl["feature_flags"],"DUPLICATE_LIVE_CASTLE_ADOPTION"
    raw=AUTHOR.read_bytes()
    verify_author(raw)
    after={**before,DEST:raw}
    assert len(after)==81 and all(after[k]==v for k,v in before.items())
    pins_new={k:blob(v) for k,v in sorted(after.items())}
    receipt={
        "feature":FEATURE, "issue":"#431", "owner_rule":"#420",
        "stage":"PRIVATE_A_PREP_ONLY",
        "source_count_before":80,"source_count_after":81,
        "added_source":[DEST],"all_old80_byte_identical":True,
        "author_git_blob":AUTHOR_BLOB,
        "production_fallback":True,
        "replaces_studio_author_preview":False,
        "uses_only_MapBuilder_existing_anchors":True,
        "new_game_authority":0,"new_remote":0,"new_physics":0,
        "new_cosmetic_parts":36,"new_lights":0,"new_particles":0,
        "false_promotion_to_all_seven_live":False,
        "studio_private_preview":"NOT_TESTED",
        "actual_nonstudio_engine":"NOT_TESTED",
        "android_15_min":"NOT_TESTED",
        "owner_acceptance":False,
        "live_art_status":"LIVE_ART_NO_GO",
        "art_decision":"ART_NO_GO",
        "official_rc_adopted":False,
        "rollback":"omit one new Script; all existing official 80 sources unchanged",
    }
    sl["total_scripts"]=81
    fl["total_sources"]=81
    sl["blobs"]=pins_new
    fl["source_gitblobs"]=pins_new
    sl["fb015_live_castle_production"]=receipt
    fl["fb015_live_castle_production"]=receipt
    fl["feature_flags"][FEATURE]=True
    scratch=Path(tempfile.mkdtemp(prefix=".p0d_live_castle_",dir=str(out.parent)))
    stage=scratch/"dist"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/DEST).write_bytes(raw)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read_sources(stage)==after and read_sources(base)==before
        os.replace(stage,out)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    print("P0D_LIVE_CASTLE_PRIVATE81_ORIGINAL80_BYTE_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    args=p.parse_args()
    apply(args.base,args.out,args.enabled=="true")
