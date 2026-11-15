#!/usr/bin/env python3
"""#470 P0D v2: real castle clock sync and carried-egg AI breakout.

Parent is the exact source-verified RC84 siege private Place. Changes ONLY
MapBuilder and SoloTeamBots; original 82 other script bodies stay exact.
No second match authority, extra Remote, official RC/main merge or publishing.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET
import build_siege_bot_breach_private84 as parent

PARENT="P0D_RC84_CASTLE_SIEGE_AI_BREACH_7WEAPONS_BEAST_SOLO_TRAPPER_PRIVATE.rbxlx"
PARENT_SHA="f032f8bc3f891521a1de49b8b1ce3e8701bdd8f32784f162f1ec3ced234109e5"
PARENT_MAP_BLOB="3b26e5df48f60f6071b2238097d4412928d42004"
PARENT_BOT_BLOB="0c55600c8c1e84c393b85542bbb1d33c22c72bc4"
OUTPUT="P0D_RC84_SIEGE_EGG_CARRIER_ESCAPE_CLOCK_SAFE_PRIVATE.rbxlx"
RC="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
EXPECTED_PLACE_SHA=""
EXPECTED_PLACE_BYTES=0
EXPECTED_MAP_BLOB=""
EXPECTED_BOT_BLOB=""

def once(s,old,new,label):
    if s.count(old)!=1 or new in s:
        raise ValueError("SIEGE_V2_SOURCE_ANCHOR_DRIFT_"+label)
    return s.replace(old,new,1)

def patch_map(s):
    # Bot tick comes from Game.serverNow(): workspace:GetServerTimeNow().
    # Human gate control accidentally used os.clock(), leaving breachLock at
    # epoch-sized seconds after an NPC breakout, permanently preventing reclose.
    s=once(s,"        local now=os.clock()\n        if now-lastCommand<1.25 then return end",
        "        -- FB-CASTLE-CLOCK: same server clock as Bot.tick and Game.\n"
        "        -- Never compare os.clock uptime with Unix server timestamps.\n"
        "        local now=workspace:GetServerTimeNow()\n"
        "        if now-lastCommand<1.25 then return end","CLOCK_SINGLE_DOMAIN")
    old='''    local function npcBreach(attackerTeam,botOrigin,now)
        if not pilotAllowed() or opened or not gate.Parent
            or type(now)~="number" or now~=now
            or typeof(botOrigin)~="Vector3" then return false end
        if attackerTeam==name
            or (attackerTeam~="RED" and attackerTeam~="BLUE") then return false end
        if now-lastSiegeAt<1.5 then return false end
        -- Distance is horizontal: gate collision should not depend on
        -- tall door height, and only bots outside the 16-stud entrance may hit.
        local enemySign=if name=="RED" then -1 else 1
        if (botOrigin.X-(x-enemySign*7))*enemySign>3 then return false end
        local dx=botOrigin.X-x
        local dz=botOrigin.Z
        if dx*dx+dz*dz>13*13 or botOrigin.Y < -2
            or botOrigin.Y>16 then return false end'''
    new='''    local function npcBreach(attackerTeam,botOrigin,now,fromInside)
        if not pilotAllowed() or opened or not gate.Parent
            or type(now)~="number" or now~=now
            or typeof(botOrigin)~="Vector3"
            or type(fromInside)~="boolean" then return false end
        if attackerTeam==name
            or (attackerTeam~="RED" and attackerTeam~="BLUE") then return false end
        if now-lastSiegeAt<1.5 then return false end
        -- A Raider without an egg breaches from the OUTSIDE; a real carrier
        -- of the defending team's stolen egg may break OUT from the inside.
        -- Both approaches are server-owned and require physical proximity.
        local sign=if name=="RED" then -1 else 1
        local approachX=x+(if fromInside then sign*7 else -sign*7)
        if math.abs(botOrigin.X-approachX)>4 then return false end
        local dx=botOrigin.X-x
        local dz=botOrigin.Z
        if dx*dx+dz*dz>13*13 or botOrigin.Y < -2
            or botOrigin.Y>16 then return false end'''
    s=once(s,old,new,"RAIDER_INSIDE_OUTSIDE_GATE_HIT_AUTH")
    if "local now=os.clock()" in s:
        raise ValueError("MIXED_CASTLE_CLOCK_STILL_PRESENT")
    for proof in ("lastCommand=now","breachLock=now+10","lastSiegeAt=now",
        "task.delay(9","action.Triggered:Connect","P0D_PRIVATE_SIEGE_GATES",
        "SiegeRequiredHits","SiegeDamage"):
        if proof not in s:raise ValueError("GATE_OR_SIEGE_REGRESSION_"+proof)
    return s

def patch_bots(s):
    old='''            if bot.style=="RAIDER" and not bot.carry then
                local enemyGate=map.teams[enemy].gate
                if enemyGate and enemyGate.door and enemyGate.door.Parent
                    and enemyGate.door:GetAttribute("GateRaised")==false
                    and type(enemyGate.breach)=="function"
                    and now-(bot.lastSiege or -math.huge)>=1.5 then
                    if enemyGate.breach(bot.team,bot.root.Position,now) then
                        bot.lastSiege=now
                    end
                end
            end'''
    new='''            if bot.style=="RAIDER" then
                local enemyGate=map.teams[enemy].gate
                if enemyGate and enemyGate.door and enemyGate.door.Parent
                    and enemyGate.door:GetAttribute("GateRaised")==false
                    and type(enemyGate.breach)=="function"
                    and now-(bot.lastSiege or -math.huge)>=1.5 then
                    -- Only the actual egg carrier has the interior escape route.
                    local isEscapingWithEgg=bot.carry==enemy
                    if not bot.carry or isEscapingWithEgg then
                        if enemyGate.breach(bot.team,bot.root.Position,now,
                            isEscapingWithEgg) then
                            bot.lastSiege=now
                        end
                    end
                end
            end'''
    s=once(s,old,new,"REAL_EGG_CARRIER_GATE_ESCAPE_ATTACK")
    old='''            if bot.style=="RAIDER" and not bot.carry then
                local enemyGate=map.teams[enemy].gate
                if enemyGate and enemyGate.door and enemyGate.door.Parent
                    and enemyGate.door:GetAttribute("GateRaised")==false then
                    local sign=if enemy=="RED" then -1 else 1
                    local door=enemyGate.door.Position
                    waypoint=Vector3.new(door.X-sign*7,
                        bot.root.Position.Y,door.Z)
                end
            end'''
    new='''            if bot.style=="RAIDER" then
                local enemyGate=map.teams[enemy].gate
                if enemyGate and enemyGate.door and enemyGate.door.Parent
                    and enemyGate.door:GetAttribute("GateRaised")==false
                    and (not bot.carry or bot.carry==enemy) then
                    local sign=if enemy=="RED" then -1 else 1
                    local door=enemyGate.door.Position
                    local escapingWithEgg=bot.carry==enemy
                    -- Inbound robber waits OUTSIDE (x - sign*7);
                    -- outbound egg carrier stages INSIDE (x + sign*7).
                    -- After opening, existing egg/score objective resumes.
                    waypoint=Vector3.new(
                        door.X+(if escapingWithEgg then sign*7 else -sign*7),
                        bot.root.Position.Y,door.Z)
                end
            end'''
    s=once(s,old,new,"EGG_CARRIER_EXIT_WAYPOINT")
    for proof in ("callbacks.steal(bot,enemy)",
        "callbacks.deposit(bot,bot.team,bot.carry)",
        "callbacks.drop(bot,bot.carry)",
        "PathfindingService:CreatePath(",
        "P0D_LateJoinSpectator",
        "bot.carry=enemy","bot.carry=nil","bot.lastSiege=now"):
        if proof not in s:raise ValueError("ORIGINAL_AI_OR_EGG_REGRESSION_"+proof)
    return s

def build(source,out,extract=None):
    with ZipFile(source) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(
            n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_PARENT_ARCHIVE")
        place=z.read(PARENT)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if parent.sha(place)!=PARENT_SHA or receipt.get("official_rc_head")!=RC:
        raise ValueError("NOT_EXACT_SIEGE_RC84_PARENT")
    if lock["blobs"].get(parent.MAP_PATH)!=PARENT_MAP_BLOB or lock["blobs"].get(parent.BOT_PATH)!=PARENT_BOT_BLOB:
        raise ValueError("ORIGINAL_SIEGE_V1_SOURCE_DRIFT")
    if receipt.get("official_rc_write") is not False:
        raise ValueError("UNSAFE_OFFICIAL_SOURCE_PARENT")
    old=parent.verify84(place,lock,feature)
    tree,sources=parent.source_nodes(place)
    pre={name:src.text for name,src in old.items()}
    sources["MapBuilder"].text=patch_map(pre["MapBuilder"])
    sources["SoloTeamBots"].text=patch_bots(pre["SoloTeamBots"])
    built=ET.tostring(tree,encoding="utf-8")
    _,after=parent.source_nodes(built)
    for n,src in pre.items():
        if n not in ("MapBuilder","SoloTeamBots") and after[n].text!=src:
            raise ValueError("UNRELATED_REAL_GAME_SCRIPT_CHANGED_"+n)
    map_blob=parent.blob(after["MapBuilder"].text)
    bot_blob=parent.blob(after["SoloTeamBots"].text)
    if EXPECTED_PLACE_SHA and (
        parent.sha(built)!=EXPECTED_PLACE_SHA or len(built)!=EXPECTED_PLACE_BYTES
        or map_blob!=EXPECTED_MAP_BLOB or bot_blob!=EXPECTED_BOT_BLOB):
        raise ValueError("SIEGE_V2_EXACT_PLACE_OR_SOURCE_DRIFT")
    lock["blobs"][parent.MAP_PATH]=feature["source_gitblobs"][parent.MAP_PATH]=map_blob
    lock["blobs"][parent.BOT_PATH]=feature["source_gitblobs"][parent.BOT_PATH]=bot_blob
    parent.verify84(built,lock,feature)
    result={
      "schema":"P0D_FB_CASTLE_AI_EGG_CARRIER_EXIT_AND_CLOCK_V2",
      "official_rc_head":RC,"official_rc_write":False,
      "parent_place_sha256":PARENT_SHA,
      "place_sha256":parent.sha(built),"place_bytes":len(built),
      "map_builder_blob":map_blob,"solo_bots_blob":bot_blob,
      "script_count":84,"other_82_script_bodies_byte_exact":True,
      "one_server_clock_for_manual_and_bot_breach":True,
      "carrier_breakout_while_egg_held":True,
      "three_real_gate_hits":True,"original_egg_score_winner_exact":True,
      "source_dual_lock_exact":True,"private_default_off":True,
      "native":"NOT_RUN","rojo":"NOT_RUN",
      "studio":"NOT_RUN","android":"NOT_RUN","owner":False,
      "product":"NO_GO"
    }
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT,built)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    if extract:
        extract.mkdir(parents=True,exist_ok=True)
        for n,node in after.items():
            (extract/(n+".luau")).write_text(node.text,encoding="utf-8")
    return result

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.parent,a.out,a.extract),ensure_ascii=False,indent=2))
