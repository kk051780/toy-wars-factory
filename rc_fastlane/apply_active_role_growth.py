"""Mount the fixed #219 WARRIOR-001 gameplay path on selected rich51."""

import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources


PACKAGE = Path(__file__).resolve().parent / "features/active_role_growth"
GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
HORDE = "server/MusouHorde.luau"
FEATURE = "GQ219_WARRIOR_001_ACTIVE_GROWTH_V1"
GROWTH = "server/MatchRoleGrowth.luau"
TIME = "server/TimePremiumRules.luau"

EDITS = {
    GAME: [
        ('''local SevenJobs = require(script.Parent:WaitForChild("SevenJobsRules"))
SevenJobs.Undead''',
         '''local SevenJobs = require(script.Parent:WaitForChild("SevenJobsRules"))
SevenJobs.Growth = require(script.Parent:WaitForChild("MatchRoleGrowth"))
SevenJobs.GrowthStates = {}
SevenJobs.Undead'''),
        ('''-- ONLY Server Game confirms objective events.''',
         '''function SevenJobs.growthEnabled()
    return RunService:IsStudio()
        and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false
        and ServerStorage:GetAttribute("P0D_RC_ENABLE_MATCH_ROLE_GROWTH")~=false
end

function SevenJobs.activeGrowth(player: Player)
    if match.phase~="ACTIVE" or not SevenJobs.growthEnabled()
        or player.Parent~=Players or player:GetAttribute("P0D_LateJoinSpectator")==true
        or getTeamName(player)=="NONE" then return nil end
    local state=SevenJobs.GrowthStates[player]
    return if state and state.round==match.serial then state else nil
end

function SevenJobs.halfMoonReady(player: Player, state, now: number): boolean
    if not state or not SevenJobs.Growth.hasCurrentSample(state,now,player.Character) then return false end
    local alive,root=healthy(player)
    return alive and root~=nil and SevenJobs.Growth.insideArena(root.Position)
end

function SevenJobs.markGrowthActivity(player: Player)
    local state=SevenJobs.activeGrowth(player)
    if not state then return end
    local alive,root=healthy(player)
    if alive and root and SevenJobs.Growth.insideArena(root.Position) then
        SevenJobs.Growth.markAction(state,match.serial,serverNow(),player.Character)
    end
end
-- ONLY Server Game confirms objective events.'''),
        ('''    if Progression.recordEvent(round,eventId,kind,true) then
        table.insert(progressionEvents[player]''',
         '''    if Progression.recordEvent(round,eventId,kind,true) then
        SevenJobs.markGrowthActivity(player)
        table.insert(progressionEvents[player]'''),
        ('''    local projectedMode,voteClassic,voteFive,scoreAllowed=modeVoteSnapshot()
    return {''',
         '''    local projectedMode,voteClassic,voteFive,scoreAllowed=modeVoteSnapshot()
    local growth=SevenJobs.activeGrowth(player)
    local halfMoonSelected=match.phase=="ACTIVE" and SevenJobs.growthEnabled()
        and sevenJobs[player]=="WARRIOR" and (sevenJobLastChoose[player] or -math.huge)>-math.huge
    local halfMoon=if halfMoonSelected and SevenJobs.halfMoonReady(player,growth,now) then growth else nil
    local jobCooldown=math.max(0,math.ceil((sevenJobLastUse[player] or -math.huge)
        +SevenJobs.DETAILS[sevenJobs[player] or "WARRIOR"].cooldown-now))
    return {'''),
        ('''        jobCooldown = math.max(0, math.ceil((sevenJobLastUse[player] or -math.huge)
            + SevenJobs.DETAILS[sevenJobs[player] or "WARRIOR"].cooldown - now)),''',
         '''        roleHalfMoon = halfMoonSelected,
        roleGrowthStage = if growth and (not halfMoonSelected or halfMoon~=nil) then SevenJobs.Growth.stage(growth) else nil,
        roleEnergy = if halfMoon then math.floor(halfMoon.energy) else nil,
        jobCooldown = if halfMoon then math.max(jobCooldown,SevenJobs.Growth.cooldown(halfMoon,now)) else jobCooldown,'''),
        ('''local function resetRound()
    for _,p in ipairs(Players:GetPlayers()) do SevenJobs.Undead.clear(p) end''',
         '''local function resetRound()
    table.clear(SevenJobs.GrowthStates)
    for _,p in ipairs(Players:GetPlayers()) do SevenJobs.Undead.clear(p) end'''),
        ('''    if match.phase~="ACTIVE" or match.serial~=startupSerial then return end
    -- All previous epoch egg carriers''',
         '''    if match.phase~="ACTIVE" or match.serial~=startupSerial then return end
    if SevenJobs.growthEnabled() then
        for _,p in ipairs(eligibleSoloPlayers()) do
            SevenJobs.GrowthStates[p]=SevenJobs.Growth.new(startupSerial)
        end
    end
    -- All previous epoch egg carriers'''),
        ('''    local function attackResponse(status:string,target:string)
        remote:FireClient''',
         '''    local function attackResponse(status:string,target:string)
        if status=="HIT" then SevenJobs.markGrowthActivity(player) end
        remote:FireClient'''),
        ('''local function sevenJobStrike(player:Player,source:Vector3,dir:Vector3,damage:number):number
    local hits,kos=horde:hit(source,dir,damage,serverNow(),player.Character)
    if hits>0 then''',
         '''local function sevenJobStrike(player:Player,source:Vector3,dir:Vector3,damage:number,
        reach:number?,targetLimit:number?,qualifiesForGrowth:boolean?):number
    local hits,kos=horde:hit(source,dir,damage,serverNow(),player.Character,reach,targetLimit)
    if hits>0 then
        if qualifiesForGrowth~=false then SevenJobs.markGrowthActivity(player) end'''),
        ('''        sevenJobStrike(player,root.Position,dir,damage)
        sevenJobFlash(root.Position+dir*5,job,4,.40)''',
         '''        sevenJobStrike(player,root.Position,dir,damage,nil,nil,false)
        sevenJobFlash(root.Position+dir*5,job,4,.40)'''),
        ('''    sevenJobLastUse[player]=now
    local spec=SevenJobs.DETAILS[job]
    local castPos''',
         '''    local growth=SevenJobs.activeGrowth(player)
    local halfMoonRange,halfMoonTargets
    if SevenJobs.growthEnabled() and job=="WARRIOR" and (sevenJobLastChoose[player] or -math.huge)>-math.huge then
        if not growth or not SevenJobs.halfMoonReady(player,growth,now) then return end
        halfMoonRange,halfMoonTargets=SevenJobs.Growth.tryHalfMoon(growth,match.serial,now)
        if not halfMoonRange or not halfMoonTargets then return end
    end
    sevenJobLastUse[player]=now
    local spec=SevenJobs.DETAILS[job]
    local castPos'''),
        ('''    if job=="WARRIOR" then
        sevenJobStrike(player,root.Position,facing,40)
    elseif job=="MAGE"''',
         '''    if job=="WARRIOR" then
        sevenJobStrike(player,root.Position,facing,40,halfMoonRange,halfMoonTargets)
    elseif job=="MAGE"'''),
        ('''                return sevenJobStrike(player,position,direction,damage)
            end,''',
         '''                return sevenJobStrike(player,position,direction,damage,nil,nil,false)
            end,'''),
        ('''    SevenJobs.Undead.clear(player)
    lastFreeHatch[player]=nil''',
         '''    SevenJobs.Undead.clear(player)
    SevenJobs.GrowthStates[player]=nil
    lastFreeHatch[player]=nil'''),
        ('''    -- Same original Game authority: canonical six-skill Store update (30s batches).
    v4TickCanonical()''',
         '''    -- Match growth samples the same server tick and the exact joined roster.
    for player,state in pairs(SevenJobs.GrowthStates) do
        local alive,root,hum=healthy(player)
        if SevenJobs.activeGrowth(player) and alive and root and hum then
            SevenJobs.Growth.sample(state,match.serial,now,player.Character,root.Position,hum.WalkSpeed)
        else
            SevenJobs.Growth.pause(state)
        end
    end
    -- Same original Game authority: canonical six-skill Store update (30s batches).
    v4TickCanonical()'''),
    ],
    HORDE: [
        ('''function Horde:hit(origin: Vector3,facing: Vector3,damage: number,now: number,ignore: Instance?): (number,number)
    if self.round<0 then return 0,0 end''',
         '''function Horde:hit(origin: Vector3,facing: Vector3,damage: number,now: number,ignore: Instance?,
        reach: number?,targetLimit: number?): (number,number)
    if self.round<0 then return 0,0 end
    local maximumReach=if reach then math.clamp(reach,0,Combat.SWEEP_RANGE) else Combat.SWEEP_RANGE
    local maximumTargets=if targetLimit then math.clamp(math.floor(targetLimit),0,6) else 6'''),
        ('''        if m.hp>0 and touched<6 then''','''        if m.hp>0 and touched<maximumTargets then'''),
        ('''            if Combat.canSweep(dist,vertical,facingDot,true) then''',
         '''            if dist<=maximumReach and Combat.canSweep(dist,vertical,facingDot,true) then'''),
    ],
    HUD: [
        ('''    jobCast.Active=jobCast.Visible and jobCd==0 and not currentNetBound
        and (type(s.carrying)~="string" or s.carrying=="")''',
         '''    local halfMoon=s.roleHalfMoon==true and picked=="WARRIOR"
    local enoughEnergy=not halfMoon or type(s.roleEnergy)=="number" and s.roleEnergy>=30
    jobCast.Active=jobCast.Visible and jobCd==0 and not currentNetBound and enoughEnergy
        and (type(s.carrying)~="string" or s.carrying=="")'''),
        ('''    jobCast.Text=if jobCd>0 then "あと"..tostring(jobCd).."秒"
        else jobSkillName[picked].."\\nQキー"''',
         '''    jobCast.Text=if jobCd>0 then "あと"..tostring(jobCd).."秒"
        elseif halfMoon then
            if type(s.roleGrowthStage)=="number" and type(s.roleEnergy)=="number" then
                "半月斬 S"..tostring(math.clamp(math.floor(s.roleGrowthStage),0,4))
                    .."\\nQ  E"..tostring(math.clamp(math.floor(s.roleEnergy),0,100))
            else "半月斬\\n準備中"
        else jobSkillName[picked].."\\nQキー"'''),
    ],
}


