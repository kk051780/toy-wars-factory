#!/usr/bin/env python3
"""Compose 1-egg classic relay after the source-exact WCS+7jobs private59 build.

This is a source-only candidate for the sole #220 RC integrator, NOT a
canonical RC or public/game-published change. Never creates a second Game.
All guards are evaluated before modifications to the scratch distribution.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

GAME="server/Game.server.luau"
HUD="client/HUD.client.luau"
POLICY="server/EggRelayPolicy.luau"
WCS="server/WCS_CrystalCanyon.server.luau"
JOBS="server/SevenJobsRules.luau"
EGG_ID="EGG_RELAY_CLASSIC_V1"
WCS_PIN="7d2afad5e9b8df410ea0eb83ad962cf42ab98e71"
JOBS_PIN="a7253d36cb67df47d4ba65d35af212ed1eb7b5b2"
BASE_DIR=Path(__file__).resolve().parents[2]
PATCHER_GITBLOB="80f1cbb0edcc80264ebeb0c8509628ae7949904c"
PATCH_OPS_GITBLOB="709804162da1537bdc412a7ce6563a004e5cdadf"

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def sources(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def patch_text(original: str, operations: list[dict]) -> str:
    result=original
    for i,op in enumerate(operations):
        anchor=op["anchor"]
        replacement=op["replace"]
        assert isinstance(anchor,str) and isinstance(replacement,str) and anchor,("PATCH_TYPE",i)
        assert result.count(anchor)==1,("PATCH_ANCHOR_DRIFT",i,anchor[:90])
        result=result.replace(anchor,replacement,1)
    return result

def run(dist: Path, author: Path, policy_source: Path, enabled: bool=True) -> bool:
    dist,author,policy_source=dist.resolve(),author.resolve(),policy_source.resolve()
    root=dist/"src"
    before=sources(root)
    assert len(before)==59,("NEED_COMBINED59",len(before))
    assert GAME in before and HUD in before and WCS in before and JOBS in before and POLICY not in before
    assert git_blob(before[WCS])==WCS_PIN and git_blob(before[JOBS])==JOBS_PIN, "WCS_OR_JOBS_DRIFT"
    game=before[GAME].decode("utf8")
    hud=before[HUD].decode("utf8")
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert 'GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")' in game
    assert "ScoutSpeciesPolicy" in game and "SavedPvePolicy.mergeWithEarned(" in game
    assert "local function applyClassicEggRelay" not in game
    assert "local seq = 0" in hud and "JOB_PICK" in hud and "JOB_SKILL" in hud
    original_lock=dist/"SOURCE_LOCK.json"
    feature_lock=dist/"RC_FEATURE_LOCK.json"
    lock_raw=original_lock.read_bytes()
    fl_raw=feature_lock.read_bytes()
    lock=json.loads(lock_raw)
    flock=json.loads(fl_raw)
    expected_blobs={p:git_blob(b) for p,b in sorted(before.items())}
    assert lock["total_scripts"]==59 and lock["blobs"]==expected_blobs, "BASE59_SOURCE_LOCK_MISMATCH"
    assert flock["total_sources"]==59 and flock["source_gitblobs"]==expected_blobs, "BASE59_FEATURE_LOCK_MISMATCH"
    assert flock["feature_flags"].get("WCS_F01_C01") is True
    assert flock["feature_flags"].get("SEVEN_JOBS_PVE_V1") is True
    assert EGG_ID not in flock["feature_flags"],"RELAY_DUPLICATE"
    cfg_path=dist/"default.project.json"
    cfg_raw=cfg_path.read_bytes()
    cfg=json.loads(cfg_raw)
    assert cfg["tree"]["ServerStorage"]["$attributes"]["P0D_RC_ENABLE_WCS_F01_C01"] is True
    assert cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    assert cfg["tree"]["StarterPlayer"]["StarterPlayerScripts"]["TrapRaidersHUD"]["$path"]=="src/client/HUD.client.luau"

    patcher=author/"tools/apply_relay.py"
    patch_path=author/"PATCH_OPS.json"
    assert git_blob(patcher.read_bytes())==PATCHER_GITBLOB, "AUTHOR_PATCHER_DRIFT"
    assert git_blob(patch_path.read_bytes())==PATCH_OPS_GITBLOB, "AUTHOR_PATCH_SPEC_DRIFT"
    spec=json.loads(patch_path.read_text("utf8"))
    assert spec["feature_id"]==EGG_ID and spec["rc_integrated"] is False
    assert len(spec["game_ops"])==9 and len(spec["hud_ops"])==6
    policy=policy_source.read_bytes()
    assert git_blob(policy)==spec["source_policy_gitblob"],"RELAY_POLICY_DRIFT"
    flags=json.loads((BASE_DIR/"rc_fastlane/FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    assert flags["SEVEN_JOBS_PVE_V1"]["enabled"] is True and flags["WCS_F01_C01"]["enabled"] is True
    assert type(flags[EGG_ID]["enabled"]) is bool
    if not enabled or not flags[EGG_ID]["enabled"]:
        assert sources(root)==before and original_lock.read_bytes()==lock_raw
        assert feature_lock.read_bytes()==fl_raw and cfg_path.read_bytes()==cfg_raw
        print("P0D_EGG_CLASSIC_OFF_COMBINED59_BYTE_EXACT_PASS")
        return False

    new_game=patch_text(game,spec["game_ops"])
    new_hud=patch_text(hud,spec["hud_ops"])
    # Protect against missing BoolValue automatically enabling an untested action.
    old='return flag == nil or (flag:IsA("BoolValue") and flag.Value == true)'
    strict='return flag ~= nil and flag:IsA("BoolValue") and flag.Value == true'
    assert new_game.count(old)==1,"MISSING_RUNTIME_FAIL_CLOSED_ANCHOR"
    new_game=new_game.replace(old,strict,1)
    assert new_game.count("remote.OnServerEvent:Connect(")==1,"SECOND_REMOTE_CONNECT"
    assert new_game.count('remote.Name = "TrapRaidersS1Remote"')==1,"SECOND_REMOTE"
    assert new_game.count("H2Score.deposit(")==game.count("H2Score.deposit("),"H2_SCORE_DRIFT"
    assert new_game.count("match.scores[team] += 1")==game.count("match.scores[team] += 1"),"SCORE_DRIFT"
    assert 'or EXPERIMENTAL_FIVE_EGG_MODE' in new_game,"H2_RELAY_NOT_FAIL_CLOSED"
    assert new_game.count("local function applyClassicEggRelay")==1
    assert new_game.count("workspace:Raycast(rootA.Position, direction, rayParams)")==1
    assert new_hud.count("relayButton.MouseButton1Click:Connect(fireClassicEggRelay)")==1
    assert new_hud.count("KeyCode.H")==1 and "JOB_PICK" in new_hud and "JOB_SKILL" in new_hud
    assert new_game.count("local now = os.clock()")>=1

    after=dict(before)
    after[GAME]=new_game.encode("utf8")
    after[HUD]=new_hud.encode("utf8")
    after[POLICY]=policy
    assert len(after)==60 and set(after)-set(before)=={POLICY}
    assert {p for p in before if before[p]!=after[p]}=={GAME,HUD}
    for key in before:
        if key not in (GAME,HUD):
            assert after[key]==before[key],("SOURCE_BODY_CHANGED",key)

    server_storage=cfg["tree"]["ServerStorage"]
    assert "P0D_RC_ENABLE_EGG_RELAY_CLASSIC" not in server_storage
    # Rojo creates a single explicitly true BoolValue for unpublished Studio
    # preview; without that BoolValue, the Game relay branch defaults OFF.
    server_storage["P0D_RC_ENABLE_EGG_RELAY_CLASSIC"]={
        "$className":"BoolValue",
        "$properties":{"Value":True}
    }
    lock["total_scripts"]=60
    lock["blobs"]={p:git_blob(b) for p,b in sorted(after.items())}
    lock["rc_egg_relay_classic_overlay"]={
        "id":EGG_ID, "author_ops_gitblob":PATCH_OPS_GITBLOB,
        "author_policy_gitblob":git_blob(policy),
        "source_before":59, "source_after":60,
        "preserved_existing_57_except_game_hud":True,
        "wcs_and_sevenjobs_policies_preserved":True,
        "mode":"CLASSIC_ONE_EGG_ONLY",
        "missing_runtime_flag":"OFF",
        "studio_only":True,
        "real_studio_2client_android_fun":"NOT_TESTED",
        "rollback":"Disable EGG_RELAY_CLASSIC_V1 build flag and restore combined59"}
    flock["total_sources"]=60
    flock["source_gitblobs"]={p:git_blob(b) for p,b in sorted(after.items())}
    flock["feature_flags"][EGG_ID]=True
    output={
        "candidate_only":True,
        "official_rc_adopted":False,
        "old_count":59,"new_count":60,
        "changed_existing":["server/Game.server.luau","client/HUD.client.luau"],
        "added_policy":POLICY,
        "h2_five_egg":"RELAY_DISABLED",
        "real_engine_studio":"NOT_TESTED"
    }
    # All preflight and source-level invariants above have been checked before
    # writing to the disposable build dist.
    (root/GAME).write_bytes(after[GAME])
    (root/HUD).write_bytes(after[HUD])
    (root/POLICY).write_bytes(after[POLICY])
    original_lock.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    feature_lock.write_text(json.dumps(flock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    cfg_path.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    (dist/"P0D_PRIVATE60_RECEIPT.json").write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    assert sources(root)==after
    print("P0D_WCS_7JOBS_EGG_CLASSIC_PRIVATE60_SOURCE_LOCK_PASS 60")
    return True

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--dist",type=Path,required=True)
    parser.add_argument("--author",type=Path,required=True)
    parser.add_argument("--policy",type=Path,required=True)
    parser.add_argument("--off-test",action="store_true")
    args=parser.parse_args()
    run(args.dist,args.author,args.policy,not args.off_test)
