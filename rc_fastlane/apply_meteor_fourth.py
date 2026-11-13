#!/usr/bin/env python3
"""Isolated source-locked PRIVATE61 (Starfall) -> PRIVATE62 (Meteor fourth lane).
This script MUST NOT be applied by an unapproved author to official RC.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FEATURE="METEOR_FOURTH_V1"
ORIGINAL=ROOT/"features/meteor_fourth/MeteorFourth.server.luau"
PIN="8a7ff2d33f801660f808cf9297e9d829ced39806"
DEST="server/MeteorFourth.server.luau"
FLAG="P0D_ENABLE_METEOR_SHORTCUT_V1"

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def sources(dist:Path)->dict[str,bytes]:
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def apply(dist:Path,profile:str,enabled_override:bool|None=None)->bool:
    if profile!="rich51":
        print("P0D_METEOR_FOURTH_FALLBACK_PROFILE_OFF")
        return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    enabled=flags[FEATURE]["enabled"] if enabled_override is None else enabled_override
    assert type(enabled) is bool
    if not enabled:
        print("P0D_METEOR_FOURTH_OFF_ZERO_WRITES_PRIVATE61_PASS")
        return False
    assert all(flags[k]["enabled"] for k in
               ("WCS_F01_C01","SEVEN_JOBS_PVE_V1","EGG_RELAY_CLASSIC_V1","STARRY_PATH_V1")), "DEPENDENCY_OFF"

    before=sources(dist)
    assert len(before)==61,("EXACT_PRIVATE61_REQUIRED",len(before))
    for k in ("server/Game.server.luau","server/WCS_CrystalCanyon.server.luau",
              "server/SevenJobsRules.luau","server/EggRelayPolicy.luau",
              "server/StarfallPath.server.luau"):
        assert k in before,("MISSING_PARENT_61_SCRIPT",k)
    assert DEST not in before,"DUPLICATE_METEOR_SCRIPT"
    assert before["server/Game.server.luau"].count(b'remote.OnServerEvent:Connect(')==1
    assert before["server/StarfallPath.server.luau"].count(b'Vector3.new(x,-0.75,-35)')==1
    lockfile=dist/"SOURCE_LOCK.json"
    lock=json.loads(lockfile.read_text("utf8"))
    pins={k:blob(v) for k,v in sorted(before.items())}
    assert lock["total_scripts"]==61 and lock["blobs"]==pins,"SOURCE61_LOCK_DRIFT"
    assert lock["rc_star_path_overlay"]["id"]=="STARRY_PATH_V1"

    cf=dist/"default.project.json"
    cfg=json.loads(cf.read_text("utf8"))
    assert cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    ss=cfg["tree"]["ServerStorage"]
    attrs=ss["$attributes"]
    assert attrs["P0D_RC_ENABLE_WCS_F01_C01"] is True
    assert attrs["P0D_RC_ENABLE_STARRY_PATH_V1"] is True
    assert ss["P0D_RC_ENABLE_EGG_RELAY_CLASSIC"]["$properties"]["Value"] is True
    assert FLAG not in ss, "METEOR_BOOT_VALUE_ALREADY_EXISTS"

    receiptfile=dist/"RC_FEATURE_LOCK.json"
    receipt=None
    if receiptfile.exists():
        receipt=json.loads(receiptfile.read_text("utf8"))
        assert receipt["total_sources"]==61
        assert receipt["source_gitblobs"]==pins,"FEATURE61_LOCK_DRIFT"
        assert FEATURE not in receipt["feature_flags"]

    raw=ORIGINAL.read_bytes()
    assert blob(raw)==PIN, "AUTHOR_METEOR_SOURCE_DRIFT"
    t=raw.decode("utf8")
    for expected in (
        "if not RunService:IsStudio() then",
        'flag ~= nil and flag:IsA("BoolValue") and flag.Value == true',
        'GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1") ~= true',
        'Workspace:WaitForChild("P0D_STARRY_PATH", 30)',
        'star:FindFirstChild("StarStep_01")',
        'local z = (west.Position.Z + east.Position.Z) * 0.5 - 17',
        'return math.abs(z-existing.Position.Z) > (width+existing.Size.Z)*0.5+buffer',
        'local function isBridgeOccupied(segments: {BasePart}): boolean',
        'while runtime.Parent ~= nil and isBridgeOccupied(segments) do',
    ):
        assert expected in t,("METEOR_FOURTH_SECURITY_ANCHOR_MISSING",expected)
    for forbidden in ("DataStoreService","UpdateAsync(","MarketplaceService",
                      'Instance.new("RemoteEvent")','OnServerEvent:Connect(',
                      "FireServer(","TakeDamage(","PromptProductPurchase("):
        assert forbidden not in t,("METEOR_FORBIDDEN_AUTHORITY",forbidden)

    after=dict(before);after[DEST]=raw
    assert len(after)==62 and all(after[k]==v for k,v in before.items())
    new_pins={k:blob(v) for k,v in sorted(after.items())}
    lock["blobs"]=new_pins
    lock["total_scripts"]=62
    lock["rc_meteor_fourth_overlay"]={
        "id":FEATURE,"source_git_blob":PIN,
        "source_count_parent_byte_exact":61,
        "starfall_route_already_present":True,
        "new_meteor_lane_local_z":-17,"starfall_lane_local_z":-35,
        "min_clearance_studs":3,"one_game_remote_store":True,
        "runtime_scope":"STUDIO_ONLY_EXPLICIT_TRUE_BOOLVALUE",
        "real_studio_2client":"NOT_TESTED",
        "rollback":"false restores exact parent PRIVATE61 no writes",
        "official_rc_adopted":False,
    }
    ss[FLAG]={"$className":"BoolValue","$properties":{"Value":True}}
    if receipt is not None:
        receipt["total_sources"]=62
        receipt["source_gitblobs"]=new_pins
        receipt["feature_flags"][FEATURE]=True
        receipt["meteor_fourth_lane_stage"]="PRIVATE_SOURCE_NOT_CANONICAL"

    # All inputs checked before any file mutation.
    (dist/"src"/DEST).write_bytes(raw)
    cf.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n","utf8")
    lockfile.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    if receipt is not None:
        receiptfile.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
    assert sources(dist)==after,"GAME_SOURCE_CHANGED"
    print("P0D_PRIVATE62_STAR_METEOR_FOURTH_SRC_EXACT_PASS 62")
    return True

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--profile",default="rich51",choices=("rich51","rich47","legacy21"))
    cli.add_argument("--dist",type=Path,required=True)
    cli.add_argument("--enabled",choices=("true","false"),default="true")
    args=cli.parse_args()
    apply(args.dist,args.profile,args.enabled=="true")