def apply(dist, profile="rich51", enabled_override=None):
    if profile != "rich51":
        return False
    pins = json.loads((PACKAGE / "source_lock.json").read_bytes())
    enabled = pins["enabled"] if enabled_override is None else enabled_override
    assert type(enabled) is bool and pins["profile"] == profile and pins["feature"] == FEATURE
    if not enabled:
        return False
    before = sources(dist)
    hashes = {name: gitblob(raw) for name, raw in before.items()}
    last = json.loads((dist / "SOURCE_LOCK.json").read_bytes())
    features = json.loads((dist / "RC_FEATURE_LOCK.json").read_bytes())
    assert len(hashes) == 69 and hashes == last["blobs"] == features["source_gitblobs"]
    routes = pins["routes"]
    assert set(routes) == {GAME, HUD, HORDE, GROWTH, TIME}
    assert all(hashes.get(name) == info["before"] for name, info in routes.items())
    assert last["rc_active_assassin_wind"]["routes"][GAME]["after"] == hashes[GAME]
    assert last["rc_active_touch_attack"]["after"] == hashes[HUD]
    after = {name: patch(before[name].decode("utf-8"), [
        {"anchor": anchor, "replace": replacement} for anchor, replacement in rows
    ]).encode("utf-8") for name, rows in EDITS.items()}
    after.update({name: (PACKAGE / Path(name).name).read_bytes() for name in (GROWTH, TIME)})
    assert gitblob(after[TIME]) == pins["source_origin"]["natural_growth_blob"]
    assert all(gitblob(raw) == routes[name]["after"] for name, raw in after.items())
    for name, raw in after.items():
        (dist / "src" / name).write_bytes(raw)
    assert sources(dist) == before | after
    current = hashes | {name: gitblob(raw) for name, raw in after.items()}
    receipt = {"feature": FEATURE,"engine": "NOT_TESTED","profile":profile,"studio_selected_role_only":True,
               "routes": routes,"source_origin":pins["source_origin"],"off_place":pins["off_place"]}
    last.update(total_scripts=len(current), blobs=current, rc_active_role_growth=receipt)
    features.update(total_sources=len(current), source_gitblobs=current, rc_active_role_growth=receipt)
    write_json(dist / "SOURCE_LOCK.json", last)
    write_json(dist / "RC_FEATURE_LOCK.json", features)
    print(json.dumps(receipt))
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile",choices=("rich51","rich47","legacy21"),required=True)
    parser.add_argument("--off-place",type=Path)
    args=parser.parse_args()
    pins=json.loads((PACKAGE/"source_lock.json").read_bytes())
    if args.profile==pins["profile"] and pins["enabled"] is True:
        if args.off_place is None:
            parser.error("--off-place required for enabled rich51")
        raw=args.off_place.read_bytes()
        assert {"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest()}==pins["off_place"]
        print("ACTIVE_ROLE_GROWTH_IMMEDIATE_OFF_EXACT")
    apply(args.dist,args.profile)
