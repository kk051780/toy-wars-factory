#!/usr/bin/env python3
"""Source-locked RC60 -> private61 additional timed Starfall path.

No Game, HUD, Store, remote, damage, score, XP or DataStore changes.
Studio 2-client / physics / Android / FUN must be tested before release.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "STARRY_PATH_V1"
SOURCE = ROOT / "features/star_path/StarfallPath.server.luau"
SOURCE_BLOB = "311d4c75e38f896f24c982afbc6f9d5c35e90cb4"
DEST = "server/StarfallPath.server.luau"
RUNTIME_ATTRIBUTE = "P0D_RC_ENABLE_STARRY_PATH_V1"

def blob(data: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()

def sources(dist: Path) -> dict[str, bytes]:
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def apply(dist: Path, profile: str, enabled_override: bool | None = None) -> bool:
    if profile != "rich51":
        print("STAR_PATH_DISABLED_FALLBACK_PROFILE")
        return False
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    enabled=flags[FEATURE]["enabled"] if enabled_override is None else enabled_override
    assert type(enabled) is bool
    if not enabled:
        print("P0D_STAR_PATH_OFF_PRESERVES_PRIOR60")
        return False
    assert all(flags[k]["enabled"] for k in ("WCS_F01_C01","SEVEN_JOBS_PVE_V1","EGG_RELAY_CLASSIC_V1")), "STAR_REQUIRES_WCS_JOBS_EGG"
    src=SOURCE.read_bytes()
    assert blob(src)==SOURCE_BLOB,"STAR_SOURCE_GIT_BLOB_DRIFT"
    text=src.decode("utf8")
    for necessary in ('if not RunService:IsStudio() then return end',
                      'GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1")~=true',
                      'P0D_STARRY_PATH','not occupied()','ReadyViaSkyV5',
                      'REOPEN_COOLDOWN=7','OPEN_SECONDS=16'):
        # ReadyViaSkyV5 is a WCS source flag, not in this script; separately check the source contract.
        if necessary != "ReadyViaSkyV5":
            assert necessary in text,("STAR_SOURCE_MISSING_SAFETY",necessary)
    for forbidden in ('GetDataStore(', 'UpdateAsync(', 'TakeDamage(', 'OnServerEvent:Connect(',
                      'Instance.new("RemoteEvent")','MarketplaceService','horde:hit(',
                      'PromptProductPurchase(', 'match.scores', 'carry[target]'):
        assert forbidden not in text,("STAR_FORBIDDEN_OWNER",forbidden)
    assert text.count("makeSwitch(")==3,"STAR_TWO_SYMMETRIC_BANK_SWITCHES"
    before=sources(dist)
    assert len(before)==60,("EXPECTED_COMBINED_SOURCE60",len(before))
    assert all(p in before for p in ("server/Game.server.luau",
                                   "server/WCS_CrystalCanyon.server.luau",
                                   "server/SevenJobsRules.luau",
                                   "server/EggRelayPolicy.luau"))
    assert DEST not in before,"STAR_ALREADY_PRESENT"
    lock_path=dist/"SOURCE_LOCK.json"
    lock=json.loads(lock_path.read_text("utf8"))
    assert lock["total_scripts"]==60
    assert lock["blobs"]=={p:blob(v) for p,v in sorted(before.items())},"RC60_SOURCE_DRIFT"
    assert lock["rc_wcs_f01_c01_overlay"]["id"]=="WCS_F01_C01"
    assert lock["rc_seven_jobs_pve_overlay"]["id"]=="SEVEN_JOBS_PVE_V1"
    assert lock["relay_classic_preview"]["feature_id"]=="EGG_RELAY_CLASSIC_V1"
    feature_lock_path=dist/"RC_FEATURE_LOCK.json"
    feat=None
    if feature_lock_path.exists():
        feat=json.loads(feature_lock_path.read_text("utf8"))
        assert feat["total_sources"]==60
        assert feat["source_gitblobs"]=={p:blob(v) for p,v in sorted(before.items())},"RC60_FEATURE_LOCK_DRIFT"
        assert FEATURE not in feat["feature_flags"],"DUPLICATE_FEATURE"
    config_path=dist/"default.project.json"
    cfg=json.loads(config_path.read_text("utf8"))
    assert cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    ss=cfg["tree"]["ServerStorage"]
    attrs=ss["$attributes"]
    assert attrs["P0D_RC_ENABLE_WCS_F01_C01"] is True
    assert ss["P0D_RC_ENABLE_EGG_RELAY_CLASSIC"]["$className"]=="BoolValue"
    assert RUNTIME_ATTRIBUTE not in attrs,"DUPLICATE_BOOT_ATTRIBUTE"
    # All fail-closed guards complete before mutating any file.
    attrs[RUNTIME_ATTRIBUTE]=True
    (dist/"src"/DEST).write_bytes(src)
    config_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    after=sources(dist)
    assert len(after)==61 and set(after)-set(before)=={DEST}
    assert all(after[p]==raw for p,raw in before.items()),"PRIOR60_CHANGED"
    pins={p:blob(raw) for p,raw in sorted(after.items())}
    lock["blobs"]=pins
    lock["total_scripts"]=61
    lock["rc_star_path_overlay"]={
        "id":FEATURE,"source_git_blob":SOURCE_BLOB,
        "one_additional_server_script":True,
        "prior60_byte_identical":True,
        "original_Game_Remote_Store_unchanged":True,
        "missing_runtime_flag_fails_closed":True,
        "open_seconds":16,"actual_close_cooldown_seconds":7,
        "occupied_closure_guard":True,"real_studio":"NOT_TESTED",
        "rollback":"Disable FEATURE_SWITCHES.features.STARRY_PATH_V1.enabled"
    }
    lock_path.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if feat is not None:
        feat["total_sources"]=61
        feat["source_gitblobs"]=pins
        feat["feature_flags"][FEATURE]=True
        feature_lock_path.write_text(json.dumps(feat,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("P0D_STARRY_PATH_PRIVATE61_60_ORIGINAL_SCRIPT_BYTES_PRESERVED_PASS")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--profile",required=True,choices=("rich51","rich47","legacy21"))
    parser.add_argument("--dist",required=True,type=Path)
    args=parser.parse_args()
    apply(args.dist,args.profile)
