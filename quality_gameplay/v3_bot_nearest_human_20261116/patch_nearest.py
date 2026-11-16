#!/usr/bin/env python3
"""One-source selected BotActors melee target-order fairness patch.

Input is original #484 AI BotActors after the pinned #531 current-session fence.
No new AI, Game, Combat, Swarm, score, UI, remote or economy authority.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

ORIGINAL_AI_GIT_BLOB = "832a26c9f713012b924234ce4cf8c1654a75654e"
MEMBER_BEFORE = '  if pc and pc.alive and pc.id~=my.id and (session.mode~="TEAM" or pc.team~=my.team) then'
MEMBER_AFTER = ('  if pc and pc.alive and pc.id~=my.id\n'
                '   and session.isCurrentHuman~=nil and session.isCurrentHuman(player)\n'
                '   and (session.mode~="TEAM" or pc.team~=my.team) then')
START = " -- Bot-vs-human combat actually checks spatial distance and humanoid health.\n"
END = " -- Enemy moving AI heroes must fight one another in bot-filled matches, too.\n"

REPLACEMENT = """  -- Choose the nearest *eligible* human within the same current match.
  -- Enumeration order from Players:GetPlayers() is not combat priority.
  -- Retain the original short range, wall LOS, stealth and membership gates.
  local nearestHumanoid:Humanoid?=nil
  local nearestDistance=11
  for _,player in ipairs(Players:GetPlayers()) do
   local pc=session.rules.castles[tostring(player.UserId)]
   if pc and pc.alive and pc.id~=my.id
    and session.isCurrentHuman~=nil and session.isCurrentHuman(player)
    and (session.mode~="TEAM" or pc.team~=my.team) then
    local character=player.Character
    local root=character and character:FindFirstChild("HumanoidRootPart")::BasePart?
    local h=character and character:FindFirstChildOfClass("Humanoid")
    local distance=if root then (root.Position-at).Magnitude else math.huge
    if character and root and h and h.Health>0 and distance<nearestDistance
     and os.clock()>=(player:GetAttribute("EGGRUMBLE_StealthUntil") or 0)
     and clearHeroStrike(actor,character,at+Vector3.new(0,1.5,0),root.Position+Vector3.new(0,1,0)) then
     nearestDistance=distance
     nearestHumanoid=h
    end
   end
  end
  if nearestHumanoid then
   lastHit[my.id]=now
   nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)
   return true
  end
"""

def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def original_member_overlay(ai_original: bytes) -> bytes:
    if git_blob(ai_original) != ORIGINAL_AI_GIT_BLOB:
        raise ValueError("RED original #484 AI blob drift")
    source = ai_original.decode("utf-8")
    if source.count(MEMBER_BEFORE) != 1 or MEMBER_AFTER in source:
        raise ValueError("RED existing #531 human membership insertion point")
    return source.replace(MEMBER_BEFORE, MEMBER_AFTER, 1).encode("utf-8")

def apply(bot_source: bytes) -> tuple[bytes, bytes]:
    bot = bot_source.decode("utf-8")
    if bot.count(MEMBER_AFTER) != 1 or bot.count(MEMBER_BEFORE):
        raise ValueError("RED missing or doubled existing #531 membership")
    unwrapped = bot.replace(MEMBER_AFTER, MEMBER_BEFORE, 1).encode("utf-8")
    if git_blob(unwrapped) != ORIGINAL_AI_GIT_BLOB:
        raise ValueError("RED current #531 bot is not derived from exact #484 AI author")
    if bot.count(START) != 1 or bot.count(END) != 1:
        raise ValueError("RED unique human BotActors melee span missing")
    a = bot.index(START)
    b = bot.index(END)
    if a >= b:
        raise ValueError("RED ordered human/bot melee boundaries")
    old = bot[a:b]
    for anchor in ("for _,player in ipairs(Players:GetPlayers())",
                   "session.isCurrentHuman(player)", "h:TakeDamage(BOT_HERO_DAMAGE)",
                   "lastHit[my.id]=now", "clearHeroStrike(actor,character",
                   'os.clock()>=(player:GetAttribute("EGGRUMBLE_StealthUntil") or 0)'):
        if old.count(anchor) != 1:
            raise ValueError("RED source behavior changed: " + anchor)
    if old.count("return true") != 1 or "for targetId,targetActor in pairs(bots)" not in bot[b:]:
        raise ValueError("RED bot-to-bot fallback altered")
    if REPLACEMENT in bot:
        raise ValueError("RED duplicate nearest-target overlay")
    patched = bot[:a] + REPLACEMENT + bot[b:]
    if patched.replace(REPLACEMENT, old, 1) != bot:
        raise AssertionError("RED patch not exactly reversible")
    if patched.count("nearestHumanoid:TakeDamage(BOT_HERO_DAMAGE)") != 1:
        raise AssertionError("RED single melee damage authority")
    if patched.count("targetHumanoid:TakeDamage(BOT_HERO_DAMAGE)") != 1:
        raise AssertionError("RED original bot-versus-bot hit was lost")
    return patched.encode("utf-8"), bot_source

def main() -> None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--bot-source",required=True,type=Path)
    ap.add_argument("--out-dir",required=True,type=Path)
    args=ap.parse_args()
    result,off=apply(args.bot_source.read_bytes())
    args.out_dir.mkdir(parents=True,exist_ok=True)
    (args.out_dir/"EGGRUMBLE_BotActors.luau").write_bytes(result)
    (args.out_dir/"EGGRUMBLE_BotActors.OFF.luau").write_bytes(off)
    print("GQ_BOT_NEAREST_SOURCE_LOCK_PASS ON="+hashlib.sha256(result).hexdigest()
          +" OFF="+hashlib.sha256(off).hexdigest()
          +" ORIGINAL="+ORIGINAL_AI_GIT_BLOB)

if __name__=="__main__":
    main()
