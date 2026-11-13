#!/usr/bin/env python3
"""P0D #220 owner V5: apply two source-locked fixes to ONE official RC build.

The original rich51 is pinned and assembled once as before. This overlay
changes ONLY the already present optional Studio V4 training server/UI pair.
No new Game, Store, Remote, XP grant, profile key, monetization, RC fork or
second Place. Setting ENABLED=false in ACTIVE.json reverts BOTH bytes to the
original pinned 51-source version at the very next canonical CI build.

Fail closed if frozen source or actual source-owned file bodies drift.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
REPO=ROOT.parent
PROFILE="rich51"
FEATURE="V4_IDLE_FRIEND_SAFE_FIX"
BASE_SHA="79123d35cd7afdd5f4f9941675bc2d2cf382ac4e"
AUTHOR_SHA="b7de8f8b7b4cccfb49d2d81c1ee4438d13a4b286"
PATHS={
    "server/V4TrainingBridge.server.luau":{
      "baseline":"326ec2cadbc71ef9d1d3a08e797479d1c6e08203",
      "fixed":"dbb7171add2b29e337171e547bc40101c2b0dce4",
      "overlay":ROOT/"overlays/V4TrainingBridge.server.luau"
    },
    "client/V4TrialOverlay.client.luau":{
      "baseline":"0859702fdd050e0b66a2c0672c419e5c7adb812a",
      "fixed":"7ad4ce4fa9d545cb33836c06dc56c0a03e384666",
      "overlay":ROOT/"overlays/V4TrialOverlay.client.luau"
    }
}

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def apply(dist:Path, profile:str):
    manifest=json.loads((ROOT/"ACTIVE.json").read_text("utf8"))
    active=manifest["active_profile"]
    assert active=="rich51",active
    enabled=manifest["feature_switches"][FEATURE]["enabled"]
    assert type(enabled) is bool
    assert manifest["source_profiles"][PROFILE]["source_commit"]==BASE_SHA
    assert manifest["feature_switches"][FEATURE]["rollback"]=="DISABLE_OVERLAY_RETAIN_RICH51"
    if profile!="rich51":
        print("P0D_RC_OVERLAY_SKIPPED_FALLBACK",profile)
        return False
    assert dist.is_dir()
    lockpath=dist/"SOURCE_LOCK.json"
    lock=json.loads(lockpath.read_text("utf8"))
    assert lock["total_scripts"]==51 and lock["original_47_byte_identical"]==47
    assert lock["official_rc_adopted"] is False, "source author preview lock must remain unaltered"
    actual={p.relative_to(dist/"src").as_posix():p.read_bytes()
            for p in (dist/"src").rglob("*.luau")}
    assert len(actual)==51
    assert set(actual)==set(lock["blobs"])
    assert {p:blob(raw) for p,raw in actual.items()}==lock["blobs"],"BASE_SOURCE_LOCK_DRIFT"
    assert manifest["active_source_commit"]==BASE_SHA
    for name,meta in PATHS.items():
        assert blob(actual[name])==meta["baseline"],name
        candidate=meta["overlay"].read_bytes()
        assert blob(candidate)==meta["fixed"],"FIXED_SOURCE_ORIGINAL_AUTHOR_DRIFT"
        s=candidate.decode("utf8")
        assert 'if not RunService:IsStudio() then return end' in s
        for banned in (
            "FireServer(", "OnServerEvent:Connect(", "GetDataStore(",
            "UpdateAsync(", "MarketplaceService", "VirtualUser",
            "VirtualInputManager", "PromptProductPurchase("
        ):
            assert banned not in s, (name,banned)
        if name.startswith("server"):
            assert 'player:IsFriendsWithAsync(other.UserId)' in s
            assert 'task.spawn(function()' in s
            assert 'pcall(function()' in s
            assert 'NoSavedXP' in s and 'NoCombatBuff' in s
            assert s.count('Scheduler.settle(')==1
            assert s.count('Model.apply(')==1
            assert s.count('Instance.new("RemoteEvent")')==0
        else:
            assert 'player.Idled:Connect(' in s
            assert 'UserInputService.InputBegan:Connect(' in s
            assert 'InputBegan' in s
            assert 'idleSeconds' in s
    # The base game's ONLY Game, Remote, Store and 49 non-V4 scripts are
    # already frozen byte-for-byte above. Update only one coherent pair.
    if not enabled:
        print("P0D_RC_V4_IDLE_FRIEND_FIX_OFF_ORIGINAL_51_EXACT")
        return False
    for name,meta in PATHS.items():
        (dist/"src"/name).write_bytes(meta["overlay"].read_bytes())
        lock["blobs"][name]=meta["fixed"]
    after={p.relative_to(dist/"src").as_posix():p.read_bytes()
           for p in (dist/"src").rglob("*.luau")}
    assert len(after)==51 and set(after)==set(actual)
    changed=sorted(p for p in actual if after[p]!=actual[p])
    assert changed==sorted(PATHS),changed
    assert all(after[p]==actual[p] for p in actual if p not in PATHS)
    assert {p:blob(raw) for p,raw in after.items()}==lock["blobs"]
    assert after["server/Game.server.luau"]==actual["server/Game.server.luau"]
    assert after["server/PersistentHatchStore.luau"]==actual["server/PersistentHatchStore.luau"]
    assert after["server/DojoRules.luau"]==actual["server/DojoRules.luau"]
    assert after["client/ResultNextStep.client.luau"]==actual["client/ResultNextStep.client.luau"]
    game=after["server/Game.server.luau"].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count('H2Score.deposit(')==1
    lock["rc_overlay"]={
      "id":FEATURE,
      "original51_source_commit":BASE_SHA,
      "author_fixed_source_commit":AUTHOR_SHA,
      "enabled":True,
      "only_changed_scripts":changed,
      "untouched_original_game_scripts":49,
      "rollback":"set rc_fastlane/ACTIVE.json feature_switches."+
        FEATURE+".enabled=false and rebuild same RC",
      "new_script_count":0,
      "new_remote":False,
      "durable_sixskill":False,
      "studio_2client":"NOT_TESTED",
      "android":"NOT_TESTED",
      "owner_fun":"NOT_TESTED"
    }
    lockpath.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_RC_V4_IDLE_FRIEND_FIX_51_EXACT_49_UNCHANGED_PASS")
    return True

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--profile",required=True)
    args=p.parse_args()
    apply(args.dist,args.profile)

if __name__=="__main__":
    main()
