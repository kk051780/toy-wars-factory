#!/usr/bin/env python3
"""P0D private61: actual source/project rollback chain and isolated OFF admission.

The snapshots are created from the REAL pinned game assembler in ONE CI run,
not synthetic fixtures or claims about Roblox Studio physics.
Never writes to canonical RC, main or a Roblox place.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import apply_wcs_f01_c01 as wcs
import apply_seven_jobs_pve as jobs
import apply_egg_relay_classic as relay
import apply_star_path as stars

STAGES=(57,58,59,60,61)
DIR=Path("/tmp/p0d_private61_admission_chain")
SERVER="server/Game.server.luau"
HUD="client/HUD.client.luau"
NEW={58:"server/WCS_CrystalCanyon.server.luau",
     59:"server/SevenJobsRules.luau",
     60:"server/EggRelayPolicy.luau",
     61:"server/StarfallPath.server.luau"}

def shabytes(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def files(root:Path)->dict[str,bytes]:
    return {p.relative_to(root).as_posix():p.read_bytes()
            for p in sorted(root.rglob("*")) if p.is_file()}

def source(root:Path)->dict[str,bytes]:
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def readjson(path:Path)->dict:
    return json.loads(path.read_text(encoding="utf8"))

def assert_stage(root:Path,n:int)->dict:
    assert (root/"src").is_dir() and (root/"default.project.json").is_file(), "NOT_DIST"
    ss=source(root)
    assert len(ss)==n,("STAGE_EXPECTED_SOURCE_COUNT",n,len(ss))
    assert len([p for p in ss if p==SERVER])==1,"NO_SINGLE_GAME"
    for fn in ("SOURCE_LOCK.json","RC_FEATURE_LOCK.json"):
        assert (root/fn).is_file(),("MISSING_PINNED_LOCK",fn,n)
    lock=readjson(root/"SOURCE_LOCK.json")
    f=readjson(root/"RC_FEATURE_LOCK.json")
    pins={p:wcs.git_blob(data) for p,data in sorted(ss.items())}
    assert lock["total_scripts"]==n and lock["blobs"]==pins,("SOURCE_LOCK_BAD",n)
    assert f["total_sources"]==n and f["source_gitblobs"]==pins,("FEATURE_LOCK_BAD",n)
    cfg=readjson(root/"default.project.json")["tree"]
    s=cfg.get("ServerStorage",{})
    att=s.get("$attributes",{})
    assert (att.get("P0D_RC_ENABLE_WCS_F01_C01") is True)==(n>=58),("WCS_ROJO_BOOT",n,att)
    assert (att.get("P0D_RC_ENABLE_SEVEN_JOBS_PVE") is True)==(n>=59),("JOBS_ROJO_BOOT",n)
    assert ("P0D_RC_ENABLE_EGG_RELAY_CLASSIC" in s)==(n>=60),("EGG_ROJO_BOOT",n)
    if n>=60:
        b=s["P0D_RC_ENABLE_EGG_RELAY_CLASSIC"]
        assert b["$className"]=="BoolValue" and b["$properties"]["Value"] is True
    assert (att.get("P0D_RC_ENABLE_STARRY_PATH_V1") is True)==(n>=61),("STAR_ROJO_BOOT",n)
    if n>=58:
        assert "server/WCS_CrystalCanyon.server.luau" in ss
    if n>=59:
        assert "server/SevenJobsRules.luau" in ss
    if n>=60:
        assert "server/EggRelayPolicy.luau" in ss
    if n>=61:
        assert "server/StarfallPath.server.luau" in ss
    game=ss[SERVER].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1,"DUPLICATE_REMOTE_HANDLER"
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1,"DUPLICATE_REMOTE_OWNER"
    return {"stage":n,"scripts":n,
            "script_sha256":{p:shabytes(v) for p,v in sorted(ss.items())},
            "manifest_sha256":{p:shabytes(v) for p,v in sorted(files(root).items())
                if p.startswith("src/") or p in
                ("default.project.json","SOURCE_LOCK.json","RC_FEATURE_LOCK.json")}}

def capture(n:int,root:Path):
    assert n in STAGES
    # Validate before copying anything, and refuse reuse of a previous job snapshot.
    result=assert_stage(root,n)
    DIR.mkdir(parents=True,exist_ok=True)
    dest=DIR/str(n)
    assert not dest.exists(),("SNAPSHOT_ALREADY_EXISTS",dest)
    dest.mkdir()
    shutil.copytree(root/"src",dest/"src")
    for name in ("default.project.json","SOURCE_LOCK.json","RC_FEATURE_LOCK.json"):
        shutil.copy2(root/name,dest/name)
    assert assert_stage(dest,n)["manifest_sha256"]==result["manifest_sha256"],"COPY_DRIFT"
    (DIR/(str(n)+".json")).write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("P0D_RC61_CAPTURED_REAL_STAGE",n)

def verify(receipt:Path):
    snapshots={}
    for n in STAGES:
        root=DIR/str(n)
        data=assert_stage(root,n)
        immutable=readjson(DIR/(str(n)+".json"))
        assert data==immutable,("STAGE_COPY_MUTATED",n)
        snapshots[n]=data
    summary=[]
    for lo,hi in zip(STAGES,STAGES[1:]):
        prev=snapshots[lo]["script_sha256"]
        next_=snapshots[hi]["script_sha256"]
        added=set(next_)-set(prev)
        changed={p for p in prev if next_[p]!=prev[p]}
        assert added=={NEW[hi]},("UNEXPECTED_ADDED_SCRIPT",hi,added)
        expected_changed={SERVER,HUD} if hi in (59,60) else set()
        assert changed==expected_changed,("EXISTING_SCRIPT_DRIFT",hi,changed,expected_changed)
        summary.append({"from":lo,"to":hi,"added":NEW[hi],
                        "changed_existing":sorted(changed),
                        "unchanged_existing":lo-len(changed)})
    off_list=[
        (57, "WCS_F01_C01", lambda d: wcs.apply(d,"rich51",False)),
        (58, "SEVEN_JOBS_PVE_V1", lambda d: jobs.apply(d,False)),
        (59, "EGG_RELAY_CLASSIC_V1", lambda d: relay.run(
            d,HERE/"features/egg_relay_classic/policy/EggRelayPolicy.luau",False)),
        (60, "STARRY_PATH_V1", lambda d: stars.apply(d,"rich51",False))
    ]
    for n,feature,disable in off_list:
        d=DIR/str(n)
        before=files(d)
        ans=disable(d)
        after=files(d)
        assert ans is False or ans is None or (isinstance(ans,dict) and ans.get("enabled") is False),("OFF_WRONG_RETURN",n,feature,ans)
        assert before==after,("OFF_NOT_BYTE_EXACT",n,feature)
        print("P0D_RC61_REAL_OFF_RETURNS_PREVIOUS_BYTE_EXACT_PASS",n,feature)
    assert len(snapshots[61]["script_sha256"])==61
    result={"kind":"P0D_PRIVATE61_REAL_LAYER_ADMISSION_AND_ROLLBACK",
            "verified_stages":list(STAGES),"added_features":summary,
            "actual_OFF_tests":[x[1] for x in off_list],
            "original_57_script_contents_preserved_except_original_Game_HUD":True,
            "one_Game_one_Remote_no_store_overwrites":True,
            "canonical_branch_written":False,
            "studio_engine_2client_android_fun":"NOT_TESTED"}
    receipt.parent.mkdir(parents=True,exist_ok=True)
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("P0D_RC61_FOUR_REAL_LAYER_OFF_BYTE_EXACT_AND_SOURCE_LOCK_PASS 57/58/59/60/61")

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--capture",type=int,choices=STAGES)
    p.add_argument("--dist",type=Path)
    p.add_argument("--verify",action="store_true")
    p.add_argument("--receipt",type=Path,default=Path("/tmp/p0d_rc_out/RC61_LAYER_QA_RECEIPT.json"))
    x=p.parse_args()
    if x.verify:
        assert x.capture is None
        verify(x.receipt)
    else:
        assert x.capture is not None and x.dist is not None
        capture(x.capture,x.dist)

if __name__=="__main__":
    main()
