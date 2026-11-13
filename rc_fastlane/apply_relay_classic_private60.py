#!/usr/bin/env python3
"""Source-locked additive CLASSIC 1-egg relay on tested WCS + SevenJobs rich59.

Private source candidate only. NEVER writes the official RC or main.
The original PR296 policy and patch manifest are *not modified*. Run this only
after the original RC57, WCS, SevenJobs 59 pipeline and before native Luau/Rojo.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUTHOR = ROOT / "_egg" / "handoffs" / "P0D-EGG-RELAY-CLASSIC-LIVE-20261114-01"
ORIGINAL_POLICY = ROOT / "_egg" / "handoffs" / "P0D-EGG-RELAY-PASS-POLICY-20261113-01" / "src" / "EggRelayPolicy.luau"
FEATURE = "EGG_RELAY_CLASSIC_V1"
GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
POLICY = "server/EggRelayPolicy.luau"
WCS = "server/WCS_CrystalCanyon.server.luau"
JOBS = "server/SevenJobsRules.luau"

def blob(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+bytes([0])+b).hexdigest()

def read_inventory(dist:Path)->dict[str,bytes]:
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes() for p in sorted(root.rglob("*.luau"))}

def checked_locks(dist:Path, before:dict[str,bytes], expected:int)->tuple[dict,dict]:
    assert len(before)==expected,("EXPECTED_COMBINED59_SOURCE",len(before),expected)
    pins={k:blob(v) for k,v in before.items()}
    lock=json.loads((dist/"SOURCE_LOCK.json").read_text("utf8"))
    receipt=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert lock["total_scripts"]==expected and lock["blobs"]==pins,"SOURCE_LOCK_CHANGED"
    assert receipt["total_sources"]==expected and receipt["source_gitblobs"]==pins,"FEATURE_LOCK_CHANGED"
    return lock,receipt

def patch(text:str,ops:list[dict],label:str)->str:
    for i,op in enumerate(ops):
        original=op["anchor"]
        replacement=op["replace"]
        assert isinstance(original,str) and isinstance(replacement,str) and original
        assert text.count(original)==1,("EXACT_ANCHOR_COLLISION",label,i,text.count(original),original[:140])
        text=text.replace(original,replacement,1)
    return text

def run(dist:Path,enabled:bool)->dict:
    before=read_inventory(dist)
    lock,receipt=checked_locks(dist,before,59)
    for key in (GAME,HUD,WCS,JOBS,"server/PersistentHatchStore.luau","server/SavedBeastEvolutionPolicy.luau",
                "server/SavedPveMasteryPolicy.luau","server/ScoutSpeciesPolicy.luau"):
        assert key in before,("REQUIRED_COMBINED_GAME_MODULE_MISSING",key)
    assert POLICY not in before and FEATURE not in receipt.get("feature_flags",{}),"DUPLICATE_RELAY"
    assert receipt["feature_flags"]["WCS_F01_C01"] is True
    assert receipt["feature_flags"]["SEVEN_JOBS_PVE_V1"] is True
    game=before[GAME].decode("utf8")
    hud=before[HUD].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert "SevenJobsRules" in game and 'P0D_RC_ENABLE_SEVEN_JOBS_PVE' in game
    assert 'action("JOB_SKILL",nil)' in hud and 'action("JOB_PICK",entry[1])' in hud
    assert "local function applyClassicEggRelay" not in game
    if not enabled:
        print("P0D_EGG_RELAY_OFF_RETURNS_EXACT_WCS_SEVENJOBS59")
        return {"enabled":False,"count":59}
    spec=json.loads((AUTHOR/"PATCH_OPS.json").read_text("utf8"))
    assert spec["feature_id"]==FEATURE
    assert len(spec["game_ops"])==9 and len(spec["hud_ops"])==6
    assert spec["rc_integrated"] is False
    policy=ORIGINAL_POLICY.read_bytes()
    assert blob(policy)==spec["source_policy_gitblob"]=="ef9b65bd6520231f299f21c5cfe2aa250798c8d0"
    newgame=patch(game,spec["game_ops"],"Game")
    newhud=patch(hud,spec["hud_ops"],"HUD")
    assert newgame.count('remote.OnServerEvent:Connect(')==1
    assert newgame.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert newgame.count("H2Score.deposit(")==game.count("H2Score.deposit(")
    assert newgame.count("match.scores[team] += 1")==game.count("match.scores[team] += 1")
    assert newgame.count("match.eggOwners[egg]=target")==1
    assert newgame.count("carry[target]=egg")==1
    assert newgame.count("local now = os.clock()")==1
    assert newhud.count("relayButton.MouseButton1Click:Connect(fireClassicEggRelay)")==1
    assert newhud.count("KeyCode.H")==1
    assert newhud.count("local seq = 0")==1
    assert "SevenJobsRules" in newgame and "SevenJobsRules" in game
    assert newgame.count("P0D_RC_ENABLE_SEVEN_JOBS_PVE")==game.count("P0D_RC_ENABLE_SEVEN_JOBS_PVE")
    assert newhud.count('action("JOB_SKILL",nil)')==hud.count('action("JOB_SKILL",nil)')
    assert newhud.count('action("JOB_PICK",entry[1])')==hud.count('action("JOB_PICK",entry[1])')
    assert newgame.count("ScoutSpecies.attack(")==game.count("ScoutSpecies.attack(")
    assert "EXPERIMENTAL_FIVE_EGG_MODE" in newgame
    after=dict(before)
    after[GAME]=newgame.encode("utf8")
    after[HUD]=newhud.encode("utf8")
    after[POLICY]=policy
    assert len(after)==60
    assert sorted(set(after)-set(before))==[POLICY]
    assert sorted(k for k in before if after[k]!=before[k])==[HUD,GAME]
    assert all(after[k]==v for k,v in before.items() if k not in (HUD,GAME))
    pins={key:blob(value) for key,value in sorted(after.items())}
    lock["total_scripts"]=60
    lock["blobs"]=pins
    lock["rc_classic_relay_private60"]={
        "feature":FEATURE,"stage":"ISOLATED_PRIVATE_SOURCE_NOT_CANONICAL",
        "preserved_wcs_and_seven_jobs":True,
        "changed_existing":[GAME,HUD],"new_original":[POLICY],
        "five_egg_mode":"UNSUPPORTED",
        "Studio_engine":"NOT_TESTED",
        "rollback":"omit this overlay and retain byte-identical WCS+7Jobs59"}
    receipt["total_sources"]=60
    receipt["source_gitblobs"]=pins
    receipt.setdefault("feature_flags",{})[FEATURE]=True
    receipt["relay_stage"]="ISOLATED_PRIVATE60_NOT_RC"
    # Validate all content and lock updates before touching the source tree.
    (dist/"src"/GAME).write_bytes(after[GAME])
    (dist/"src"/HUD).write_bytes(after[HUD])
    (dist/"src"/POLICY).write_bytes(policy)
    (dist/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    (dist/"RC_FEATURE_LOCK.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
    assert read_inventory(dist)==after
    print("P0D_WCS_JOBS_EGG_RELAY_REAL59_TO_60_SOURCE_LOCK_PASS")
    return {"enabled":True,"count":60,"existing_changed":[GAME,HUD],
            "new":POLICY,"previous59_untouched_except_game_hud":True}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--enabled",choices=("on","off"),required=True)
    args=p.parse_args()
    run(args.dist,args.enabled=="on")
