"""Mount the fixed MAGE-041 Water Bolt on the existing active neutral authority."""
import argparse
import hashlib
import json
from pathlib import Path
import textwrap

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources

PACKAGE = Path(__file__).resolve().parent / "features/active_mage_water"
FEATURE = "GQ219_MAGE_041_ACTIVE_WATER_BOLT_V1"
GAME = "server/Game.server.luau"
HORDE = "server/MusouHorde.luau"
GROWTH = "server/MatchRoleGrowth.luau"
HUD = "client/HUD.client.luau"
WATER = "server/MageWaterCatalog.luau"

EDITS = {
    GROWTH: [
        ('''    lastCast: number,
    actionAt: number?,''',
         '''    lastCast: number,
    lastJobUse: number?,
    actionAt: number?,'''),
        ('''function Growth.cooldown(state: State, now: number): number
    return math.max(0,math.ceil(state.lastCast+CAST_COOLDOWN-now))
end

-- Ownership, current avatar, phase and the user's role selection are checked by Game.
function Growth.tryHalfMoon(state: State, round: number, now: number): (number?, number?)
    if state.round~=round or not Growth.hasCurrentSample(state,now,state.character)
        or now-state.lastCast<CAST_COOLDOWN or state.energy<CAST_ENERGY then
        return nil,nil
    end
    local index=Growth.stage(state)+1
    state.energy-=CAST_ENERGY
    state.lastCast=now
    return RANGE_BY_STAGE[index], LIMIT_BY_STAGE[index]
end''',
         '''function Growth.cooldown(state: State, now: number, cooldown: number?): number
    local last=if cooldown then math.max(state.lastCast,state.lastJobUse or -math.huge) else state.lastCast
    return math.max(0,math.ceil(last+(cooldown or CAST_COOLDOWN)-now))
end

-- Ownership, current avatar, phase and the user's role selection are checked by Game.
function Growth.tryCast(state: State, round: number, now: number, cooldown: number, energy: number): number?
    if state.round~=round or not Growth.hasCurrentSample(state,now,state.character)
        or now-state.lastCast<cooldown or state.energy<energy then return nil end
    state.energy-=energy
    state.lastCast=now
    return Growth.stage(state)
end

function Growth.tryHalfMoon(state: State, round: number, now: number): (number?, number?)
    local stage=Growth.tryCast(state,round,now,CAST_COOLDOWN,CAST_ENERGY)
    if stage==nil then return nil,nil end
    return RANGE_BY_STAGE[stage+1], LIMIT_BY_STAGE[stage+1]
end'''),
    ],
    GAME: [
        ('''SevenJobs.Armament = require(script.Parent:WaitForChild("SevenJobArmamentM1"))''',
         '''SevenJobs.Armament = require(script.Parent:WaitForChild("SevenJobArmamentM1"))
SevenJobs.Water = require(script.Parent:WaitForChild("MageWaterCatalog"))'''),
        ('''function SevenJobs.halfMoonReady(player: Player, state, now: number): boolean''',
         '''function SevenJobs.waterSelected(player: Player): boolean
    return match.phase=="ACTIVE" and SevenJobs.growthEnabled()
        and ServerStorage:GetAttribute("P0D_RC_ENABLE_MAGE_WATER_BOLT")~=false
        and player.Parent==Players and player:GetAttribute("P0D_LateJoinSpectator")~=true
        and sevenJobs[player]=="MAGE" and (sevenJobLastChoose[player] or -math.huge)>-math.huge
end

function SevenJobs.growthCastReady(player: Player, state, now: number): boolean'''),
        ('''    local halfMoon=if halfMoonSelected and SevenJobs.halfMoonReady(player,growth,now) then growth else nil
    local jobCooldown''',
         '''    local halfMoon=if halfMoonSelected and SevenJobs.growthCastReady(player,growth,now) then growth else nil
    local waterSelected=SevenJobs.waterSelected(player)
    local water=if waterSelected and SevenJobs.growthCastReady(player,growth,now) then growth else nil
    local waterTarget,waterSeconds
    if water then waterTarget,waterSeconds=horde:waterStatus(player,now) end
    local jobCooldown'''),
        ('''        roleHalfMoon = halfMoonSelected,
        roleGrowthStage = if growth and (not halfMoonSelected or halfMoon~=nil) then SevenJobs.Growth.stage(growth) else nil,
        roleEnergy = if halfMoon then math.floor(halfMoon.energy) else nil,
        jobCooldown = if halfMoon then math.max(jobCooldown,SevenJobs.Growth.cooldown(halfMoon,now)) else jobCooldown,''',
         '''        roleHalfMoon = halfMoonSelected,
        roleWaterBolt = waterSelected,
        roleWaterTarget = waterTarget,
        roleWaterSeconds = waterSeconds,
        roleGrowthStage = if growth and ((not halfMoonSelected and not waterSelected)
            or halfMoon~=nil or water~=nil) then SevenJobs.Growth.stage(growth) else nil,
        roleEnergy = if halfMoon or water then math.floor((halfMoon or water).energy) else nil,
        jobCooldown = if water then SevenJobs.Growth.cooldown(water,now,SevenJobs.Water.cd)
            elseif halfMoon then math.max(jobCooldown,SevenJobs.Growth.cooldown(halfMoon,now)) else jobCooldown,'''),
        ('''        reach:number?,targetLimit:number?,qualifiesForGrowth:boolean?):number
    local hits,kos=horde:hit(source,dir,damage,serverNow(),player.Character,reach,targetLimit)''',
         '''        reach:number?,targetLimit:number?,qualifiesForGrowth:boolean?,waterStage:number?):number
    local hits,kos
    if waterStage~=nil then
        local index=waterStage+1
        hits,kos=horde:castWater(source,dir,damage,serverNow(),player,player.Character,
            SevenJobs.Water.metrics[1].values[index],SevenJobs.Water.metrics[2].values[index],waterStage)
    else
        hits,kos=horde:hit(source,dir,damage,serverNow(),player.Character,reach,targetLimit)
    end'''),
        ('''    local job=sevenJobs[player] or "WARRIOR"
    if not SevenJobs.canUse''',
         '''    local job=sevenJobs[player] or "WARRIOR"
    local waterSelected=SevenJobs.waterSelected(player)
    if not SevenJobs.canUse'''),
        ('''        last=sevenJobLastUse[player] or -math.huge}) or not root then return end''',
         '''        last=if waterSelected then -math.huge else (sevenJobLastUse[player] or -math.huge)})
        or not root then return end'''),
        ('''    local growth=SevenJobs.activeGrowth(player)
    local halfMoonRange,halfMoonTargets''',
         '''    local growth=SevenJobs.activeGrowth(player)
    if waterSelected then
        if not growth or not SevenJobs.growthCastReady(player,growth,now) then return end
        if SevenJobs.Growth.cooldown(growth,now,SevenJobs.Water.cd)>0 then return end
        local stage=SevenJobs.Growth.tryCast(growth,match.serial,now,SevenJobs.Water.cd,SevenJobs.Water.energy)
        if stage==nil then return end
        sevenJobLastUse[player]=now
        growth.lastJobUse=now
        sevenJobStrike(player,root.Position,facing,SevenJobs.DETAILS.MAGE.damage,nil,nil,true,stage)
        remote:FireClient(player,snapshotFor(player))
        return
    end
    local halfMoonRange,halfMoonTargets'''),
        ('''        if not growth or not SevenJobs.halfMoonReady(player,growth,now) then return end''',
         '''        if not growth or not SevenJobs.growthCastReady(player,growth,now) then return end'''),
        ('''    sevenJobLastUse[player]=now
    local spec=SevenJobs.DETAILS[job]''',
         '''    sevenJobLastUse[player]=now
    local castState=SevenJobs.GrowthStates[player]
    if castState and castState.round==match.serial then castState.lastJobUse=now end
    local spec=SevenJobs.DETAILS[job]'''),
    ],
    HUD: [
        ('''    local halfMoon=s.roleHalfMoon==true and picked=="WARRIOR"
    local enoughEnergy=not halfMoon or type(s.roleEnergy)=="number" and s.roleEnergy>=30''',
         '''    local halfMoon=s.roleHalfMoon==true and picked=="WARRIOR"
    local waterBolt=s.roleWaterBolt==true and picked=="MAGE"
    local growingSkill=if halfMoon then "半月斬" elseif waterBolt then "水弾" else nil
    local enoughEnergy=not growingSkill or type(s.roleEnergy)=="number" and s.roleEnergy>=30'''),
        (r'''    jobCast.Text=if jobCd>0 then "あと"..tostring(jobCd).."秒"
        elseif halfMoon then
            if type(s.roleGrowthStage)=="number" and type(s.roleEnergy)=="number" then
                "半月斬 S"..tostring(math.clamp(math.floor(s.roleGrowthStage),0,4))
                    .."\nQ  E"..tostring(math.clamp(math.floor(s.roleEnergy),0,100))
            else "半月斬\n準備中"
        else jobSkillName[picked].."\nQキー"''',
         r'''    jobCast.Text=if waterBolt and type(s.roleWaterTarget)=="number"
            and type(s.roleWaterSeconds)=="number" and s.roleWaterSeconds>0 then
                "水印 "..tostring(s.roleWaterTarget).." · "..string.format("%.1f秒",s.roleWaterSeconds)
                    .."\nあと"..tostring(jobCd).."秒"
        elseif jobCd>0 then "あと"..tostring(jobCd).."秒"
        elseif growingSkill then
            if type(s.roleGrowthStage)=="number" and type(s.roleEnergy)=="number" then
                growingSkill.." S"..tostring(math.clamp(math.floor(s.roleGrowthStage),0,4))
                    .."\nQ  E"..tostring(math.clamp(math.floor(s.roleEnergy),0,100))
            else growingSkill.."\n準備中"
        else jobSkillName[picked].."\nQキー"'''),
    ],
}

