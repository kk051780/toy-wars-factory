#!/usr/bin/env python3
"""#444 private canary: restore original Horde.reset for owner-opted-in non-Studio PRIVATE servers.

SOURCE QA only: retain one original Game/Remote/damage authority and parent 81
source bytes except exact Game one-line predicate. No public enable, no Publish.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path

GAME="server/Game.server.luau"
HORDE="server/MusouHorde.luau"
FEATURE="P0D_PRIVATE_LIVE_HORDE_NINE_V1"
OPT_IN="P0D_PRIVATE_LIVE_HORDE_NINE"
OLD='if RunService:IsStudio() then horde:reset(match.serial,serverNow()) end'
NEW=('if RunService:IsStudio() or (game.PrivateServerId ~= "" '
     'and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true) '
     'then horde:reset(match.serial,serverNow()) end')

def blob(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()

def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink()
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),p
    src=root/"src"
    assert src.is_dir()
    return {p.relative_to(src).as_posix():p.read_bytes() for p in sorted(src.rglob("*.luau"))}

def patch(raw:bytes)->bytes:
    src=raw.decode("utf8")
    assert src.count(OLD)==1,("ORIGINAL_STUDIO_RESET_ANCHOR_DRIFT",src.count(OLD))
    assert src.count("horde:reset(match.serial,serverNow())")==1,"MULTIPLE_HORDE_RESET_AUTHORITY"
    assert src.count('remote.OnServerEvent:Connect(')==1,"DUPLICATE_REMOTE_AUTHORITY"
    assert FEATURE not in src and OPT_IN not in src,"REPEATED_PILOT"
    if "if RunService:IsStudio() then horde:reset" not in src:
        raise AssertionError("Horde Studio ONLY provenance missing")
    out=src.replace(OLD,NEW,1)
    assert out.replace(NEW,OLD,1)==src
    assert out.count("horde:reset(match.serial,serverNow())")==1
    assert out.count("game.PrivateServerId ~= "+'""')==1
    assert out.count('workspace:GetAttribute("'+OPT_IN+'") == true')==1
    assert out.count('remote.OnServerEvent:Connect(')==1
    return out.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    assert not out.exists(),"OUT_MUST_NOT_EXIST"
    if not enabled:
        print("PRIVATE_LIVE_HORDE_OFF_ZERO_WRITES");return False
    base=base.resolve()
    out=out.parent.resolve(strict=True)/out.name
    assert base.is_dir() and out.parent.is_dir() and not out.is_relative_to(base)
    original=read(base)
    assert len(original)==81 and GAME in original and HORDE in original
    origpins={p:blob(s) for p,s in sorted(original.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==origpins,"PARENT_SOURCE_LOCK_DRIFT"
    for previous in (
        "FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2",
        "FB015_FOREST_BIOMES_MONUMENTS_V2",
        "FB015_CASTLE_GATE_SILHOUETTE_MOBILE_V3",
        "FB016_ART_CAMERA_SIGHTLINE_V2",
        "FB015_GOROGAN_MOBILE_LOD_V1",
        "FB015_LIVE_CASTLE_SAFE_PARITY_V1",
    ):
        assert fl["feature_flags"].get(previous) is True,("MISSING_PRIOR_STAGE",previous)
    assert FEATURE not in fl["feature_flags"],"DUPLICATE_CANARY"
    receiptV2=fl["fb019_hit_visibility"]
    assert receiptV2["source_blobs_after"][GAME]==origpins[GAME],"ORIGINAL_FB019_AUTHOR_DRIFT"
    assert "horde:reset(" in original[GAME].decode("utf8")
    # Guarded source-only mutation is exactly ONE existing predicate, not a
    # second damage/hit authority, heartbeat, remote, or new NPC script.
    updated={**original,GAME:patch(original[GAME])}
    assert len(updated)==81 and {p for p in original if updated[p]!=original[p]}=={GAME}
    assert updated[HORDE]==original[HORDE],"MUSOU_HORDE_AUTHORITY_MUST_NOT_CHANGE"
    pins={p:blob(s) for p,s in sorted(updated.items())}
    receipt={
       "id":FEATURE,"parent_authoritative_source_count":81,
       "original_authority_git_blob":origpins[GAME],
       "new_authority_git_blob":pins[GAME],
       "source_changed":[GAME],"other80_sources_byte_exact":True,
       "original_horde_module_byte_exact":True,"extra_remote":0,"extra_Game":0,
       "extra_horde_reset_calls":0,"server_private_session_required":True,
       "workspace_server_optin_attribute":OPT_IN,
       "public_nonstudio_effect":"OFF_WITHOUT_PRIVATE_SERVER_ID",
       "private_default":"OFF_UNLESS_EXPLICIT_SERVER_ATTRIBUTE",
       "studio_original":"UNCHANGED",
       "actual_neutral_mobs_spawn":"NOT_TESTED",
       "actual_horde_damage_popup":"NOT_TESTED",
       "real_private_pc_android":"NOT_TESTED",
       "children_3min_fun":"NOT_TESTED","fps_15min":"NOT_TESTED",
       "release_blocker_444":"NOT_RESOLVED",
       "art_decision":"ART_NO_GO","fun_decision":"FUN_NO_GO",
       "mobile_decision":"MOBILE_NO_GO","live_art_decision":"LIVE_ART_NO_GO",
       "owner_accepted":False,"public_publish_approved":False,
       "rollback":"Remove exact opt-in one-line replacement and rebuild canonical81",
    }
    sl["blobs"]=pins
    fl["source_gitblobs"]=pins
    sl["private_live_horde"]=receipt
    fl["private_live_horde"]=receipt
    fl["feature_flags"][FEATURE]=True
    tmp=Path(tempfile.mkdtemp(prefix=".p0d_private_horde_",dir=str(out.parent)))
    stage=tmp/"out"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(updated[GAME])
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==updated and read(base)==original
        os.replace(stage,out)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
    print("P0D_PRIVATE_HORDE81_GAME_ONE_PREDICATE_OTHER80_EXACT_PASS")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--enabled",choices=("true","false"),required=True)
    args=parser.parse_args()
    apply(args.base,args.out,args.enabled=="true")
