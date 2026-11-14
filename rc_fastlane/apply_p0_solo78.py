#!/usr/bin/env python3
"""P0 #395 private78 sole Game/HUD repair for botless one-player five-egg.

Backport the source-authored PR #395 solo Classic gate into the already unified
private78 without adding a feature ID, source script, Game, Remote or DataStore.
Official RC66 and complete parent private78 stay byte-for-byte unchanged.
"""
from __future__ import annotations
import argparse,json,os,shutil,tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob,BASE_RC
from apply_p0_results78 import GAME,REPAIR
HUD="client/HUD.client.luau"
ID="FB005_SOLO_FIVE_EGG_BOTLESS_MODE_GUARD_QA_V1"
AUTHOR_PR=395
OLD="EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE"
NEW='''EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio()
        and #Players:GetPlayers()>1 and chosenMode==ModeVote.SCORE'''
READY_OLD="ready = roundReady[player] == true,"
READY_NEW='''ready = roundReady[player] == true,
        soloFiveEggUnavailable = RunService:IsStudio()
            and #Players:GetPlayers()==1,'''
HUD_OLD='    lobbyHelp.Visible = s.phase == "LOBBY"'
HUD_NEW='''    lobbyHelp.Visible = s.phase == "LOBBY"
    -- Reuse existing lobby help; no HUD overlay or large text on battlefield.
    if s.soloFiveEggUnavailable == true then
        lobbyHelp.Text = "ソロ：通常卵戦／味方2・敵3のAI\\n5個卵戦は2人以上"
    else
        lobbyHelp.Text = "敵城の卵を奪い自城へ！城を破壊しても勝利\\n攻撃：F／タップ　罠：T"
    end'''

def sub_once(s:str,a:str,b:str)->str:
    assert s.count(a)==1,("SOLO_GAME_OR_HUD_SOURCE_DRIFT",a,s.count(a))
    return s.replace(a,b,1)

def patch_game(s:str)->str:
    assert "soloFiveEggUnavailable" not in s,"SOLO_ALREADY_APPLIED"
    assert REPAIR in s,"SOLO_RESULTS_LOBBY_FIX_NOT_PRESENT"
    assert s.count("local function resetRound()")==1 and s.count("local function tickRound()")==1
    assert s.count("remote.OnServerEvent:Connect(")==1
    assert s.count("pcall(SoloTeamBots.start,map,")==1
    assert "if RunService:IsStudio() and studioSoloRoundStarted\n        and not EXPERIMENTAL_FIVE_EGG_MODE then" in s, "SOLO_BOT_START_GUARD_DRIFT"
    s=sub_once(s,OLD,NEW)
    s=sub_once(s,READY_OLD,READY_NEW)
    assert s.count('#Players:GetPlayers()>1 and chosenMode==ModeVote.SCORE')==1
    assert s.count("soloFiveEggUnavailable") == 1
    assert s.count("remote.OnServerEvent:Connect(")==1
    return s

def patch_hud(s:str)->str:
    assert "soloFiveEggUnavailable" not in s,"SOLO_HUD_ALREADY_APPLIED"
    assert "VoluntaryReady" in s and "lobbyHelp" in s
    s=sub_once(s,HUD_OLD,HUD_NEW)
    assert s.count("soloFiveEggUnavailable")==1
    assert s.count('lobbyHelp.Visible = s.phase == "LOBBY"')==1
    return s

def compose(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_PRIVATE78_SOLO_BOTLESS_OFF_ZERO_WRITE");return False
    base=base.absolute();out=out.absolute()
    assert out.parent.is_dir() and not out.exists(), "SOLO_OUT_EXISTS_OR_PARENT_MISSING"
    assert out!=base and not out.is_relative_to(base) and not base.is_relative_to(out), "SOLO_INPUT_OUTPUT_OVERLAP"
    before=read(base)
    assert len(before)==78 and GAME in before and HUD in before, "SOLO_REQUIRES_REAL_78"
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(v) for p,v in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==78
    assert sl["blobs"]==fl["source_gitblobs"]==pins, "SOLO_INPUT_LOCK_DRIFT"
    assert fl["p0_private77"]["official_base"]==BASE_RC
    assert fl["p0_results78"]["no_new_source"] is True
    assert fl["p0_fullbody78"]["other77_byte_identical"] is True
    assert fl["feature_flags"]["FB005_STUDIO_SOLO_TEAM_BOTS_CLASSIC_V1"] is True
    assert ID not in fl["feature_flags"] and "p0_solo78" not in fl
    game=patch_game(before[GAME].decode("utf8")).encode("utf8")
    hud=patch_hud(before[HUD].decode("utf8")).encode("utf8")
    after={**before,GAME:game,HUD:hud}
    assert len(after)==78
    assert {k for k in before if before[k]!=after[k]}=={GAME,HUD}
    assert all(before[k]==after[k] for k in before if k not in (GAME,HUD))
    pins78={p:gitblob(v) for p,v in sorted(after.items())}
    receipt={
        "id":ID,"author_pr":AUTHOR_PR,
        "scope":"ONLY existing Game and HUD: one-human SCORE vote -> Classic SOLO bot enabled",
        "one_human":"CLASSIC_WITH_2_ALLY_3_ENEMY_BOTS",
        "two_or_more_humans":"ORIGINAL_SCORE_FIVE_EGG_VOTE_PRESERVED",
        "snapshot_flag":"soloFiveEggUnavailable",
        "new_feature_count":0,"new_script_count":0,"source_count":78,
        "other76_sources_byte_identical":True,
        "parent78_byte_identical":True,
        "studio_solo":"NOT_TESTED","android":"NOT_TESTED",
        "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
        "formal_rc_adoption":False,
        "rollback":"omit P0 SOLO78 overlay to exact fullbody + results private78",
    }
    sl["blobs"]=pins78;fl["source_gitblobs"]=pins78
    sl["p0_solo78"]=receipt;fl["p0_solo78"]=receipt
    root=Path(tempfile.mkdtemp(prefix=".p0d_solo78_",dir=str(out.parent)))
    stage=root/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(game)
        (stage/"src"/HUD).write_bytes(hud)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins78
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins78
        assert not out.exists()
        os.replace(stage,out)
    finally:
        shutil.rmtree(root,ignore_errors=True)
    assert read(base)==before,"SOLO_PARENT78_CHANGED"
    print("P0_PRIVATE78_SOLO_BOTLESS_CLASSIC_MODE_GAME_HUD_SOURCE_LOCK_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    a=p.parse_args()
    compose(a.base,a.out,a.enabled=="true")