WATER_METHODS = '''function Horde:updateWaterCue(neutral,now: number)
    local remaining=0
    if neutral.hp>0 and neutral.waterMarks then
        for _,mark in pairs(neutral.waterMarks) do
            if mark.round==self.round then remaining=math.max(remaining,mark.expiry-now) end
        end
    end
    if remaining<=0 then
        if neutral.waterCue then neutral.waterCue.Enabled=false end
        return
    end
    if not neutral.waterCue then
        local cue=Instance.new("BillboardGui")
        cue.Name="WaterMarkStatus"
        cue.Size=UDim2.fromOffset(114,26)
        cue.StudsOffsetWorldSpace=Vector3.new(0,if neutral.elite then 10.3 else 8.2,0)
        cue.MaxDistance=75
        cue.AlwaysOnTop=false
        local label=Instance.new("TextLabel")
        label.Name="Status"
        label.Size=UDim2.fromScale(1,1)
        label.BackgroundColor3=Color3.fromRGB(14,37,59)
        label.BackgroundTransparency=.16
        label.TextColor3=Color3.fromRGB(177,238,255)
        label.TextScaled=true
        label.Parent=cue
        cue.Parent=neutral.body
        neutral.waterCue,neutral.waterText=cue,label
    end
    local displaySeconds=math.max(.1,math.ceil(remaining*10-.000001)/10)
    neutral.waterText.Text="水印 "..tostring(neutral.id).." · "..string.format("%.1f秒",displaySeconds)
    neutral.waterCue.Enabled=true
end

function Horde:waterStatus(owner: Player,now: number): (number?,number?)
    local selected,remaining,preferredDirect
    for _,neutral in ipairs(self.mobs) do
        local mark=neutral.waterMarks and neutral.waterMarks[owner]
        if neutral.hp>0 and mark and mark.round==self.round and mark.expiry>now then
            local direct=mark.direct
            if remaining==nil or direct and not preferredDirect
                or direct==preferredDirect and mark.expiry-now>remaining then
                selected,remaining,preferredDirect=neutral.id,mark.expiry-now,direct
            end
        end
    end
    return selected,remaining
end

-- Water Bolt uses the same HP/KO handler as F and the other neutral abilities.
-- Its range and targeting are checked against the actual caster, not a supplied target.
function Horde:castWater(origin: Vector3,direction: Vector3,damage: number,now: number,
        owner: Player,ignore: Instance?,reach: number,markSeconds: number,stage: number): (number,number)
    if self.round<0 then return 0,0 end
    local params=RaycastParams.new()
    params.FilterType=Enum.RaycastFilterType.Exclude
    params.FilterDescendantsInstances=if ignore then {ignore,self.folder} else {self.folder}
    local function visible(from: Vector3,to: Vector3): boolean
        return workspace:Raycast(from,to-from,params)==nil
    end
    local struck,nearest=nil,math.huge
    for _,neutral in ipairs(self.mobs) do
        if neutral.hp<=0 then continue end
        local unit=horizontal(origin,neutral.pos)
        local distance=(neutral.pos-origin).Magnitude
        if distance<=reach and distance<nearest and math.abs(neutral.pos.Y-origin.Y)<=Combat.SWEEP_MAX_VERTICAL
            and direction:Dot(unit)>=.9 and visible(origin,neutral.pos) then
            struck,nearest=neutral,distance
        end
    end
    if struck==nil then return 0,0 end
    local impact=struck.pos
    local unit,dist=horizontal(origin,impact)
    if self:damageNeutral(struck,unit,dist,damage,now) then return 1,1 end
    local function mark(neutral,direct: boolean)
        neutral.waterMarks=neutral.waterMarks or {}
        neutral.waterMarks[owner]={expiry=now+markSeconds,round=self.round,direct=direct}
        self:updateWaterCue(neutral,now)
    end
    mark(struck,true)
    if stage>=2 then
        -- The old three-direction slot supplies a three-target budget. Spread
        -- marks at the impact only, with no additional hit or damage.
        local neighbours={}
        for _,neutral in ipairs(self.mobs) do
            if neutral==struck or neutral.hp<=0 then continue end
            local distance=(neutral.pos-impact).Magnitude
            if distance<=6 and visible(impact,neutral.pos) and visible(origin,neutral.pos) then
                table.insert(neighbours,{neutral=neutral,distance=distance})
            end
        end
        table.sort(neighbours,function(a,b)
            if a.distance==b.distance then return a.neutral.id<b.neutral.id end
            return a.distance<b.distance
        end)
        for i=1,math.min(2,#neighbours) do mark(neighbours[i].neutral,false) end
    end
    return 1,0
end
'''


