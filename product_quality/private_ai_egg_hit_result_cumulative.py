#!/usr/bin/env python3
"""FB005: keep one ORIGINAL Game score authority while fixing private AI hit/victory UX.
PRIVATE A-PREP ONLY. Not an official RC/adoption/studio-gameplay PASS.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from role7_respawn_guard import extract, verify, blob

PARENT_NAME="P0D_FB005_BOTS_SPECTATOR_SAFE_LOBBY_RC82.rbxlx"
OUTPUT_NAME="P0D_FB005_AI_RAID_RESULT_PRIVATE_RC82.rbxlx"
RC="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
PARENT_SHA="11c9afe248915989531ff4945cb7267e70f7bf0e7ebfeb8782ac22d8dcdfe6d6"
PARENT_GAME_BLOB="19219949555bd86359e50ed245ca1eebecfd3e32"
GAME="server/Game.server.luau"
BOT="server/SoloTeamBots.luau"
EXPECTED_GAME="95844ce3dea61db9f13c7b5808388700c7ba7cfd"
EXPECTED_PLACE="6d007e4024c2fce71b21bfd89ffc66a9b4b29f524d99d8a1ae24e0abb443e42a"
EXPECTED_BYTES=781291

PRIORITY_OLD="""    -- Cannot hit castle with the same swing after hitting neutral soldiers.
    if mobHits>0 then return end
    -- Human can really hurt an enemy humanoid BOT within the same
"""
PRIORITY_NEW="""    -- An enemy team BOT may be hit even if a neutral mob was hit in this swing.
    -- Real enemy Players already have that priority above; bots must match.
    -- Human can really hurt an enemy humanoid BOT within the same
"""
CASTLE_OLD="""        end
    end
    local enemy = Rules.opponent(team)
    local core = map.teams[enemy].core
"""
CASTLE_NEW="""        end
    end
    -- One swing may strike a mob and an enemy player/bot, NEVER the castle too.
    if mobHits>0 then return end
    local enemy = Rules.opponent(team)
    local core = map.teams[enemy].core
"""
REASON_OLD="""        if winner then stopRound(winner,"STUDIO_BOT_EGG_CAPTURE")
        else broadcast() end
"""
REASON_NEW="""        -- A private 1-human raid uses the normal egg-victory result message.
        -- Keep the historical Studio practice receipt unchanged.
        if winner then
            stopRound(winner,if RunService:IsStudio() then "STUDIO_BOT_EGG_CAPTURE"
                else "EGG_CAPTURE")
        else broadcast() end
