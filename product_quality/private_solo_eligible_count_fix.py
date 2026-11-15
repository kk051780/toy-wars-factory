#!/usr/bin/env python3
"""FB005 actual 82-script Game: solo players count excludes inactive observers.

A pinned private A-PREP child of original #297 + quality #471 candidate.
No official RC/main write; existing SoloTeamBots and egg authority unchanged.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
from role7_respawn_guard import extract, verify, blob

RC="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
PARENT="P0D_ROLE7_SOLO_BOTS_SAFE_SPECTATOR_RC82.rbxlx"
PARENT_SHA="2f86fcaaa392ef26e277ee35387525f7ad58f41b0b8baf6cc4d4bee61bb11ebb"
GAME_BLOB="2d98c3c7ac89ea2195b46afb171cfb78af37615e"
BOT_BLOB="a77176fdcfe3351b5dc9ed4aa23fcf48a28edd53"
OUTPUT="P0D_SOLO_AI_ELIGIBLE_COUNT_SAFE_RC82.rbxlx"
GAME="server/Game.server.luau"
BOT="server/SoloTeamBots.luau"
EXPECTED_PLACE_SHA="cabd147e588b4dc7599e115c335b0d8c9acaf9f953c48a2dcb79d6985bbd2246"
EXPECTED_PLACE_BYTES=780882
EXPECTED_GAME_BLOB="ee05adc30c18800eb3d51473fdbb7719b17165ca"
LATCH_BEFORE=('studioSoloRoundStarted = StudioSolo.isSoloRound(RunService:IsStudio() or privateHordeTrialAllowed(),\n'
    '        #Players:GetPlayers(), teamCount("RED"), teamCount("BLUE"))')
LATCH_AFTER=('studioSoloRoundStarted = StudioSolo.isSoloRound(RunService:IsStudio() or privateHordeTrialAllowed(),\n'
    '        #eligibleSoloPlayers(), teamCount("RED"), teamCount("BLUE"))')
FAIL_BEFORE=('if studioSoloRoundStarted and match.phase=="ACTIVE"\n'
    '                    and #Players:GetPlayers()==1 then\n'
    '                    stopRound("DRAW","SOLO_BOTS_TICK_FAILURE")')
FAIL_AFTER=('if studioSoloRoundStarted and match.phase=="ACTIVE"\n'
    '                    and #eligibleSoloPlayers()==1 then\n'
    '                    stopRound("DRAW","SOLO_BOTS_TICK_FAILURE")')

def sha(raw):return hashlib.sha256(raw).hexdigest()

def swap(src,old,new,label):
    if src.count(old)!=1 or new in src:raise ValueError("ORIGINAL_GAME_ANCHOR_DRIFT_"+label)
    return src.replace(old,new,1)

def egg_block(s):
    begin='for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect'
    end='\n-- P0D_SAVED_PVE_MASTERY_V1:'
    a=s.index(begin)
    return s[a:s.index(end,a)]

def patch(original):
    out=swap(original,LATCH_BEFORE,LATCH_AFTER,"SOLO_MATCH_LATCH")
    out=swap(out,FAIL_BEFORE,FAIL_AFTER,"SOLO_BOT_TICK_FAILURE")
    if egg_block(out)!=egg_block(original):raise ValueError("EGG_SCORE_WINNER_CHANGED")
    for token in ('if map.model:FindFirstChild("P0D_SAFE_LOBBY")==nil then',
        'horde:tick(now,eligibleSoloPlayers(),healthy)',
        'pcall(SoloTeamBots.start,map,getTeamName(player),botAuthority)',
        'pcall(SoloTeamBots.tick,now)',
        'SoloTeamBots.stop()',
        'sevenJobPickAckSeq[player]~=selectedAck',
        'player.Character~=castCharacter',
        'personalEggDeposits[player]=(personalEggDeposits[player] or 0)+1'):
        if token not in out:raise ValueError("LOST_ORIGINAL_GAMEPLAY:"+token)
    return out

def build(parent,output,extract_dir=None):
    with ZipFile(parent) as z:
        members=z.namelist()
        if len(members)!=len(set(members)) or any(
            n.startswith("/") or ".." in Path(n).parts for n in members
        ):raise ValueError("UNSAFE_PARENT_ZIP")
        raw=z.read(PARENT)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if sha(raw)!=PARENT_SHA or receipt.get("official_rc_head")!=RC or not receipt.get("private_only"):
        raise ValueError("UNPINNED_PRIVATE_PARENT")
    originals=verify(raw,lock,feature)
    if lock["blobs"].get(GAME)!=GAME_BLOB or lock["blobs"].get(BOT)!=BOT_BLOB:
        raise ValueError("AUTHOR_GAME_BOT_BLOB_DRIFT")
    root,scripts=extract(raw)
    new_game=patch(originals["Game"].text)
    scripts["Game"].text=new_game
    place=ET.tostring(root,encoding="utf-8")
    after=extract(place)[1]
    if len(after)!=82 or any(
        after[n].text!=originals[n].text for n in originals if n!="Game"
    ):raise ValueError("OTHER_81_SOURCE_CHANGED")
    game_blob=blob(new_game)
    if game_blob!=EXPECTED_GAME_BLOB or len(place)!=EXPECTED_PLACE_BYTES or sha(place)!=EXPECTED_PLACE_SHA:
        raise ValueError("REPRODUCIBLE_OUTPUT_PIN_CHANGED")
    lock["blobs"][GAME]=feature["source_gitblobs"][GAME]=game_blob
    verify(place,lock,feature)
    report={"schema":"P0D_FB005_SOLO_AI_ELIGIBLE_COUNT_V1",
        "official_rc_head":RC,"official_rc_write":False,
        "parent_sha256":PARENT_SHA,"place_sha256":sha(place),
        "place_bytes":len(place),"new_game_blob":game_blob,
        "bot_source_blob_unchanged":BOT_BLOB,
        "scripts":82,"unchanged_parent_scripts":81,
        "egg_score_winner_unchanged":True,"source_lock_exact":True,
        "private_only":True,"default_off":True,
        "soloround_eligible_count":True,"bot_tick_failure_eligible_count":True,
        "native":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN",
        "owner":False,"product":"NO_GO"}
    with ZipFile(output,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT,place)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(report,indent=2)+"\n")
    if extract_dir:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for name,node in after.items():
            (extract_dir/(name+".luau")).write_text(node.text,encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.parent,a.out,a.extract),ensure_ascii=False,indent=2))
