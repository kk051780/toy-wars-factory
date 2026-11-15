#!/usr/bin/env python3
"""FB005 private 1-human team bots: real Game + original SoloTeamBots source.
No official RC, Store, egg, Remote or match-authority writes.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
from collections import Counter
from zipfile import ZipFile, ZIP_DEFLATED
from xml.etree import ElementTree as ET
from role7_respawn_guard import extract, verify, blob, sha

PARENT="P0D_ROLE7_ACK_WIND_BUILDER_COMBO_RESPAWN_SPECTATOR_RC82.rbxlx"
PARENT_SHA="bbb9c919cb11cfc5147a75a9d8f8e770eb5a7d540acfffeb650010f5710e0d1c"
OUT="P0D_ROLE7_SPECTATOR_PRIVATE_SOLO_BOTS_RC82.rbxlx"
BASE="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
GAME="server/Game.server.luau"
BOTS="server/SoloTeamBots.luau"
GAME_BLOB="976d2a7118a0013f1dc32f414ec4fe54b9b84b31"
BOTS_BLOB="a77176fdcfe3351b5dc9ed4aa23fcf48a28edd53"
PLACE_SHA="457cb3fb34d9fe72485e335aa0e7307c06fab75bcff09cffd6d45615d94bfde8"

def swap(s, before, after, key):
    if s.count(before)!=1 or after in s:
        raise ValueError("AMBIGUOUS_OR_REPEAT_PATCH:"+key)
    return s.replace(before, after, 1)

def egg_block(s):
    begin=s.index('for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect')
    end=s.index('\n-- P0D_SAVED_PVE_MASTERY_V1:',begin)
    return s[begin:end]

def build(parent,output,extract_dir=None):
    with ZipFile(parent) as z:
        if len(set(z.namelist()))!=len(z.namelist()):
            raise ValueError("DUPLICATE_PARENT_ZIP_MEMBER")
        raw=z.read(PARENT)
        sl=json.loads(z.read("SOURCE_LOCK.json"))
        fl=json.loads(z.read("RC_FEATURE_LOCK.json"))
        meta=json.loads(z.read("RECEIPT.json"))
    if sha(raw)!=PARENT_SHA or meta.get("official_rc_head")!=BASE:
        raise ValueError("STALE_OR_UNVERIFIED_PARENT")
    original=verify(raw,sl,fl)
    root,els=extract(raw)
    if len(els)!=82 or sl["blobs"][GAME]!=blob(original["Game"].text) or sl["blobs"][BOTS]!=blob(original["SoloTeamBots"].text):
        raise ValueError("ORIGINAL_GAME_BOT_SOURCE_IDENTITY_DRIFT")
    expected_classes={"Game":"Script","SoloTeamBots":"ModuleScript"}
    located={}
    for item in root.iter("Item"):
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        if name in expected_classes:
            if name in located or item.get("class")!=expected_classes[name]:
                raise ValueError("DUPLICATE_OR_WRONG_GAME_BOT_CLASS")
            located[name]=True
    if set(located)!=set(expected_classes):
        raise ValueError("MISSING_AUTHOR_MODULE")
    game=original["Game"].text
    bots=original["SoloTeamBots"].text
    gate='local function privateHordeTrialAllowed(): boolean\n    return game.PrivateServerId ~= "" and\n        workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE") == true\nend'
    game=swap(game,gate,gate+'\n-- Private single-player team bots: independent opt-in and default OFF.\nlocal function privateSoloBotsTrialAllowed(): boolean\n    return privateHordeTrialAllowed()\n        and workspace:GetAttribute("P0D_PRIVATE_SOLO_TEAM_BOTS") == true\nend',"PRIVATE_BOT_GATE")
    game=swap(game,
       'if RunService:IsStudio() and studioSoloRoundStarted\n        and not EXPERIMENTAL_FIVE_EGG_MODE then',
       'if (RunService:IsStudio() or privateSoloBotsTrialAllowed())\n        and studioSoloRoundStarted and not EXPERIMENTAL_FIVE_EGG_MODE then',"SOLO_BOT_START")
    attack_gate='if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then'
    if game.count(attack_gate)!=2:
        raise ValueError("SOLO_ATTACK_OR_TICK_GATES_CHANGED")
    game=game.replace(attack_gate,
      'if (RunService:IsStudio() or privateSoloBotsTrialAllowed())\n        and not EXPERIMENTAL_FIVE_EGG_MODE then')
    game=swap(game,
       '    tickTraps(now)\n    -- The ORIGINAL Game clock alone owns auto-training;',
       '    tickTraps(now)\n    -- Disable/rollback private bot models immediately, never affect Studio.\n    if not RunService:IsStudio() and SoloTeamBots.isActive()\n        and not privateSoloBotsTrialAllowed() then\n        SoloTeamBots.stop()\n        if studioSoloRoundStarted and match.phase=="ACTIVE"\n            and #eligibleSoloPlayers()==1 then\n            stopRound("DRAW","PRIVATE_SOLO_BOTS_DISABLED")\n        end\n    end\n    -- The ORIGINAL Game clock alone owns auto-training;', "SOLO_BOT_DISABLE")
    bots=swap(bots,
       '    if not RunService:IsStudio() then return false end\n    local eligible=0',
       '    -- Non-Studio agents require private-server double opt-in.\n    if not (RunService:IsStudio() or\n        (game.PrivateServerId ~= ""\n         and workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE_NINE")==true\n         and workspace:GetAttribute("P0D_PRIVATE_SOLO_TEAM_BOTS")==true)) then\n        return false\n    end\n    local eligible=0',"BOT_MODULE_PRIVATE_ONLY")
    bots=swap(bots,
       '    folder:SetAttribute("StudioBotPreview",true)',
       '    folder:SetAttribute("StudioBotPreview",RunService:IsStudio())',"STUDIO_METADATA")
    if egg_block(original["Game"].text)!=egg_block(game):
        raise ValueError("EGG_STEAL_DEPOSIT_WINNER_CHANGED")
    for proof in ('sevenJobPickAckSeq[player]~=selectedAck',
        'player.Character~=castCharacter',
        'horde:tick(now,eligibleSoloPlayers(),healthy)',
        'pcall(SoloTeamBots.start,map,getTeamName(player),botAuthority)',
        'pcall(SoloTeamBots.tick,now)',
        'SoloTeamBots.tryHumanHit(team,root.Position,look'):
        if proof not in game:raise ValueError("MISSING_AUTHOR_FIX:"+proof)
    for proof in ('function Bot.tick(now)', 'callbacks.deposit(bot,bot.team,bot.carry)',
                  'function Bot.tryHumanHit('):
        if proof not in bots:raise ValueError("MISSING_ORIGINAL_BOT_AUTHORITY:"+proof)
    if blob(game)!=GAME_BLOB or blob(bots)!=BOTS_BLOB:
        raise ValueError("REPRODUCED_SOURCE_GITBLOB_MISMATCH")
    els["Game"].text=game
    els["SoloTeamBots"].text=bots
    place=ET.tostring(root,encoding="utf-8")
    if sha(place)!=PLACE_SHA or len(place)!=780350:
        raise ValueError("ACTUAL_PLACE_REPRODUCTION_MISMATCH")
    _,after=extract(place)
    if any(after[n].text!=original[n].text for n in original if n not in ("Game","SoloTeamBots")):
        raise ValueError("OTHER_80_SOURCE_CHANGED")
    sl["blobs"][GAME]=fl["source_gitblobs"][GAME]=GAME_BLOB
    sl["blobs"][BOTS]=fl["source_gitblobs"][BOTS]=BOTS_BLOB
    verify(place,sl,fl)
    r={"schema":"FB005_PRIVATE_SOLO_TEAM_BOTS_V1",
       "official_rc_head":BASE,"official_rc_write":False,"source_scripts":82,
       "unchanged_parent_source":80,"changed":[GAME,BOTS],
       "place_sha256":PLACE_SHA,"place_bytes":len(place),"source_lock_exact":True,
       "egg_score_winner_source_exact":True,"private_only":True,"default_off":True,
       "server_optin":["P0D_PRIVATE_LIVE_HORDE_NINE","P0D_PRIVATE_SOLO_TEAM_BOTS"],
       "native":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN","product":"NO_GO"}
    with ZipFile(output,"w",ZIP_DEFLATED) as z:
        z.writestr(OUT,place)
        z.writestr("SOURCE_LOCK.json",json.dumps(sl,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(fl,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(r,indent=2)+"\n")
    if extract_dir:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for n,src in after.items():
            (extract_dir/(n+".luau")).write_text(src.text,encoding="utf-8")
    return r

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.parent,a.out,a.extract),indent=2))
if __name__=="__main__":main()