def horde_edits(source):
    code = source.decode("utf-8")
    start = "                    local dealt=math.max(1,math.min(math.floor(damage),40))"
    end = "\n                end\n            end\n        end\n    end\n    return touched,defeated"
    assert code.count(start) == code.count(end) == 1
    first = code.index(start)
    last = code.index(end, first)
    handler = textwrap.indent(textwrap.dedent(code[first:last]), "    ")
    handler = patch(handler, [{
        "anchor": "        defeated+=1\n        self.kills+=1",
        "replace": "        m.waterMarks=nil\n        if m.waterCue then m.waterCue.Enabled=false end\n        self.kills+=1",
    }])
    # Keep the original HP, popup, knockback, attack and KO data mutations in one handler.
    damage = ("function Horde:damageNeutral(m,unit: Vector3,dist: number,damage: number,now: number): boolean\n"
              + handler + "\n    return m.hp<=0\nend\n")
    code = code[:first] + "                    if self:damageNeutral(m,unit,dist,damage,now) then defeated+=1 end" + code[last:]
    code = patch(code, [
        {"anchor": "function Horde:tick(", "replace": damage + WATER_METHODS + "function Horde:tick("},
        {"anchor": "    local impacts={}\n    for _,m in ipairs(self.mobs) do",
         "replace": """    local impacts={}
    for _,m in ipairs(self.mobs) do
        if m.waterMarks then
            for owner,mark in pairs(m.waterMarks) do
                if m.hp<=0 or mark.round~=self.round or now>=mark.expiry then
                    m.waterMarks[owner]=nil
                end
            end
            if next(m.waterMarks)==nil then m.waterMarks=nil end
        end
        if m.waterCue and m.waterCue.Enabled then self:updateWaterCue(m,now) end"""},
    ])
    return code.encode("utf-8")


