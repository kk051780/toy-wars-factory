#!/usr/bin/env python3
"""#470 source-exact composition: original #297 selected READY repair + adaptive wind.

Quality stage only. No authorized RC deployment, engine claims or additional Game.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZIP_DEFLATED

GAME = "server/Game.server.luau"
WIND = "server/S1RaiderWindRules.luau"
HUD = "client/HUD.client.luau"
HEAD = "d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
AUTHOR_PLACE_SHA = "66204b3a25ca61af16fc9b21638906e88b300727a0987dd0a1f19fcd960157d0"
AUTHOR_GAME_BLOB = "eea411befa2c7986d463eef29e28636eb2d02f08"
AUTHOR_HUD_BLOB = "4e3c9d8f3a1064e5387f3fb9ccbd08e3d7499af0"
WIND_BASE_BLOB = "7d5706774b874759e7ab994dc0654c3ae9a46502"
EXPECTED_GAME_BLOB = "a12dc933c7e80b94d1423e04d8273a2bbcaa7830"
EXPECTED_WIND_BLOB = "d66efccbf90028627cd65aa0fb33173506819c11"
EXPECTED_PLACE_SHA = "8d26ec3526527a3fd014935423ca263166b07a77fb5ba92508178c4ef5382d19"

GAME_BEFORE = "    if not WindRules.canActivate({\n        phase = match.phase, team = team, role = roles[player] or \"RAIDER\",\n        alive = alive, carrying = carry[player] ~= nil, slowed = slowed[player] ~= nil,\n        active = (windUntil[player] or 0) > now, now = now,\n        lastAt = lastWind[player] or -math.huge,\n        x = root.Position.X, y = root.Position.Y, z = root.Position.Z,\n    }) then return end"
GAME_AFTER = "    local windInput:any = {\n        phase = match.phase, team = team, role = roles[player] or \"RAIDER\",\n        alive = alive, carrying = carry[player] ~= nil, slowed = slowed[player] ~= nil,\n        active = (windUntil[player] or 0) > now, now = now,\n        lastAt = lastWind[player] or -math.huge,\n        x = root.Position.X, y = root.Position.Y, z = root.Position.Z,\n    }\n    -- FB004 quality: exact live floor size. Default OFF keeps official behavior.\n    if ServerStorage:GetAttribute(\"P0D_ADAPTIVE_WIND_FIELD\") == true then\n        local grass=map.model:FindFirstChild(\"GrassArena\")\n        if not grass or not grass:IsA(\"BasePart\") or not grass.Anchored\n            or not grass.CanCollide or grass.Parent~=map.model then return end\n        local localPosition=grass.CFrame:PointToObjectSpace(root.Position)\n        windInput.adaptiveField=true\n        windInput.arenaX=localPosition.X\n        windInput.arenaZ=localPosition.Z\n        windInput.arenaMaxX=math.min(178,grass.Size.X*.5-5)\n        windInput.arenaMaxZ=math.min(140,grass.Size.Z*.5-6)\n    end\n    if not WindRules.canActivate(windInput) then return end"
WIND_BEFORE = "    -- Only ordinary walkable ground in current S1 arena; no sky-flight speed exploit.\n    if math.abs(s.x) > 120 or math.abs(s.z) > 65 or s.y < 1 or s.y > 12 then\n        return false\n    end"
WIND_AFTER = "    -- OFF: preserve old official default 120/65, no new permission in public.\n    -- ON: caller supplies ONLY server-derived GrassArena geometry, not client fields.\n    local limitX,limitZ=120,65\n    local xx,zz=s.x,s.z\n    if s.adaptiveField == true then\n        if not finite(s.arenaX) or not finite(s.arenaZ)\n            or not finite(s.arenaMaxX) or not finite(s.arenaMaxZ)\n            or s.arenaMaxX < 16 or s.arenaMaxZ < 16\n            or s.arenaMaxX > 178 or s.arenaMaxZ > 140 then return false end\n        limitX,limitZ=s.arenaMaxX,s.arenaMaxZ\n        xx,zz=s.arenaX,s.arenaZ\n        -- Hard ceiling inside original server ACTIVE out-of-bounds return (182/144).\n        if math.abs(s.x) > 178 or math.abs(s.z) > 140 then return false end\n    elseif s.adaptiveField ~= nil then\n        return false\n    end\n    if math.abs(xx) > limitX or math.abs(zz) > limitZ or s.y < 1 or s.y > 12 then\n        return false\n    end"

# FB-004 / FB-008: real Q impacts must obey the same expiring 2.4s
# combo window as ordinary ATTACK, not carry an expired chain forever.
Q_COMBO_BEFORE = """    local hits,kos=horde:hit(source,dir,damage,serverNow(),player.Character)
    if hits>0 then
        mobCombo[player]=math.min(99,(mobCombo[player] or 0)+hits)
        mobComboUntil[player]=serverNow()+2.4"""
Q_COMBO_AFTER = """    local hitNow=serverNow()
    local hits,kos=horde:hit(source,dir,damage,hitNow,player.Character)
    if hits>0 then
        -- Match ATTACK's 2.4s combo chain; expired Q hits restart the chain.
        mobCombo[player]=if hitNow<(mobComboUntil[player] or 0)
            then math.min(99,(mobCombo[player] or 0)+hits) else hits
        mobComboUntil[player]=hitNow+2.4"""
# Delayed Q must not hit after team rebalance or same-role reselection.
Q_DELAY_BEFORE = """local function sevenJobDelayedStrike(player:Player,job:string,serial:number,
        origin:Vector3,dir:Vector3,damage:number,delaySeconds:number)
    task.delay(delaySeconds,function()
        if ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")==false
            or match.phase~="ACTIVE" or match.serial~=serial
            or player.Parent~=Players or sevenJobs[player]~=job
            or carry[player]~=nil or slowed[player]~=nil then return end"""
Q_DELAY_AFTER = """local function sevenJobDelayedStrike(player:Player,job:string,serial:number,
        origin:Vector3,dir:Vector3,damage:number,delaySeconds:number)
    local selectedAck=sevenJobPickAckSeq[player]
    task.delay(delaySeconds,function()
        if ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")==false
            or match.phase~="ACTIVE" or match.serial~=serial
            or player.Parent~=Players or sevenJobs[player]~=job
            -- Reject delayed hit after role is revoked or re-picked (even same role).
            or sevenJobSelected[player]~=true
            or sevenJobPickAckSeq[player]~=selectedAck
            or carry[player]~=nil or slowed[player]~=nil then return end"""

def sha(data):
    return hashlib.sha256(data).hexdigest()

def blob(source):
    data=source.encode("utf-8")
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def get_sources(xml):
    root=ET.fromstring(xml)
    result={}
    items={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        source=props.find("string[@name='Source']")
        if name is None or source is None or source.text is None:raise ValueError("MISSING_SCRIPT_DATA")
        if name in result:raise ValueError("DUPLICATE_SCRIPT:"+name)
        result[name]=source.text
        items[name]=source
    return root,result,items

def assert_locked(xml,source_lock,feature_lock):
    root,sources,items=get_sources(xml)
    if (len(sources)!=82 or source_lock.get("total_scripts")!=82
        or feature_lock.get("total_sources")!=82):
        raise ValueError("SOURCE_COUNT_DRIFT")
    locks=source_lock.get("blobs")
    if not isinstance(locks,dict) or locks!=feature_lock.get("source_gitblobs"):
        raise ValueError("DUAL_LOCK_MISMATCH")
    if Counter(blob(s) for s in sources.values())!=Counter(locks.values()):
        raise ValueError("ACTUAL_PLACE_SOURCE_LOCK_MISMATCH")
    return root,sources,items


# FB004 observer/Horde source-selective fix on the ORIGINAL author's real Game.
# No second Remote, AI, health, score or gameplay authority. Source-drift FAIL.
def apply_spectator_horde_fix(game: str) -> str:
    changes = [
        (
            '    if RunService:IsStudio() and\n        (match.phase=="ACTIVE" or match.phase=="COUNTDOWN") then\n        player.Team=nil',
            '    if (RunService:IsStudio() or privateHordeTrialAllowed()) and\n        (match.phase=="ACTIVE" or match.phase=="COUNTDOWN") then\n        player.Team=nil',
        ),
        (
            '    if match.phase == "LOBBY" then\n        if RunService:IsStudio() then\n            for _,entrant in ipairs(Players:GetPlayers()) do',
            '    if match.phase == "LOBBY" then\n        if RunService:IsStudio() or privateHordeTrialAllowed()\n'
            '            or #eligibleSoloPlayers() < #Players:GetPlayers() then\n'
            '            for _,entrant in ipairs(Players:GetPlayers()) do',
        ),
        (
            '                        root.CFrame=LobbyIsland.spawn(getTeamName(entrant))\n                    else\n                        scheduleLobbyRecovery(entrant)',
            '                        root.CFrame=if RunService:IsStudio()\n'
            '                            then LobbyIsland.spawn(getTeamName(entrant))\n'
            '                            else map.teams[getTeamName(entrant)].spawn + Vector3.new(0,2,0)\n'
            '                    else\n                        scheduleLobbyRecovery(entrant)',
        ),
        (
            'horde:tick(now,Players:GetPlayers(),healthy)',
            'horde:tick(now,eligibleSoloPlayers(),healthy)',
        ),
        (
            '            if ok and hum and victimRoot and now>=(invulnUntil[victim] or 0) then',
            '            if ok and hum and victimRoot\n'
            '                and victim:GetAttribute("P0D_LateJoinSpectator")~=true\n'
            '                and (getTeamName(victim)=="RED" or getTeamName(victim)=="BLUE")\n'
            '                and now>=(invulnUntil[victim] or 0) then',
        ),
    ]
    for i, (before, after) in enumerate(changes, 1):
        if game.count(before) != 1:
            raise ValueError("SPECTATOR_SOURCE_DRIFT_" + str(i))
        game = game.replace(before, after, 1)
    if game.count('horde:tick(now,eligibleSoloPlayers(),healthy)') != 1:
        raise ValueError("HORDE_ELIGIBILITY_NOT_ENFORCED")
    if game.count('local function eligibleSoloPlayers(): {Player}') != 1:
        raise ValueError("SOLO_ROSTER_AUTHORITY_NOT_SINGLE")
    return game

def compose(outer_zip):
    with ZipFile(io.BytesIO(outer_zip)) as outer:
        inner=outer.read("P0D_RC82_ROLE7_READY_PRIVATE_SOURCE_PATCH.zip")
    with ZipFile(io.BytesIO(inner)) as z:
        place=z.read("PRIVATE_ROLE7_READY_RC82.rbxlx")
        sl=json.loads(z.read("SOURCE_LOCK.json"))
        fl=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if sha(place)!=AUTHOR_PLACE_SHA or receipt.get("source_rc")!=HEAD:
        raise ValueError("WRONG_ORIGINAL_AUTHOR_ARTIFACT")
    root,sources,items=assert_locked(place,sl,fl)
    for key,wanted in ((GAME,AUTHOR_GAME_BLOB),(HUD,AUTHOR_HUD_BLOB),(WIND,WIND_BASE_BLOB)):
        if sl["blobs"].get(key)!=wanted:raise ValueError("ORIGINAL_AUTHOR_DRIFT:"+key)
    if sources["Game"].count(GAME_BEFORE)!=1 or sources["S1RaiderWindRules"].count(WIND_BEFORE)!=1:
        raise ValueError("AUTHOR_PATCH_CONFLICT_WITH_WIND")
    # Reuse existing #470 Builder-Q blocked-raycast fix; no independent Game/Remote.
    # A rejected physical placement must NOT consume 18s cooldown or play success FX.
    raycast=('        local params=RaycastParams.new()\n'
             '        params.FilterType=Enum.RaycastFilterType.Exclude\n'
             '        params.FilterDescendantsInstances={player.Character :: Model,horde.folder}\n'
             '        if workspace:Raycast(root.Position,facing*9,params) then return end\n')
    safe='        if not SevenJobs.safeWall(wallCenter.X,wallCenter.Z,near) then return end\n'
    post=raycast+'        local wall=Instance.new("Part")'
    fixed_game=sources["Game"].replace(GAME_BEFORE,GAME_AFTER,1)
    if fixed_game.count(safe)!=1 or fixed_game.count(post)!=1:
        raise ValueError("BUILDER_Q_REBASE_OVERLAP_OR_DRIFT")
    fixed_game=fixed_game.replace(safe,safe+raycast,1)
    fixed_game=fixed_game.replace(post,'        local wall=Instance.new("Part")',1)
    if fixed_game.count(Q_COMBO_BEFORE)!=1 or fixed_game.count(Q_DELAY_BEFORE)!=1:
        raise ValueError("AUTHOR_Q_COMBO_OR_DELAY_GUARD_DRIFT")
    fixed_game=fixed_game.replace(Q_COMBO_BEFORE,Q_COMBO_AFTER,1)
    fixed_game=fixed_game.replace(Q_DELAY_BEFORE,Q_DELAY_AFTER,1)
    fixed_game=apply_spectator_horde_fix(fixed_game)
    job=fixed_game.index('local function useSevenJob(')
    if not (fixed_game.index(raycast,job)<fixed_game.index('    sevenJobLastUse[player]=now',job)):
        raise ValueError("BUILDER_Q_RAYCAST_AFTER_COST")
    fixed_wind=sources["S1RaiderWindRules"].replace(WIND_BEFORE,WIND_AFTER,1)
    if ('sevenJobPickAckSeq[player]~=selectedAck' not in fixed_game
        or 'mobCombo[player]=if hitNow<(mobComboUntil[player] or 0)' not in fixed_game):
        raise ValueError("COMBO_OR_ROLE_REVOKE_REPAIR_NOT_APPLIED")
    if blob(fixed_game)!=EXPECTED_GAME_BLOB or blob(fixed_wind)!=EXPECTED_WIND_BLOB:
        raise ValueError("FIXED_SOURCE_REPRODUCIBILITY_FAILURE")
    items["Game"].text=fixed_game
    items["S1RaiderWindRules"].text=fixed_wind
    out=ET.tostring(root,encoding="utf-8")
    if sha(out)!=EXPECTED_PLACE_SHA:raise ValueError("COMPOSED_PLACE_REPRODUCIBILITY_FAILURE")
    _,after,_=get_sources(out)
    for name in sources:
        if name not in ("Game","S1RaiderWindRules") and sources[name]!=after[name]:
            raise ValueError("OTHER_AUTHOR_SOURCE_CHANGED:"+name)
    if sources["TrapRaidersHUD"]!=after["TrapRaidersHUD"]:raise ValueError("HUD_NOT_PRESERVED")
    if ("sevenJobSelected[player]~=true" not in fixed_game
        or "broadcast() -- update all peers after job change" not in fixed_game
        or "sevenJobPickAckSeq" not in fixed_game
        or "pendingJobSeq" not in after["TrapRaidersHUD"]):
        raise ValueError("LATEST_ROLE7_EXACT_ACK_PATCH_REMOVED")
    sl["blobs"][GAME]=fl["source_gitblobs"][GAME]=EXPECTED_GAME_BLOB
    sl["blobs"][WIND]=fl["source_gitblobs"][WIND]=EXPECTED_WIND_BLOB
    assert_locked(out,sl,fl)
    return out,sl,fl,after

def build(outer_zip,output,extract_dir=None):
    place,sl,fl,sources=compose(outer_zip)
    with ZipFile(output,"w",ZIP_DEFLATED) as z:
        z.writestr("COMPOSED_ROLE7_WIND_RC82.rbxlx",place)
        z.writestr("SOURCE_LOCK.json",json.dumps(sl,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(fl,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps({
          "schema":"PQ_AUTHOR297_EXACT_ACK_WIND_BUILDER_Q_COMBO_SPECTATOR_V4","head":HEAD,
          "scripts":82,"unchanged_author":80,"place_bytes":len(place),
          "place_sha256":sha(place),"source_lock":True,"exact_job_pick_ack_preserved":True,
          "builder_q_false_cooldown_fixed":True,
          "q_combo_expiry_fixed":True,
          "delayed_q_stale_selection_denied":True,
          "private_latejoin_spectator":True,
          "horde_authorized_roster_only":True,
          "elite_revalidates_spectator":True,
          "spectator_re_admit_after_flag_off":True,
          "official_rc_write":False,"engine":"NOT_RUN","android":"NOT_RUN",
          "owner":False,"decision":"PRODUCT_NO_GO"},indent=2)+"\n")
    if extract_dir is not None:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for name,src in sources.items():
            (extract_dir/(name+".luau")).write_text(src,encoding="utf-8")
    return len(sources),sha(place)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--author-outer",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    args=p.parse_args()
    n,digest=build(args.author_outer.read_bytes(),args.out,args.extract)
    print("P0D_SOURCE_COMPOSITE_NO_GO",n,digest)
if __name__=="__main__":main()
