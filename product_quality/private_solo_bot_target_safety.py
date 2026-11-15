#!/usr/bin/env python3
"""#470 FB005: fix real original SoloTeamBots spectator/neutral targeting.

Builds a source-locked private-only child of existing #471 solo+safe-lobby
candidate. No new match authority, no second bot implementation, no RC write.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED
from role7_respawn_guard import extract, verify, blob

BASE = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
PARENT = "P0D_ROLE7_SOLO_BOTS_SAFE_SPECTATOR_RC82.rbxlx"
PARENT_SHA = "2f86fcaaa392ef26e277ee35387525f7ad58f41b0b8baf6cc4d4bee61bb11ebb"
GAME_BLOB = "2d98c3c7ac89ea2195b46afb171cfb78af37615e"
BOT_BLOB = "a77176fdcfe3351b5dc9ed4aa23fcf48a28edd53"
OUTPUT = "P0D_ROLE7_SOLO_BOTS_SAFE_TARGETS_RC82.rbxlx"
GAME = "server/Game.server.luau"
BOT = "server/SoloTeamBots.luau"

FIND_BEFORE = 'if team~=bot.team and root and hum and hum.Health>0 then'
FIND_AFTER = (
    'if (team=="RED" or team=="BLUE") and team~=bot.team\n'
    '            -- Late observers have no role in the battle, even if team lingers.\n'
    '            and p:GetAttribute("P0D_LateJoinSpectator")~=true\n'
    '            and root and hum and hum.Health>0 then'
)
DAMAGE_BEFORE = (
    'or target.Team==nil or target.Team.Name==bot.team then return end'
)
DAMAGE_AFTER = (
    'or target.Team==nil\n'
    '            or (target.Team.Name~="RED" and target.Team.Name~="BLUE")\n'
    '            or target:GetAttribute("P0D_LateJoinSpectator")==true\n'
    '            or target.Team.Name==bot.team then return end'
)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def swap(src: str, old: str, new: str, tag: str) -> str:
    if src.count(old) != 1 or new in src:
        raise ValueError("SOURCE_TARGET_GUARD_DRIFT_" + tag)
    return src.replace(old, new, 1)

def egg_authority(src: str) -> str:
    begin = 'for _, team in ipairs({"RED", "BLUE"}) do\n    map.teams[team].eggPrompt.Triggered:Connect'
    end = '\n-- P0D_SAVED_PVE_MASTERY_V1:'
    start = src.index(begin)
    return src[start:src.index(end, start)]

def patch(game_source: str, bot_source: str):
    game_fixed = swap(game_source, DAMAGE_BEFORE, DAMAGE_AFTER, "SERVER_DAMAGE")
    bot_fixed = swap(bot_source, FIND_BEFORE, FIND_AFTER, "AI_NEAREST_ENEMY")
    if egg_authority(game_source) != egg_authority(game_fixed):
        raise ValueError("EGG_SCORE_WINNER_REGRESSION")
    for token in (
        'privateSoloBotsTrialAllowed()',
        'horde:tick(now,eligibleSoloPlayers(),healthy)',
        'if map.model:FindFirstChild("P0D_SAFE_LOBBY")==nil then',
        'sevenJobPickAckSeq[player]~=selectedAck',
        'player.Character~=castCharacter',
        'SoloTeamBots.stop()',
        'pcall(SoloTeamBots.tick,now)',
        'callbacks.deposit(bot,bot.team,bot.carry)',
    ):
        if token == 'callbacks.deposit(bot,bot.team,bot.carry)':
            if token not in bot_fixed: raise ValueError("BOT_EGG_AI_REGRESSION")
        elif token not in game_fixed:
            raise ValueError("GAME_ROLE_OR_AI_REGRESSION:" + token)
    if 'game.PrivateServerId ~= ""' not in bot_fixed or 'P0D_PRIVATE_SOLO_TEAM_BOTS' not in bot_fixed:
        raise ValueError("BOT_PRIVATE_OPTIN_LOST")
    return game_fixed, bot_fixed

def build(parent: Path, output: Path, extract_dir: Path | None = None) -> dict:
    with ZipFile(parent) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(
            n.startswith("/") or ".." in Path(n).parts for n in names
        ): raise ValueError("UNSAFE_PARENT_ZIP")
        place = z.read(PARENT)
        lock = json.loads(z.read("SOURCE_LOCK.json"))
        feature = json.loads(z.read("RC_FEATURE_LOCK.json"))
        parent_receipt = json.loads(z.read("RECEIPT.json"))
    if sha(place) != PARENT_SHA or parent_receipt.get("official_rc_head")!=BASE or not parent_receipt.get("private_only"):
        raise ValueError("STAGED_PARENT_DRIFT")
    originals=verify(place,lock,feature)
    if lock["blobs"].get(GAME)!=GAME_BLOB or lock["blobs"].get(BOT)!=BOT_BLOB:
        raise ValueError("UNEXPECTED_ORIGINAL_GAME_OR_BOT_BLOB")
    tree,scripts=extract(place)
    game,bot=patch(originals["Game"].text, originals["SoloTeamBots"].text)
    scripts["Game"].text=game
    scripts["SoloTeamBots"].text=bot
    placed=ET.tostring(tree,encoding="utf-8")
    after=extract(placed)[1]
    if len(after)!=82 or any(
        after[n].text!=originals[n].text
        for n in originals if n not in ("Game","SoloTeamBots")
    ):
        raise ValueError("80_OTHER_SOURCE_BODY_DRIFT")
    lock["blobs"][GAME]=feature["source_gitblobs"][GAME]=blob(game)
    lock["blobs"][BOT]=feature["source_gitblobs"][BOT]=blob(bot)
    verify(placed,lock,feature)
    report={
        "schema":"P0D_FB005_SOLO_AI_NEUTRAL_SPECTATOR_TARGET_GUARD_V1",
        "official_rc_head":BASE,"official_rc_write":False,
        "parent_place_sha256":PARENT_SHA,
        "place_sha256":sha(placed),"place_bytes":len(placed),
        "new_game_blob":blob(game),"new_bot_blob":blob(bot),
        "scripts":82,"unchanged_parent_scripts":80,
        "egg_score_winner_source_exact":True,
        "source_lock_exact":True,
        "private_only":True,"default_off":True,
        "neutral_team_excluded":True,
        "late_spectator_excluded":True,
        "double_server_damage_guard":True,
        "native":"NOT_RUN","rojo":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN",
        "product":"NO_GO","owner":False
    }
    with ZipFile(output,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT,placed)
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
    args=p.parse_args()
    print(json.dumps(build(args.parent,args.out,args.extract),ensure_ascii=False,indent=2))
