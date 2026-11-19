#!/usr/bin/env python3
"""#470: real SOLO raider siege breach of physical gates in the cumulative RC84.

ONLY original MapBuilder and SoloTeamBots source bodies change. Existing
author Game, egg/score/HP, 7-job weapons, portals, Beast, HUD and other 82 scripts
remain source-byte exact. Experimental private Place, no official RC writes.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET

PARENT_PLACE="P0D_RC84_CASTLE_BEAST_SOLO_SEVEN_WEAPONS_TRAPPER_PRIVATE.rbxlx"
PARENT_SHA="e0ebec60cb48e0fd3ed1d5fdbb50c7376f0948facc4c523e7d489ea754291ab4"
MAP_PATH="server/MapBuilder.luau"
BOT_PATH="server/SoloTeamBots.luau"
GAME_PATH="server/Game.server.luau"
PARENT_MAP_BLOB="52e677d208412483b744c7ac464eb0ffbc9e6ecd"
PARENT_BOT_BLOB="a77176fdcfe3351b5dc9ed4aa23fcf48a28edd53"
PARENT_GAME_BLOB="9b7fb4648b9b6c6b5efbc958ecdf275e46f6830d"
PARENT_TRAPPER_BLOB="61bcfea24c1ac318800b982b87dacc09c6889040"
OFFICIAL="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
OUTPUT_PLACE="P0D_RC84_CASTLE_SIEGE_AI_BREACH_7WEAPONS_BEAST_SOLO_TRAPPER_PRIVATE.rbxlx"
EXPECTED_SHA="f032f8bc3f891521a1de49b8b1ce3e8701bdd8f32784f162f1ec3ced234109e5"
EXPECTED_BYTES=818874
EXPECTED_MAP="3b26e5df48f60f6071b2238097d4412928d42004"
EXPECTED_BOT="0c55600c8c1e84c393b85542bbb1d33c22c72bc4"

def sha(raw):return hashlib.sha256(raw).hexdigest()
def blob(source):
    b=source.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def once(s,old,new,label):
    if s.count(old)!=1 or new in s:
        raise ValueError("ORIGINAL_SOURCE_DRIFT_"+label)
    return s.replace(old,new,1)

MAP_SIEGE_ORIGINAL='''    local breachLock=0
    local lastCommand=-math.huge'''
MAP_SIEGE_NEW='''    local breachLock=0
    local lastCommand=-math.huge
    -- FB-CASTLE-BOT: NPC siege requires three real hits before a breach.
    -- Each gate tracks its own state, and its defense lasts at most 9 seconds.
    local siegeDamage=0
    local lastSiegeAt=-math.huge
    gate:SetAttribute("SiegeDamage",0)
    gate:SetAttribute("SiegeRequiredHits",3)'''
MAP_SLIDE_OLD='''        opened=opening
        gate:SetAttribute("GateRaised",opening)'''
MAP_SLIDE_NEW='''        opened=opening
        -- A new closure/opening always starts with a fresh siege condition.
        siegeDamage=0
        gate:SetAttribute("SiegeDamage",siegeDamage)
        gate:SetAttribute("GateRaised",opening)'''
MAP_RETURN_OLD='''    return {door=gate,control=console,action=action}
end'''
MAP_RETURN_NEW='''    -- Only server-created enemy raiders may call this closure. The caller
    -- never controls a portal/destination, HP/egg/score or player Remote.
    local function npcBreach(attackerTeam,botOrigin,now)
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
            or botOrigin.Y>16 then return false end
        lastSiegeAt=now
        siegeDamage+=1
        gate:SetAttribute("SiegeDamage",siegeDamage)
        if siegeDamage>=3 then
            -- Breaking the door counts as a siege, never as a score/KO.
            breachLock=now+10
            lastCommand=now
            openGate()
        end
        return true
    end
    return {door=gate,control=console,action=action,breach=npcBreach}
end'''

BOT_HIT_ANCHOR='''            if not bot.carry and bot.style=="RAIDER"
                and (bot.root.Position-map.teams[enemy].egg.Position).Magnitude<=7 then'''
BOT_HIT_NEW='''            -- A real egg-raiding AI must be able to break a locked gate.
            -- This is server-only: the MapBuilder gate validates opposing
            -- team, human/AI-safe entrance distance, and global hit cadence.
            if bot.style=="RAIDER" and not bot.carry then
                local enemyGate=map.teams[enemy].gate
                if enemyGate and enemyGate.door and enemyGate.door.Parent
                    and enemyGate.door:GetAttribute("GateRaised")==false
                    and type(enemyGate.breach)=="function"
                    and now-(bot.lastSiege or -math.huge)>=1.5 then
                    if enemyGate.breach(bot.team,bot.root.Position,now) then
                        bot.lastSiege=now
                    end
                end
            end
            if not bot.carry and bot.style=="RAIDER"
                and (bot.root.Position-map.teams[enemy].egg.Position).Magnitude<=7 then'''

BOT_GOAL_ANCHOR='''            local waypoint=if bot.carry then map.teams[bot.team].scorePad.Position
                elseif bot.style=="GUARD" then map.teams[bot.team].egg.Position
                else map.teams[enemy].egg.Position
            if bot.style=="GUARD" then'''
BOT_GOAL_NEW='''            local waypoint=if bot.carry then map.teams[bot.team].scorePad.Position
                elseif bot.style=="GUARD" then map.teams[bot.team].egg.Position
                else map.teams[enemy].egg.Position
            -- A CLOSED gate changes the actual raider objective into the
            -- approach point OUTSIDE the entrance. No teleport or wall glitch.
            -- Once breach opens it, the original egg objective resumes.
            if bot.style=="RAIDER" and not bot.carry then
                local enemyGate=map.teams[enemy].gate
                if enemyGate and enemyGate.door and enemyGate.door.Parent
                    and enemyGate.door:GetAttribute("GateRaised")==false then
                    local sign=if enemy=="RED" then -1 else 1
                    local door=enemyGate.door.Position
                    waypoint=Vector3.new(door.X-sign*7,
                        bot.root.Position.Y,door.Z)
                end
            end
            if bot.style=="GUARD" then'''

def patch_map(s):
    s=once(s,MAP_SIEGE_ORIGINAL,MAP_SIEGE_NEW,"SIEGE_DAMAGE_STATE")
    s=once(s,MAP_SLIDE_OLD,MAP_SLIDE_NEW,"RESET_ON_GATE_OPEN_CLOSE")
    s=once(s,MAP_RETURN_OLD,MAP_RETURN_NEW,"SERVER_NPC_BREACH")
    for required in ("GetAttributeChangedSignal(\"P0D_PRIVATE_SIEGE_GATES\")",
        'task.delay(9','openGate()','gate:SetAttribute("GateRaised",opening)',
        'if t.Name==name then','P0D_PRIVATE_SIEGE_GATES',
        'local function npcBreach(attackerTeam,botOrigin,now)'):
        if required not in s:raise ValueError("MAP_GATE_CONTRACT_REMOVED:"+required)
    return s

def patch_bot(s):
    s=once(s,BOT_HIT_ANCHOR,BOT_HIT_NEW,"RAIDER_CAN_ATTACK_GATE")
    s=once(s,BOT_GOAL_ANCHOR,BOT_GOAL_NEW,"GO_TO_OUTSIDE_GATE_THEN_EGG")
    if s.count("enemyGate.breach(bot.team,bot.root.Position,now)")!=1:
        raise ValueError("BOT_GATE_AUTHORITY_DUPLICATED")
    for req in ("callbacks.deposit(bot,bot.team,bot.carry)",
                "callbacks.steal(bot,enemy)","callbacks.attackBot(bot,rival,6)",
                "callbacks.attackHuman(bot,player,6)",
                "P0D_LateJoinSpectator","bot.carry=nil",
                "PathfindingService:CreatePath"):
        if req not in s:raise ValueError("BOT_EGG_OR_COMBAT_REGRESSION:"+req)
    return s

def source_nodes(data):
    root=ET.fromstring(data)
    scripts={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):
            continue
        p=item.find("Properties")
        if p is None:continue
        name=p.findtext("string[@name='Name']")
        source=p.find("string[@name='Source']")
        if not name or source is None or source.text is None or name in scripts:
            raise ValueError("DUPLICATE_OR_MALFORMED_SCRIPT")
        scripts[name]=source
    return root,scripts

def verify84(data,lock,feature):
    _,scripts=source_nodes(data)
    if len(scripts)!=84 or lock.get("total_scripts")!=84 or feature.get("total_sources")!=84:
        raise ValueError("SOURCE84_COUNT_DRIFT")
    if lock.get("blobs")!=feature.get("source_gitblobs") or len(lock["blobs"])!=84:
        raise ValueError("SOURCE84_LOCK_DRIFT")
    if Counter(blob(s.text) for s in scripts.values())!=Counter(lock["blobs"].values()):
        raise ValueError("SOURCE84_BLOB_DRIFT")
    return scripts

def build(parent,out,extract=None):
    with ZipFile(parent) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(
            n.startswith("/") or ".." in Path(n).parts for n in names):
            raise ValueError("UNSAFE_PARENT_ARCHIVE")
        original=z.read(PARENT_PLACE)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        feature=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if sha(original)!=PARENT_SHA or receipt.get("official_rc_head")!=OFFICIAL:
        raise ValueError("WRONG_PARENT_PLACE_OR_OFFICIAL_SHA")
    pins={MAP_PATH:PARENT_MAP_BLOB,BOT_PATH:PARENT_BOT_BLOB,
          GAME_PATH:PARENT_GAME_BLOB,
          "server/TrapperWarpService.luau":PARENT_TRAPPER_BLOB}
    if any(lock["blobs"].get(k)!=v for k,v in pins.items()):
        raise ValueError("PARENT_CORE_SOURCE_PIN_DRIFT")
    old=verify84(original,lock,feature)
    root,sources=source_nodes(original)
    before={n:node.text for n,node in old.items()}
    sources["MapBuilder"].text=patch_map(before["MapBuilder"])
    sources["SoloTeamBots"].text=patch_bot(before["SoloTeamBots"])
    final=ET.tostring(root,encoding="utf-8")
    updated=source_nodes(final)[1]
    if any(updated[n].text!=before[n] for n in before
        if n not in ("MapBuilder","SoloTeamBots")):
        raise ValueError("82_UNRELATED_REAL_GAME_SOURCES_CHANGED")
    if EXPECTED_SHA and (sha(final)!=EXPECTED_SHA or
        len(final)!=EXPECTED_BYTES or
        blob(updated["MapBuilder"].text)!=EXPECTED_MAP or
        blob(updated["SoloTeamBots"].text)!=EXPECTED_BOT):
        raise ValueError("SIEGE_PRIVATE_PLACE_DIGEST_DRIFT")
    lock["blobs"][MAP_PATH]=feature["source_gitblobs"][MAP_PATH]=blob(updated["MapBuilder"].text)
    lock["blobs"][BOT_PATH]=feature["source_gitblobs"][BOT_PATH]=blob(updated["SoloTeamBots"].text)
    verify84(final,lock,feature)
    report={
      "schema":"P0D_FB_CASTLE_REAL_SOLO_AI_BREACH_PRIVATE_RC84_V1",
      "official_rc_head":OFFICIAL,"official_rc_write":False,
      "parent_place_sha256":PARENT_SHA,"place_sha256":sha(final),
      "place_bytes":len(final),
      "map_builder_blob":lock["blobs"][MAP_PATH],
      "solo_bots_blob":lock["blobs"][BOT_PATH],
      "game_blob_unchanged":PARENT_GAME_BLOB,
      "script_count":84,"unchanged_game_and_81_other_scripts":True,
      "source_dual_lock_exact":True,
      "egg_steal_deposit_score_winner_exact":True,
      "enemy_raider_breach_three_hits":True,
      "gate_siege_auto_open_nine_seconds_preserved":True,
      "bot_paths_to_gate_before_egg_when_closed":True,
      "private_default_off":True,"native":"NOT_RUN",
      "rojo":"NOT_RUN","studio":"NOT_RUN","android":"NOT_RUN",
      "product":"NO_GO","owner":False}
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT_PLACE,final)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,indent=2,ensure_ascii=False)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(feature,indent=2,ensure_ascii=False)+"\n")
        z.writestr("RECEIPT.json",json.dumps(report,indent=2,ensure_ascii=False)+"\n")
    if extract:
        extract.mkdir(parents=True,exist_ok=True)
        for n,node in updated.items():
            (extract/(n+".luau")).write_text(node.text,encoding="utf-8")
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.parent,a.out,a.extract),ensure_ascii=False,indent=2))
