#!/usr/bin/env python3
"""#444/#420: private-one-human trial of the ORIGINAL 9-mob Horde in real Game.

Official RC81 has verified B private Horde reset+hit+AI, but nonStudio original
StudioSolo.canStart requires 2 humans and prevents a 1-human phone test from
ever reaching ACTIVE. Only in OWNER-allowed private sessions reuse the existing
StudioSolo state machine; public count>=2 remains unchanged. READY remains
explicit, normal timeout and the original one Game authority remain intact.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path

from apply_private_horde_combat import read,blob

GAME="server/Game.server.luau"
SOLO="server/StudioSoloPreviewRules.luau"
HORDE="server/MusouHorde.luau"
GAME_PIN="211197f57959129a2ca91387ec1be038e0627010"
SOLO_PIN="de0e0df12346de2b4e7b607c74eddaaac693dc99"
HORDE_PIN="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
PARENT_HEAD="7005762b4a137fd46e4938c06fbaa937ce8f8cf9"
FEATURE="P0D_PRIVATE_ONE_HUMAN_HORDE_READY_TRIAL_V1"
OWNER_ATTR="P0D_PRIVATE_LIVE_HORDE_NINE"
OLD_DECL="local studioSoloRoundStarted = false\n"
NEW_DECL=(
  OLD_DECL+
  "-- "+FEATURE+": a private owner-controlled one-human neutral-monster trial.\n"+
  "-- Studio practice remains as-is; normal public matches still require two teams.\n"+
  "local function privateHordeTrialAllowed(): boolean\n"+
  '    return game.PrivateServerId ~= "" and\n'+
  '        workspace:GetAttribute("'+OWNER_ATTR+'") == true\n'+
  "end\n"
)
OLD_LATCH="StudioSolo.isSoloRound(RunService:IsStudio(),"
NEW_LATCH="StudioSolo.isSoloRound(RunService:IsStudio() or privateHordeTrialAllowed(),"
OLD_START="StudioSolo.canStart(RunService:IsStudio(), count,"
NEW_START="StudioSolo.canStart(RunService:IsStudio() or privateHordeTrialAllowed(), count,"
OLD_EMPTY="StudioSolo.emptyWinner(RunService:IsStudio(),"
NEW_EMPTY=("StudioSolo.emptyWinner(RunService:IsStudio() or "
           "(studioSoloRoundStarted and privateHordeTrialAllowed()),")

def one(g:str,a:str,b:str,count:int)->str:
    assert g.count(a)==count,("SINGLE_SOURCE_ANCHOR_DRIFT",a[:80],count,g.count(a))
    return g.replace(a,b,count)

def patch(raw:bytes)->bytes:
    assert blob(raw)==GAME_PIN,("OFFICIAL_RC81_GAME_DRIFT",blob(raw))
    game=raw.decode("utf8")
    assert FEATURE not in game and "privateHordeTrialAllowed" not in game
    assert game.count('horde:reset(match.serial,serverNow())')==1
    assert game.count('horde:hit(')>=1 and game.count('horde:tick(')==1
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count("local function resetRound()")==1
    assert game.count("local function tickRound()")==1
    assert game.count("if everybodyReady() and StudioSolo.canStart(")==1
    assert "if not everybodyReady() then" in game
    assert 'if RunService:IsStudio() and studioSoloRoundStarted' in game
    assert 'if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then' in game
    assert game.count('game.PrivateServerId ~= ""')==4, "B_HORDE_THREE_GATES_MUST_ALREADY_EXIST"
    assert game.count('workspace:GetAttribute("'+OWNER_ATTR+'") == true')==4
    assert 'if RunService:IsStudio() then horde:reset' not in game
    assert game.count('musouHitFeedback = ')==1
    assert "P0D_PRIVATE_ONE_HUMAN_HORDE_READY_TRIAL_V1" not in game
    assert 'if s.musouActive==true or (s.musouHitFeedback==true' not in game


    # Only four source regions changed (declaration, 1 latch, two calls, one
    # empty-winner) without changing the original Solo module or Game rules.
    g=one(game,OLD_DECL,NEW_DECL,1)
    g=one(g,OLD_LATCH,NEW_LATCH,1)
    g=one(g,OLD_START,NEW_START,2)
    g=one(g,OLD_EMPTY,NEW_EMPTY,1)
    assert g.count('StudioSolo.canStart(RunService:IsStudio() or privateHordeTrialAllowed()')==2
    assert g.count('StudioSolo.isSoloRound(RunService:IsStudio() or privateHordeTrialAllowed()')==1
    assert g.count("studioSoloRoundStarted and privateHordeTrialAllowed()")==1
    assert g.count("remote.OnServerEvent:Connect(")==1
    assert g.count('horde:reset(')==1 and g.count('horde:tick(')==1
    assert g.count('game.PrivateServerId ~= ""')==5
    assert g.count('workspace:GetAttribute("'+OWNER_ATTR+'") == true')==5
    assert g.count('if RunService:IsStudio() and studioSoloRoundStarted')==1
    assert g.count('if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then')==2
    # The two original sites are human-vs-StudioBOT attack and the BOT AI tick.
    # Both must remain Studio-only; private 1-human battles ONLY Horde monsters.
    assert 'if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then\n        local victim=SoloTeamBots.tryHumanHit(' in g
    assert 'if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then\n            local ok,err=pcall(SoloTeamBots.tick,now)' in g
    assert 'workspace:SetAttribute("'+OWNER_ATTR+'"' not in g
    assert g.count('musouHitFeedback = ')==1,"PRESERVE_LAST_RC_REAL_HIT"

    # Check exact reversible patch; this protects all other original Game text.
    restored=one(g,NEW_EMPTY,OLD_EMPTY,1)
    restored=one(restored,NEW_START,OLD_START,2)
    restored=one(restored,NEW_LATCH,OLD_LATCH,1)
    restored=one(restored,NEW_DECL,OLD_DECL,1)
    assert restored==game, "ORIGINAL_GAME_NOT_RESTORABLE"
    return g.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    assert not out.exists(),"DEST_ALREADY_EXISTS"
    if not enabled:
        print("P0D_ONE_HUMAN_PRIVATE_TRIAL_OFF_ZERO_WRITE")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and not base.is_symlink() and out.parent.is_dir()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==81
    assert {GAME,SOLO,HORDE,"client/HUD.client.luau"}.issubset(before)
    pins={p:blob(v) for p,v in sorted(before.items())}
    source=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    features=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert source["total_scripts"]==features["total_sources"]==81
    assert source["blobs"]==features["source_gitblobs"]==pins,"AUTHOR_SOURCE_LOCK_DRIFT"
    assert pins[GAME]==GAME_PIN and pins[SOLO]==SOLO_PIN and pins[HORDE]==HORDE_PIN
    for f in ("P0D_PRIVATE_LIVE_HORDE_NINE_V1",
              "P0D_PRIVATE_LIVE_HORDE_ATTACK_TICK_V2",
              "FB019_REAL_HIT_VISIBLE_SERVER_CONFIRMED_V2",
              "P0D_URGENT_READY_900_V1",
              "P0D_PRIVATE_LIVE_HORDE_HIT_TOAST_V3",
              "FB015_LIVE_ART_PRIVATE_CLIENT_PILOT_V1"):
        assert features["feature_flags"].get(f) is True,("PARENT_SOURCE_FEATURE_MISSING",f)
    assert not features["feature_flags"].get(FEATURE,False)
    original_solo=before[SOLO].decode("utf8")
    for signature in ("function Solo.canStart(", "function Solo.isSoloRound(",
                      "function Solo.emptyWinner(",
                      "if count >= minPlayers and red > 0 and blue > 0 then",
                      "return isStudio == true and count == 1"):
        assert signature in original_solo,("CANONICAL_SOLO_POLICY_DRIFT",signature)
    after=dict(before);after[GAME]=patch(before[GAME])
    assert len(after)==81 and {k for k in before if after[k]!=before[k]}=={GAME}
    pins_new={p:blob(v) for p,v in sorted(after.items())}
    receipt={
      "schema":"P0D_PRIVATE_ONE_HUMAN_HORDE_TRIAL_SOURCE_V1",
      "parent_official_sha":PARENT_HEAD,
      "parent_Game_blob":GAME_PIN,"new_Game_blob":pins_new[GAME],
      "parent_StudioSolo_blob":SOLO_PIN,"parent_Horde_blob":HORDE_PIN,
      "only_modified_existing_source":[GAME],"other80_byte_identical":True,
      "source_count":81,"single_Game_Remote_Horde":True,
      "private_owner_explicit_READY_required":True,
      "private_server_id_and_owner_attribute_required":True,
      "private_attribute":OWNER_ATTR,
      "public_min_players":"UNCHANGED_2",
      "one_player_pve":"PRIVATE_TRIAL_ONLY",
      "studio_bots_remain_studio_only":True,
      "original_9_mobs_reset_hit_tick_unchanged":True,
      "round_epoch_anti_replay_unchanged":True,
      "automatic_start":False,
      "real_private_runtime":"NOT_TESTED",
      "public_default":"OFF",
      "live_horde_decision":"LIVE_HORDE_NO_GO",
      "live_art_decision":"LIVE_ART_NO_GO",
      "art_decision":"ART_NO_GO","mobile_decision":"MOBILE_NO_GO",
      "fun_decision":"FUN_NO_GO","owner_accepted":False,
      "official_rc_adopted":False,
      "rollback":"omit one source-only overlay, rebuild exact official RC81"
    }
    source["blobs"]=pins_new
    features["source_gitblobs"]=pins_new
    source["private_one_human_trial"]=receipt
    features["private_one_human_trial"]=receipt
    features["feature_flags"][FEATURE]=True
    scratch=Path(tempfile.mkdtemp(prefix=".p0d_horde_one_player_",dir=str(out.parent)))
    temp=scratch/"source"
    try:
        shutil.copytree(base,temp,symlinks=False)
        (temp/"src"/GAME).write_bytes(after[GAME])
        (temp/"SOURCE_LOCK.json").write_text(json.dumps(source,ensure_ascii=False,indent=2)+"\n","utf8")
        (temp/"RC_FEATURE_LOCK.json").write_text(json.dumps(features,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(temp)==after and read(base)==before
        os.replace(temp,out)
    finally:
        shutil.rmtree(scratch,ignore_errors=True)
    print("P0D_PRIVATE_ONE_HUMAN_HORDE_RC81_ONLY_GAME_SOURCE_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
