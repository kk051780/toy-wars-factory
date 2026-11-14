#!/usr/bin/env python3
"""FB-016: source-exact additive RC78 -> RC80 no-occlusion passage/shoreline repair."""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPECS={
    "server/FoliagePassageFix.server.luau":(
        HERE/"features/fb016_passage/FoliagePassageFix.server.luau",
        "86180c0596b9e3fcfe69b816610f7ba5605b6055"),
    "client/FoliageCameraFade.client.luau":(
        HERE/"features/fb016_passage/FoliageCameraFade.client.luau",
        "0df4bf00148b9067f46a554671d3281391cd06be"),
}
FEATURE="FB016_FOLIAGE_PASSAGE_20261114"
BASE_COUNT=78
FINAL_COUNT=80

def gitblob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),("UNSAFE_PATH",p)
    source=root/"src"
    return {p.relative_to(source).as_posix():p.read_bytes()
            for p in sorted(source.rglob("*.luau"))}

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"OFF_MUST_NOT_TOUCH_OUTPUT"
        print("FB016_SWITCH_OFF_ZERO_WRITE_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==BASE_COUNT,("REQUIRE_VERIFIED_RC78",len(before))
    required={
        "server/Game.server.luau",
        "server/Owner361CastleBattlefield.server.luau",
        "server/FantasyWorldArt.server.luau",
        "server/H1SeaGroundRepair.server.luau",
        "server/SoloTeamBots.luau",
        "client/BattleHUDGovernor.client.luau",
    }
    assert required.issubset(before),("MISSING_P0_SOURCE",required-set(before))
    assert not any(p in before for p in SPECS)
    source_pin={p:gitblob(b) for p,b in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    project=json.loads((base/"default.project.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==BASE_COUNT
    assert sl["blobs"]==fl["source_gitblobs"]==source_pin
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    starter=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert "FoliageCameraFade" not in starter
    assert FEATURE not in fl["feature_flags"]
    added={}
    for dest,(source,sha) in SPECS.items():
        data=source.read_bytes()
        assert gitblob(data)==sha,("PIN_DRIFT",dest)
        assert b"RunService:IsStudio()" in data
        assert not any(x in data for x in (
            b"DataStoreService",b"MarketplaceService",b"OnServerEvent:Connect(",
            b"TakeDamage(",b"FireServer(",b"UpdateAsync(",b"TeleportService"))
        added[dest]=data
    assert b"FOREST_TRUNK_" in added["server/FoliagePassageFix.server.luau"]
    assert b"FB011_REAL_OCEAN_CHANNEL_V2" in added["server/FoliagePassageFix.server.luau"]
    assert b"LocalTransparencyModifier" in added["client/FoliageCameraFade.client.luau"]
    after=dict(before);after.update(added)
    assert len(after)==FINAL_COUNT
    next_pins={p:gitblob(b) for p,b in sorted(after.items())}
    starter["FoliageCameraFade"]={"$path":"src/client/FoliageCameraFade.client.luau"}
    sl["total_scripts"]=FINAL_COUNT;sl["blobs"]=next_pins
    fl["total_sources"]=FINAL_COUNT;fl["source_gitblobs"]=next_pins
    fl["feature_flags"][FEATURE]=True
    receipt={
        "id":FEATURE, "owner_feedback":"FB-016", "base_source_count":78,
        "result_source_count":80, "original78_byte_exact":True,
        "new_sources":{k:sha for k,(_,sha) in SPECS.items()},
        "parent_egg_hp_score_store_game_unchanged":True,
        "dryland_top_y_still_minus_one":True,
        "studio_retest":"REQUIRED", "owner_acceptance":"NOT_TESTED",
        "rollback":"omit this one additive overlay to restore RC78",
    }
    sl["fb016_passage"]=receipt
    fl["fb016_passage"]=receipt
    temp=Path(tempfile.mkdtemp(prefix=".fb016_",dir=str(out.parent)))
    staged=temp/"dist"
    try:
        shutil.copytree(base,staged,symlinks=False)
        for dest,data in added.items():
            target=staged/"src"/dest
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(data)
        (staged/"SOURCE_LOCK.json").write_text(
            json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(
            json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"default.project.json").write_text(
            json.dumps(project,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after
        assert all(read(base)[p]==b for p,b in before.items())
        os.replace(staged,out)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    print("FB016_RC80_SOURCE_LOCK_78_PRESERVED_TWO_ADDED_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
