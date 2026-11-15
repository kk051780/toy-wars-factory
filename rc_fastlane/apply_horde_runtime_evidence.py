#!/usr/bin/env python3
"""#444 minimal private read-only runtime witness, source-locked to B official V2.

Only ADD one server diagnostic script to original 81 unchanged, OFF zero-write.
Private Roblox physical test requires owner opt-in later; CI is source-only.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
AUTHOR=Path(__file__).resolve().parent/"features/live_art/P0DPrivateHordeEvidence.server.luau"
AUTHOR_BLOB="233e19afd4a91f5e0e037148bcc7f4d56fa55d2f"
DEST="server/P0DPrivateHordeEvidence.server.luau"
GAME="server/Game.server.luau"
HORDE="server/MusouHorde.luau"
FEATURE="P0D_PRIVATE_HORDE_ENGINE_EVIDENCE_V1"
BASE_OFFICIAL="bf3e2ae7ff8ab7f5e6e5af6d139f0b0f62483df2"
GAME_BLOB="6533f2b3ec106141508e70027f7dc9844c8cbcb0"
HORDE_BLOB="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def read(root:Path)->dict[str,bytes]:
    assert root.is_dir() and not root.is_symlink(),"INVALID_BASE"
    for p in root.rglob("*"):
        assert not p.is_symlink() and p.resolve().is_relative_to(root.resolve()),("SYMLINK",str(p))
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}
def verify_author(raw:bytes)->None:
    assert blob(raw)==AUTHOR_BLOB,("AUTHOR_NOT_PINNED",blob(raw))
    s=raw.decode("utf8")
    for must in (
        "if not RunService:IsServer() then return end",
        'if not RunService:IsStudio() and game.PrivateServerId == "" then return end',
        'workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") ~= true',
        'workspace:GetAttribute("P0D_PRIVATE_HORDE_EVIDENCE") ~= true',
        'workspace:WaitForChild("TRAP_RAIDERS_S1", 45)',
        '"EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT"',
        '"MUSOU_ELITE_TELEGRAPH"',
        '"MUSOU_MINION_"',
        '"RealDamagePopup"',
        '"CHECKPOINT"',
        "local MAX_SAMPLES = 360",
        "local MAX_MOBS = 9",
        "sample % 60 == 0",
        "liveCombatQualityApproved = false",
        "ownerAccepted = false",
    ):
        assert must in s,("MISSING_PRIVATE_RUNTIME_SAFETY",must)
    for bad in (
        "FireServer(", "OnServerEvent", "FireClient(", "RemoteEvent",
        "GetDataStore(", "SetAttribute(", "CanCollide = true",
        "Humanoid:TakeDamage(", "Instance.new(", "HttpService:PostAsync",
        "TweenService", "RunService.Heartbeat:Connect", "task.spawn(",
        "HttpService:RequestAsync"
    ):
        assert bad not in s,("PROBE_MUST_NOT_MUTATE_GAME",bad)
    assert s.count("task.wait(SAMPLE_SECONDS)")==1
    assert s.count("HttpService:JSONEncode(data)")==1
def apply(base:Path,out:Path,enabled:bool)->bool:
    assert not out.exists(),"OUTPUT_EXISTS"
    if not enabled:
        print("P0D_PRIVATE_HORDE_EVIDENCE_OFF_ZERO_WRITE");return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==81 and DEST not in before
    assert blob(before[GAME])==GAME_BLOB,("PARENT_GAME_V2_DRIFT",blob(before[GAME]))
    assert blob(before[HORDE])==HORDE_BLOB
    assert b"privateHordeTrialAllowed()" in before[GAME] and b"musouHitFeedback" in before[GAME]
    assert b"impactDisplayEpoch" in before["client/HUD.client.luau"]
    pins={path:blob(data) for path,data in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pj=json.loads((base/"default.project.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==81
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert pj["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    for flag in ("P0D_PRIVATE_LIVE_HORDE_NINE_V1",
                 "P0D_PRIVATE_LIVE_HORDE_ATTACK_TICK_V2",
                 "FB015_LIVE_CASTLE_SAFE_PARITY_V1",
                 "P0D_PRIVATE_ONE_HUMAN_HORDE_READY_TRIAL_V1",
                 "P0D_PRIVATE_LIVE_HORDE_HIT_TOAST_V3",
                 "FB015_LIVE_ART_PRIVATE_CLIENT_PILOT_V1"):
        assert fl["feature_flags"].get(flag) is True,("REQUIRED_PARENT_FLAG",flag)
    assert FEATURE not in fl["feature_flags"]
    raw=AUTHOR.read_bytes();verify_author(raw)
    after={**before,DEST:raw}
    assert len(after)==82 and all(after[k]==v for k,v in before.items())
    newpins={path:blob(data) for path,data in sorted(after.items())}
    receipt={
        "schema":"P0D_HORDE_PRIVATE_RUNTIME_WITNESS_A_PREP_V1",
        "original_rc_head":BASE_OFFICIAL,
        "feature_id":FEATURE,"issue":"#444",
        "stage":"B_220_RC81_CUMULATIVE_PRIVATE_82_SOURCE_ONLY",
        "old_script_count":81,"new_script_count":82,
        "old81_byte_identical":True,
        "preserves_private_onehuman_real_hit_art_source_exact":True,
        "new_script":DEST,"author_gitblob":AUTHOR_BLOB,
        "gameplay_authority_changed":False,"new_remotes":0,
        "new_ui":0,"new_damage":0,"new_world_parts":0,
        "owner_private_optin_required":True,"public_hard_block":True,
        "log_pii":False,"bounded_samples":360,
        "must_observe":["9 actual models","server popup enabled on hit",
                        "motion evidence","KO popup"],
        "real_roblox_runtime":"NOT_TESTED",
        "formal_rc_source_staged":True,
        "low_end_android_15min":"NOT_TESTED",
        "owner_accepted":False,"official_rc_adopted":False,
        "live_horde_gate":"LIVE_HORDE_NO_GO",
        "art_gate":"ART_NO_GO","mobile_gate":"MOBILE_NO_GO","fun_gate":"FUN_NO_GO",
        "rollback":"disable by omitting only new diagnostic Script, old 81 bytes unchanged"
    }
    sl["total_scripts"]=82;fl["total_sources"]=82
    sl["blobs"]=newpins;fl["source_gitblobs"]=newpins
    sl["horde_runtime_probe_v1"]=fl["horde_runtime_probe_v1"]=receipt
    fl["feature_flags"][FEATURE]=True
    tmp=Path(tempfile.mkdtemp(prefix=".p0d_horde_evidence_",dir=str(out.parent)))
    stage=tmp/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/DEST).write_bytes(raw)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after and read(base)==before
        os.replace(stage,out)
    finally: shutil.rmtree(tmp,ignore_errors=True)
    print("P0D_PRIVATE_HORDE_EVIDENCE_82_SOURCE_OLD81_BYTE_EXACT")
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
