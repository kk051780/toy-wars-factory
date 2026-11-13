#!/usr/bin/env python3
"""Compose classic egg relay onto the already integrated WCS+7Jobs private59.
Never write official RC. Exact 15 source anchors, single Game/Remote/Store.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

HERE=Path(__file__).resolve()
ROOT=HERE.parents[2]
GAME="server/Game.server.luau"
HUD="client/HUD.client.luau"
RELAY="server/EggRelayPolicy.luau"
WCS="server/WCS_CrystalCanyon.server.luau"
JOBS="server/SevenJobsRules.luau"
FLAG="EGG_RELAY_CLASSIC_V1"
POLICY_BLOB="ef9b65bd6520231f299f21c5cfe2aa250798c8d0"
OPS_BLOB="709804162da1537bdc412a7ce6563a004e5cdadf"

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def srcs(dist:Path)->dict[str,bytes]:
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes() for p in sorted(root.rglob("*.luau"))}

def apply_ops(source:str, ops:list, kind:str)->str:
    for i,entry in enumerate(ops):
        anchor=entry["anchor"]
        replacement=entry["replace"]
        assert isinstance(anchor,str) and isinstance(replacement,str)
        assert source.count(anchor)==1,("MULTI_FEATURE_GAME_HUD_ANCHOR_CONFLICT",kind,i,anchor[:90],source.count(anchor))
        # Original single-feature relay permitted nil to enable automatically.
        # In the combined candidate this must require an explicit opt-in.
        if kind=="Game" and "return flag == nil or" in replacement:
            old='return flag == nil or (flag:IsA("BoolValue") and flag.Value == true)'
            assert replacement.count(old)==1,"AUTHOR_FLAG_SOURCE_DRIFT"
            replacement=replacement.replace(old,'return flag ~= nil and (flag:IsA("BoolValue") and flag.Value == true)')
        source=source.replace(anchor,replacement,1)
    return source

def run(dist:Path,author:Path,enabled:bool)->bool:
    dist,author=dist.resolve(),author.resolve()
    before=srcs(dist)
    assert len(before)==59,("REQUIRES_WCS_JOBS59",len(before))
    assert GAME in before and HUD in before and WCS in before and JOBS in before
    assert RELAY not in before,"DUPLICATE_RELAY_POLICY"
    assert blob(before[JOBS])=="a7253d36cb67df47d4ba65d35af212ed1eb7b5b2"
    assert sum(x=="server/Game.server.luau" for x in before)==1
    flags=json.loads((ROOT/"rc_fastlane/FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    assert flags["WCS_F01_C01"]["enabled"] is True and flags["SEVEN_JOBS_PVE_V1"]["enabled"] is True
    assert type(flags[FLAG]["enabled"]) is bool
    lockpath=dist/"SOURCE_LOCK.json"; flpath=dist/"RC_FEATURE_LOCK.json"
    lockraw=lockpath.read_bytes(); flraw=flpath.read_bytes()
    lock=json.loads(lockraw); flock=json.loads(flraw)
    pins={p:blob(v) for p,v in sorted(before.items())}
    assert lock["total_scripts"]==59 and lock["blobs"]==pins, "BASE59_SOURCE_LOCK_DRIFT"
    assert flock["total_sources"]==59 and flock["source_gitblobs"]==pins, "BASE59_FEATURE_LOCK_DRIFT"
    assert flock["feature_flags"]["SEVEN_JOBS_PVE_V1"] is True
    assert FLAG not in flock["feature_flags"]
    if not enabled or not flags[FLAG]["enabled"]:
        assert srcs(dist)==before and lockpath.read_bytes()==lockraw and flpath.read_bytes()==flraw
        print("P0D_TRIPLE_RELAY_OFF_RESTORES_WCS_JOBS59_BYTE_EXACT_PASS")
        return False
    specpath=author/"PATCH_OPS.json"
    policy=author.parent/"P0D-EGG-RELAY-PASS-POLICY-20261113-01/src/EggRelayPolicy.luau"
    assert blob(specpath.read_bytes())==OPS_BLOB,"RELAY_AUTHOR_PATCH_DRIFT"
    spec=json.loads(specpath.read_text("utf8"))
    assert spec["feature_id"]==FLAG and spec["rc_integrated"] is False
    assert len(spec["game_ops"])==9 and len(spec["hud_ops"])==6
    raw_policy=policy.read_bytes()
    assert blob(raw_policy)==POLICY_BLOB,"RELAY_POLICY_DRIFT"
    game=before[GAME].decode("utf8")
    hud=before[HUD].decode("utf8")
    assert "SevenJobsRules" in game and "ScoutSpeciesPolicy" in game
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count("applyClassicEggRelay(")==0
    assert hud.count("local seq = 0")==1
    game2=apply_ops(game,spec["game_ops"],"Game")
    hud2=apply_ops(hud,spec["hud_ops"],"HUD")
    assert game2.count("remote.OnServerEvent:Connect(")==1
    assert game2.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game2.count("match.eggOwners[egg]=target")==1
    assert game2.count("carry[target]=egg")==1
    assert game2.count("H2Score.deposit(")==game.count("H2Score.deposit(")
    assert game2.count("match.scores[team] += 1")==game.count("match.scores[team] += 1")
    assert 'return flag ~= nil and (flag:IsA("BoolValue") and flag.Value == true)' in game2
    assert "or EXPERIMENTAL_FIVE_EGG_MODE" in game2,"FIVE_EGG_MUST_BE_OFF"
    assert hud2.count("relayButton.MouseButton1Click:Connect(fireClassicEggRelay)")==1
    assert hud2.count("local seq = 0")==1
    after=dict(before);after[GAME]=game2.encode("utf8");after[HUD]=hud2.encode("utf8");after[RELAY]=raw_policy
    assert len(after)==60
    assert set(after)-set(before)=={RELAY}
    assert {p for p in before if before[p]!=after[p]}=={GAME,HUD}
    assert all(after[p]==before[p] for p in before if p not in (GAME,HUD))
    assert after["server/PersistentHatchStore.luau"]==before["server/PersistentHatchStore.luau"]
    pins2={p:blob(v) for p,v in sorted(after.items())}
    lock["total_scripts"]=60;lock["blobs"]=pins2
    lock["rc_relay_classic_combo_overlay"]={
        "id":FLAG,"source_pin":POLICY_BLOB,"author_ops_pin":OPS_BLOB,
        "previous_59_sources_preserved_except":["server/Game.server.luau","client/HUD.client.luau"],
        "one_original_game_remote_store":True,"studio_runtime_explicit_BoolValue_true_only":True,
        "mode":"ONE_EGG_ONLY","stage":"PRIVATE_SOURCE_CANDIDATE_NOT_OFFICIAL",
        "rollback":"disable EGG_RELAY_CLASSIC_V1 then rebuild source59"}
    flock["total_sources"]=60;flock["source_gitblobs"]=pins2
    flock["feature_flags"][FLAG]=True
    originals={p:before[p] for p in (GAME,HUD)}
    try:
        for p in (GAME,HUD,RELAY):
            target=dist/"src"/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(after[p])
        lockpath.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
        flpath.write_text(json.dumps(flock,ensure_ascii=False,indent=2)+"\n","utf8")
        assert srcs(dist)==after
        print("P0D_WCS_JOBS_RELAY_PRIVATE60_ONE_GAME_SOURCE_LOCK_PASS")
        return True
    except BaseException:
        for p,v in originals.items(): (dist/"src"/p).write_bytes(v)
        if (dist/"src"/RELAY).exists(): (dist/"src"/RELAY).unlink()
        lockpath.write_bytes(lockraw);flpath.write_bytes(flraw)
        assert srcs(dist)==before,"ROLLBACK_SOURCE_MISMATCH"
        raise

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--dist",type=Path,required=True)
    cli.add_argument("--author",type=Path,required=True)
    cli.add_argument("--off-test",action="store_true")
    a=cli.parse_args()
    run(a.dist,a.author,not a.off_test)
