#!/usr/bin/env python3
"""#431 nonStudio-compatible, private-only 60-part twin-biome forest for real MapBuilder.

Adds a NEW decorative Script to genuine canonical RC81 distro with live-safe castle:
all previous 81 untouched, 82 real Rojo sources. B #220 alone owns official CAS.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path

HERE=Path(__file__).resolve().parent
AUTHOR=HERE/"features/live_art/P0DLiveForestArt.server.luau"
AUTHOR_BLOB="bff8b2122bb73cd035ae09e8d965d0b39553a593"
DEST="server/P0DLiveForestArt.server.luau"
FEATURE="P0D_PRIVATE_LIVE_FOREST_MOBILE60_V1"
OFFICIAL_PARENT="bab8e93bfe0bce0baddfe64ee2898962486058af"
BASE_MAP="server/MapBuilder.luau"

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink(),"MISSING_SOURCE_DIR"
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),("SOURCE_SYMLINK_REFUSED",p)
    src=root/"src"
    assert src.is_dir()
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def author(raw:bytes)->None:
    assert blob(raw)==AUTHOR_BLOB,("FOREST_ART_AUTHOR_DRIFT",blob(raw))
    text=raw.decode("utf8")
    for require in (
        'if not RunService:IsServer() then return end',
        'if game.PrivateServerId == "" then return end',
        'workspace:GetAttribute("P0D_PRIVATE_LIVE_FOREST") ~= true then return end',
        'if script:GetAttribute("EnablePrivatePreview") ~= true then return end',
        'workspace:WaitForChild("TRAP_RAIDERS_S1",45)',
        'local BUDGET = 60',
        'assert(made == BUDGET,',
        'p.CanCollide = false','p.CanTouch = false',
        'p.CanQuery = false','p.CastShadow = false',
        '"NORTH_FROST_CEDAR"','"SOUTH_SUNSET_BLOSSOM"',
        'if root:FindFirstChild("P0D_PRIVATE_LIVE_FOREST_V1") then return end',
    ):
        assert require in text,("MISSING_AUTHOR_SOURCE_GUARD",require)
    assert "if not RunService:IsStudio() then return end" not in text
    for denied in ('Instance.new("ScreenGui")','Instance.new("BillboardGui")',
                  "FireServer(","OnServerEvent:Connect(","GetDataStore(",
                  "TakeDamage(","UpdateAsync(","Terrain:FillBlock(",
                  "grass.Size =","arena.Size =","p.CanCollide = true",
                  "p.CanQuery = true","Lighting.ClockTime",
                  'Instance.new("PointLight")',"MarketplaceService"):
        assert denied not in text,("UNSAFE_FOREST_ART_SOURCE",denied)

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"OFF_ZERO_WRITES"
        print("LIVE_FOREST_PRIVATE_OFF_ZERO_WRITE")
        return False
    base=base.resolve()
    out=out.absolute()
    assert base.is_dir() and not base.is_symlink()
    assert out.parent.is_dir() and not out.parent.is_symlink() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==81 and DEST not in before and BASE_MAP in before and 'server/P0DLiveCastleArt.server.luau' in before
    for p in ("server/Game.server.luau","client/HUD.client.luau","server/SoloTeamBots.luau"):
        assert p in before,("MISSING_GAME_AUTHORITY",p)
    map_source=before[BASE_MAP].decode("utf8")
    for required in ('"TRAP_RAIDERS_S1"','"GrassArena"','"CenterRoad"',
                     '"RED"','"BLUE"','"_CASTLE"','Vector3.new(250, 4, 142)'):
        assert required in map_source,("BASE_MAP_BUILDER_CHANGED",required)
    pins={p:blob(data) for p,data in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    project=json.loads((base/"default.project.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert pins==sl["blobs"]==fl["source_gitblobs"],"SOURCE_LOCK_DRIFT"
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    flags=fl["feature_flags"]
    for f in ("FB017_NO_PERSISTENT_BATTLE_GUIDES",
              "FB019_RESPONSIVE_ATTACK_INPUT_SWING",
              "FB015_FOREST_BIOMES_MONUMENTS_V2",
              "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3",
              "FB016_ART_CAMERA_SIGHTLINE_V2",
              "FB015_GOROGAN_MOBILE_LOD_V1",
              "FB015_LIVE_CASTLE_SAFE_PARITY_V1"):
        assert flags.get(f) is True,("MISSING_OFFICIAL_ART4_FEATURE",f)
    assert not flags.get(FEATURE,False)
    raw=AUTHOR.read_bytes()
    author(raw)
    after={**before,DEST:raw}
    assert len(after)==82 and all(after[p]==data for p,data in before.items())
    newpins={p:blob(data) for p,data in sorted(after.items())}
    receipt={
      "feature":FEATURE,"official_parent":OFFICIAL_PARENT,
      "private_preview_only":True,"original_81_source_byte_exact":True,
      "new_script":DEST,"new_source_blob":AUTHOR_BLOB,
      "original_game_hud_remote_egg_store_unchanged":True,
      "actual_original_MapBuilder_dependency_only":True,
      "studio_preview_default":"OFF","public_server_default":"OFF",
      "private_server_only":True,
      "server_workspace_opt_in":"P0D_PRIVATE_LIVE_FOREST",
      "static_decor_parts":60,"new_collisions":0,
      "new_lights":0,"new_guis":0,
      "live_art_decision":"LIVE_ART_NO_GO",
      "art_decision":"ART_NO_GO","mobile_decision":"MOBILE_NO_GO",
      "fun_decision":"FUN_NO_GO","owner_accepted":False,
      "real_nonstudio_runtime":"NOT_TESTED",
      "android_15min":"NOT_TESTED",
      "official_rc_adopted":False,
      "rollback":"omit independent new Script; official ART4 80 source unchanged"}
    sl["total_scripts"]=fl["total_sources"]=82
    sl["blobs"]=fl["source_gitblobs"]=newpins
    sl["live_forest_private_pilot"]=fl["live_forest_private_pilot"]=receipt
    flags[FEATURE]=True
    scratch=Path(tempfile.mkdtemp(prefix=".p0d_live_forest_",dir=str(out.parent)))
    stage=scratch/"out"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/DEST).write_bytes(raw)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after and read(base)==before
        os.replace(stage,out)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    print("P0D_PRIVATE_LIVE_FOREST_RC81_TO82_ORIGINAL81_EXACT_PASS")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--enabled",choices=("true","false"),required=True)
    a=parser.parse_args()
    apply(a.base,a.out,a.enabled=="true")
