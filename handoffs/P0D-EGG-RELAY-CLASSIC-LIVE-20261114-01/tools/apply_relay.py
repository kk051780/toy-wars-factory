#!/usr/bin/env python3
"""Apply source-locked Egg Relay classic-only patch to a prepared UNPUBLISHED RC dist.
Author candidate ONLY. #220 sole official RC integrator owns any adoption.
Usage: python3 tools/apply_relay.py --dist PATH --policy PATH
Run AFTER other original canonical overlays, never on main / live Place.
"""
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\\0"+data).hexdigest()
def patch(data,ops):
    for index,entry in enumerate(ops):
        anchor=entry["anchor"]
        assert data.count(anchor)==1,("ANCHOR_DRIFT",index,anchor[:100])
        data=data.replace(anchor,entry["replace"],1)
    return data
def run(dist,policy):
    spec=json.loads((ROOT/"PATCH_OPS.json").read_text(encoding="utf8"))
    assert spec["feature_id"]=="EGG_RELAY_CLASSIC_V1"
    assert spec["rc_integrated"] is False
    assert spec["real_studio"]=="NOT_TESTED"
    raw=policy.read_bytes()
    assert blob(raw)==spec["source_policy_gitblob"],"POLICY_DRIFT"
    src=dist/"src"
    game=src/"server/Game.server.luau"
    hud=src/"client/HUD.client.luau"
    mod=src/"server/EggRelayPolicy.luau"
    assert not mod.exists(),"NO_SECOND_MODULE_OR_DOUBLE_PATCH"
    beforeGame=game.read_text(encoding="utf8")
    beforeHud=hud.read_text(encoding="utf8")
    assert beforeGame.count("remote.OnServerEvent:Connect(")==1
    assert beforeGame.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert beforeHud.count("local seq = 0")==1
    assert "local function applyClassicEggRelay" not in beforeGame
    afterGame=patch(beforeGame,spec["game_ops"])
    afterHud=patch(beforeHud,spec["hud_ops"])
    assert afterGame.count("remote.OnServerEvent:Connect(")==1
    assert afterGame.count("H2Score.deposit(")==beforeGame.count("H2Score.deposit(")
    assert afterGame.count("match.scores[team] += 1")==beforeGame.count("match.scores[team] += 1")
    assert afterHud.count("local seq = 0")==1
    assert 'EGG_RELAY' in afterGame and 'EGG_RELAY' in afterHud
    game.write_text(afterGame,encoding="utf8")
    hud.write_text(afterHud,encoding="utf8")
    mod.write_bytes(raw)
    lockFile=dist/"SOURCE_LOCK.json"
    if lockFile.exists():
        lock=json.loads(lockFile.read_text("utf8"))
        lock["blobs"]={p.relative_to(src).as_posix():blob(p.read_bytes())
            for p in sorted(src.rglob("*.luau"))}
        lock["total_scripts"]=len(lock["blobs"])
        lock["relay_classic_preview"]={"feature_id":"EGG_RELAY_CLASSIC_V1",
            "stage":"SOURCE_CANDIDATE_NOT_OFFICIAL_RC",
            "5_egg":"NOT_SUPPORTED","real_studio":"NOT_TESTED",
            "rollback":"omit this patch and rebuild same base"}
        lockFile.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\\n","utf8")
    print("CLASSIC_EGG_RELAY_PATCH_SOURCE_APPLIED_3_FILES_NOT_STUDIO")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--policy",type=Path,required=True)
    a=p.parse_args()
    run(a.dist,a.policy)