def apply_edits(source, route):
    if route == HORDE:
        return horde_edits(source)
    rows = [{"anchor": a, "replace": b} for a, b in EDITS[route]]
    return patch(source.decode("utf-8"), rows).encode("utf-8")


def load_pins():
    return json.loads((PACKAGE / "source_lock.json").read_bytes())


def apply(dist, profile, off_place):
    pins = load_pins()
    assert pins["profile"] == "rich51" and pins["feature"] == FEATURE
    assert type(pins["enabled"]) is bool
    if profile != pins["profile"] or not pins["enabled"]:
        return False
    off = off_place.read_bytes()
    assert pins["off_place"] == {"bytes":len(off), "sha256":hashlib.sha256(off).hexdigest()}
    prior = sources(dist)
    hashes = {route:gitblob(raw) for route,raw in prior.items()}
    lock = json.loads((dist / "SOURCE_LOCK.json").read_bytes())
    receipt = json.loads((dist / "RC_FEATURE_LOCK.json").read_bytes())
    assert len(hashes) == 72 and hashes == lock["blobs"] == receipt["source_gitblobs"]
    prior_mage = lock["rc_active_mage_armament"]
    assert prior_mage == receipt["rc_active_mage_armament"]
    routes = pins["routes"]
    assert set(routes) == {GAME,HORDE,GROWTH,HUD,WATER}
    assert all(hashes.get(route) == row["before"] for route,row in routes.items())
    assert all(routes[route]["before"] == prior_mage["routes"][route]["after"] for route in (GAME,HORDE))
    prepared = {route:apply_edits(prior[route],route) for route in (GAME,HORDE,GROWTH,HUD)}
    prepared[WATER] = (PACKAGE / Path(WATER).name).read_bytes()
    assert hashlib.sha256(prepared[WATER]).hexdigest() == pins["source_origin"]["selected_catalog_sha256"]
    assert all(gitblob(raw) == routes[route]["after"] for route,raw in prepared.items())
    for route, raw in prepared.items():
        (dist / "src" / route).write_bytes(raw)
    assert sources(dist) == prior | prepared
    current = hashes | {route:gitblob(raw) for route,raw in prepared.items()}
    entry = {"feature":FEATURE,"profile":profile,"routes":routes,"source_origin":pins["source_origin"],
             "off_place":pins["off_place"],"studio_selected_role_only":True,"engine":"NOT_TESTED"}
    lock.update(blobs=current,total_scripts=len(current),rc_active_mage_water=entry)
    receipt.update(source_gitblobs=current,total_sources=len(current),rc_active_mage_water=entry)
    write_json(dist / "SOURCE_LOCK.json",lock)
    write_json(dist / "RC_FEATURE_LOCK.json",receipt)
    print("ACTIVE_MAGE_WATER_IMMEDIATE_OFF_EXACT")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist",type=Path,required=True)
    parser.add_argument("--profile",choices=("rich51","rich47","legacy21"),required=True)
    parser.add_argument("--off-place",type=Path,required=True)
    args = parser.parse_args()
    apply(args.dist,args.profile,args.off_place)