"""

# Reuse the verified existing #471 solo eligibility fix, not a second Game owner.
KICKOFF_OLD='''    studioSoloRoundStarted = StudioSolo.isSoloRound(RunService:IsStudio() or privateHordeTrialAllowed(),
        #Players:GetPlayers(), teamCount("RED"), teamCount("BLUE"))'''
KICKOFF_NEW='''    -- A COUNTDOWN spectator is not an eligible solo rival at kickoff.
    studioSoloRoundStarted = StudioSolo.isSoloRound(RunService:IsStudio() or privateHordeTrialAllowed(),
        #eligibleSoloPlayers(), teamCount("RED"), teamCount("BLUE"))'''
BOT_FAILURE_OLD='''                if studioSoloRoundStarted and match.phase=="ACTIVE"
                    and #Players:GetPlayers()==1 then
                    stopRound("DRAW","SOLO_BOTS_TICK_FAILURE")'''
BOT_FAILURE_NEW='''                -- A neutral/late-join spectator does not prevent fail-closed DRAW.
                if studioSoloRoundStarted and match.phase=="ACTIVE"
                    and #eligibleSoloPlayers()==1 then
                    stopRound("DRAW","SOLO_BOTS_TICK_FAILURE")'''

def sha(b):return hashlib.sha256(b).hexdigest()
def swap_once(s,old,new,key):
    if s.count(old)!=1 or new in s:raise ValueError("SOURCE_HUNK_DRIFT_OR_DUPLICATE:"+key)
    return s.replace(old,new,1)
def human_egg(s):
    start=s.index("map.teams[team].eggPrompt.Triggered:Connect(function(player: Player)")
    end=s.index("\n-- P0D_SAVED_PVE_MASTERY_V1:",start)
    return s[start:end]

def build(parent,out,extract_dir=None):
    with ZipFile(parent) as z:
        names=z.namelist()
        if len(set(names))!=len(names) or any(n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_ZIP_MEMBERS")
        place=z.read(PARENT_NAME)
        sl=json.loads(z.read("SOURCE_LOCK.json"))
        fl=json.loads(z.read("RC_FEATURE_LOCK.json"))
        old_receipt=json.loads(z.read("RECEIPT.json"))
    if sha(place)!=PARENT_SHA or sl["blobs"].get(GAME)!=PARENT_GAME_BLOB \
            or old_receipt.get("official_rc_head")!=RC:
        raise ValueError("WRONG_PARENT_OR_OFFICIAL_ANCHOR")
    original=verify(place,sl,fl)
    root,source=extract(place)
    old=original["Game"].text
    start=old.index("local function applyAttack(")
    end=old.index("\n-- H1 RAIDER wind:",start)
    attack=old[start:end]
    attack=swap_once(attack,PRIORITY_OLD,PRIORITY_NEW,"BOT_ATTACK_PRIORITY")
    attack=swap_once(attack,CASTLE_OLD,CASTLE_NEW,"NO_CASTLE_DOUBLE_HIT")
    if not attack.index("SoloTeamBots.tryHumanHit")<attack.index("if mobHits>0 then return end")<attack.index("local enemy = Rules.opponent(team)"):
        raise ValueError("ATTACK_PRIORITY_NOT_FIXED")
    new=old[:start]+attack+old[end:]
    start=new.index("local botAuthority={")
    end=new.index("    attackHuman=function(",start)
    bot_auth=swap_once(new[start:end],REASON_OLD,REASON_NEW,"BOT_EGG_WIN_RESULT")
    new=new[:start]+bot_auth+new[end:]
    new=swap_once(new,KICKOFF_OLD,KICKOFF_NEW,"SOLO_COUNTDOWN_EXCLUDE_SPECTATOR")
    new=swap_once(new,BOT_FAILURE_OLD,BOT_FAILURE_NEW,"SOLO_ERROR_FAILCLOSED_WITH_SPECTATOR")
    if human_egg(old)!=human_egg(new):
        raise ValueError("HUMAN_EGG_SCORE_REGRESSION")
    for essential in ("P0D_PRIVATE_SOLO_TEAM_BOTS","P0D_SAFE_LOBBY","privateSoloBotsTrialAllowed()",
        "horde:tick(now,eligibleSoloPlayers(),healthy)","sevenJobPickAckSeq[player]~=selectedAck",
        "player.Character~=castCharacter","personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1",
        "match.scores[homeTeam]+=1","Rules.winner(match.scores,match.hp,Config.CapturesToWin)"):
        if essential not in new:raise ValueError("ORIGINAL_GAME_CONTRACT_REMOVED:"+essential)
    if blob(new)!=EXPECTED_GAME:raise ValueError("GAME_BLOB_REPRODUCIBILITY_FAILURE")
    source["Game"].text=new
    output_place=ET.tostring(root,encoding="utf-8")
    if sha(output_place)!=EXPECTED_PLACE or len(output_place)!=EXPECTED_BYTES:
        raise ValueError("PLACE_BYTES_OR_SHA_REPRODUCIBILITY_FAILURE")
    after=extract(output_place)[1]
    if any(after[n].text!=original[n].text for n in original if n!="Game"):
        raise ValueError("OTHER_81_LUAU_CHANGED")
    sl["blobs"][GAME]=fl["source_gitblobs"][GAME]=EXPECTED_GAME
    verify(output_place,sl,fl)
    meta={"schema":"P0D_FB005_AI_EGG_RESULT_ELIGIBLE_SOLO_AND_FAILURE_V2",
          "official_rc_head":RC,"official_rc_write":False,
          "place_sha256":EXPECTED_PLACE,"place_bytes":EXPECTED_BYTES,
          "game_blob":EXPECTED_GAME,"bots_blob":sl["blobs"][BOT],
          "sources":82,"unchanged_parent_sources":81,
          "human_egg_score_exact":True,"private_default_off":True,
          "bot_hit_and_egg_reason_fixed":True,
          "solo_late_spectator_not_opponent":True,"bot_tick_failure_draw_with_spectator":True,
          "native":"NOT_RUN","rojo":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN",
          "owner":False,"product":"NO_GO"}
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT_NAME,output_place)
        z.writestr("SOURCE_LOCK.json",json.dumps(sl,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(fl,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(meta,ensure_ascii=False,indent=2)+"\n")
    if extract_dir:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for n,element in after.items():
            (extract_dir/(n+".luau")).write_text(element.text,encoding="utf-8")
    return meta

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    args=p.parse_args()
    print(json.dumps(build(args.parent,args.out,args.extract),ensure_ascii=False,indent=2))
