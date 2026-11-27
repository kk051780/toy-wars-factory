"""Mount NINJA-031 movement on the established active role and match authority."""
import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources

PACKAGE = Path(__file__).resolve().parent / "features/active_ninja_blink"
FEATURE = "GQ219_NINJA_031_ACTIVE_BLINK_V1"
GAME = "server/Game.server.luau"
HUD = "client/HUD.client.luau"
BLINK = "server/NinjaBlink.luau"

EDITS = {
    GAME: [
        ('''SevenJobs.Water = require(script.Parent:WaitForChild("MageWaterCatalog"))''',
         '''SevenJobs.Water = require(script.Parent:WaitForChild("MageWaterCatalog"))
SevenJobs.Blink = require(script.Parent:WaitForChild("NinjaBlink"))'''),
        ('''function SevenJobs.growthCastReady(player: Player, state, now: number): boolean''',
         '''function SevenJobs.blinkSelected(player: Player): boolean
    return match.phase=="ACTIVE" and SevenJobs.growthEnabled()
        and ServerStorage:GetAttribute("P0D_RC_ENABLE_NINJA_BLINK")~=false
        and player.Parent==Players and player:GetAttribute("P0D_LateJoinSpectator")~=true
        and sevenJobs[player]=="NINJA" and (sevenJobLastChoose[player] or -math.huge)>-math.huge
end

function SevenJobs.growthCastReady(player: Player, state, now: number): boolean'''),
        ('''    local water=if waterSelected and SevenJobs.growthCastReady(player,growth,now) then growth else nil
    local waterTarget''',
         '''    local water=if waterSelected and SevenJobs.growthCastReady(player,growth,now) then growth else nil
    local blinkSelected=SevenJobs.blinkSelected(player)
    local blink=nil
    if blinkSelected and SevenJobs.growthCastReady(player,growth,now) then
        local _,blinkRoot,blinkHum=healthy(player)
        if blinkRoot and blinkHum and SevenJobs.Blink.isGrounded(blinkHum)
            and SevenJobs.Blink.direction(blinkRoot.CFrame.LookVector,blinkRoot.AssemblyLinearVelocity,
                blinkHum.WalkSpeed,SevenJobs.Growth.stage(growth)) then blink=growth end
    end
    local waterTarget'''),
        ('''        roleWaterSeconds = waterSeconds,
        roleGrowthStage = if growth and ((not halfMoonSelected and not waterSelected)
            or halfMoon~=nil or water~=nil) then SevenJobs.Growth.stage(growth) else nil,
        roleEnergy = if halfMoon or water then math.floor((halfMoon or water).energy) else nil,
        jobCooldown = if water then SevenJobs.Growth.cooldown(water,now,SevenJobs.Water.cd)''',
         '''        roleWaterSeconds = waterSeconds,
        roleBlink = blinkSelected,
        roleGrowthStage = if growth and ((not halfMoonSelected and not waterSelected and not blinkSelected)
            or halfMoon~=nil or water~=nil or blink~=nil) then SevenJobs.Growth.stage(growth) else nil,
        roleEnergy = if halfMoon or water or blink then math.floor((halfMoon or water or blink).energy) else nil,
        jobCooldown = if blink then SevenJobs.Growth.cooldown(blink,now,SevenJobs.Blink.config.cd)
            elseif water then SevenJobs.Growth.cooldown(water,now,SevenJobs.Water.cd)'''),
        ('''local function useSevenJob(player:Player,data:any)''',
         '''function SevenJobs.executeBlink(player: Player,state,stage: number,character: Model,
        root: BasePart,hum: Humanoid,team: string,direction: Vector3)
    local arena=map.model:FindFirstChild("GrassArena")
    if not arena or not arena:IsA("BasePart") then return end
    local origin=root.Position
    local duration=SevenJobs.Blink.config.metrics[2].values[stage+1]
    local amount=SevenJobs.Blink.config.metrics[1].values[stage+1]
    local serial=match.serial
    local selectedAt=sevenJobLastChoose[player]
    local signal=Instance.new("Part")
    signal.Name="P0D_NINJA_BLINK_WARNING"
    signal.Size=Vector3.new(.72,.12,2.6)
    signal.Anchored=true
    signal.CanCollide=false;signal.CanTouch=false;signal.CanQuery=false
    signal.CastShadow=false
    signal.Color=Color3.fromRGB(113,84,158)
    signal.Material=Enum.Material.SmoothPlastic
    local aim=origin+direction*1.45-Vector3.new(0,1.25,0)
    signal.CFrame=CFrame.lookAt(aim,aim+direction)
    signal.Parent=map.model
    task.delay(duration,function()
        if signal.Parent then signal:Destroy() end
        local alive,current,currentHum=healthy(player)
        if not alive or current~=root or currentHum~=hum or player.Character~=character
            or not SevenJobs.Blink.isGrounded(hum)
            or match.serial~=serial or SevenJobs.activeGrowth(player)~=state
            or not SevenJobs.blinkSelected(player) or getTeamName(player)~=team
            or sevenJobLastChoose[player]~=selectedAt or carry[player]~=nil or slowed[player]~=nil then return end
        local drift=root.Position-origin
        if drift.Magnitude>4.5 or (drift-direction*drift:Dot(direction)).Magnitude>.6 then return end
        local target=SevenJobs.Blink.landing(arena,character,root.Position,direction,amount)
        if not target then return end
        for _,other in ipairs(Players:GetPlayers()) do
            if other~=player then
                local otherAlive,otherRoot=healthy(other)
                if otherAlive and otherRoot and (otherRoot.Position-target).Magnitude<3.2 then return end
            end
        end
        root.CFrame=root.CFrame+(target-root.Position)
        root.AssemblyLinearVelocity=Vector3.zero
        root.AssemblyAngularVelocity=Vector3.zero
        SevenJobs.markGrowthActivity(player)
    end)
end

local function useSevenJob(player:Player,data:any)'''),
        ('''    local alive,root=healthy(player)
    local team=getTeamName(player)
    local now=serverNow()
    local job=sevenJobs[player] or "WARRIOR"
    local waterSelected=SevenJobs.waterSelected(player)''',
         '''    local alive,root,hum=healthy(player)
    local team=getTeamName(player)
    local now=serverNow()
    local job=sevenJobs[player] or "WARRIOR"
    local waterSelected=SevenJobs.waterSelected(player)
    local blinkSelected=SevenJobs.blinkSelected(player)'''),
        ('''        last=if waterSelected then -math.huge else (sevenJobLastUse[player] or -math.huge)})''',
         '''        last=if waterSelected or blinkSelected then -math.huge else (sevenJobLastUse[player] or -math.huge)})'''),
        ('''    local growth=SevenJobs.activeGrowth(player)
    if waterSelected then''',
         '''    local growth=SevenJobs.activeGrowth(player)
    if blinkSelected then
        local character=player.Character
        if not character or not hum or not SevenJobs.Blink.isGrounded(hum)
            or not growth or not SevenJobs.growthCastReady(player,growth,now) then return end
        local config=SevenJobs.Blink.config
        if SevenJobs.Growth.cooldown(growth,now,config.cd)>0 then return end
        local direction=SevenJobs.Blink.direction(root.CFrame.LookVector,root.AssemblyLinearVelocity,
            hum.WalkSpeed,SevenJobs.Growth.stage(growth))
        if not direction then return end
        local stage=SevenJobs.Growth.tryCast(growth,match.serial,now,config.cd,config.energy)
        if stage==nil then return end
        sevenJobLastUse[player]=now
        growth.lastJobUse=now
        SevenJobs.executeBlink(player,growth,stage,character,root,hum,team,direction)
        remote:FireClient(player,snapshotFor(player))
        return
    end
    if waterSelected then'''),
    ],
    HUD: [
        ('''    local waterBolt=s.roleWaterBolt==true and picked=="MAGE"
    local growingSkill=if halfMoon then "半月斬" elseif waterBolt then "水弾" else nil''',
         '''    local waterBolt=s.roleWaterBolt==true and picked=="MAGE"
    local blink=s.roleBlink==true and picked=="NINJA"
    local growingSkill=if halfMoon then "半月斬" elseif waterBolt then "水弾" elseif blink then "瞬歩" else nil'''),
    ],
}


def apply_edits(raw, route):
    return patch(raw.decode("utf-8"), [
        {"anchor": anchor, "replace": value} for anchor, value in EDITS[route]
    ]).encode("utf-8")


def load_pins():
    return json.loads((PACKAGE / "source_lock.json").read_bytes())


def apply(dist, profile, off_place):
    pins = load_pins()
    assert pins["profile"] == "rich51" and pins["feature"] == FEATURE
    assert type(pins["enabled"]) is bool
    if profile != pins["profile"] or not pins["enabled"]:
        return False
    off = off_place.read_bytes()
    assert pins["off_place"] == {"bytes":len(off),"sha256":hashlib.sha256(off).hexdigest()}
    prior = sources(dist)
    hashes = {route:gitblob(raw) for route,raw in prior.items()}
    lock = json.loads((dist / "SOURCE_LOCK.json").read_bytes())
    receipt = json.loads((dist / "RC_FEATURE_LOCK.json").read_bytes())
    assert len(hashes)==73 and hashes==lock["blobs"]==receipt["source_gitblobs"]
    assert lock["rc_active_mage_water"]==receipt["rc_active_mage_water"]
    routes = pins["routes"]
    assert set(routes)=={GAME,HUD,BLINK}
    assert all(hashes.get(route)==data["before"] for route,data in routes.items())
    assert all(hashes[route]==lock["rc_active_mage_water"]["routes"][route]["after"] for route in (GAME,HUD))
    updated={route:apply_edits(prior[route],route) for route in EDITS}
    updated[BLINK]=(PACKAGE / Path(BLINK).name).read_bytes()
    assert all(gitblob(raw)==routes[route]["after"] for route,raw in updated.items())
    for route,raw in updated.items():
        (dist / "src" / route).write_bytes(raw)
    assert sources(dist)==prior|updated
    current=hashes|{route:gitblob(raw) for route,raw in updated.items()}
    entry={"feature":FEATURE,"profile":profile,"routes":routes,"source_origin":pins["source_origin"],
           "off_place":pins["off_place"],"studio_selected_role_only":True,"engine":"NOT_TESTED"}
    lock.update(blobs=current,total_scripts=len(current),rc_active_ninja_blink=entry)
    receipt.update(source_gitblobs=current,total_sources=len(current),rc_active_ninja_blink=entry)
    write_json(dist / "SOURCE_LOCK.json",lock)
    write_json(dist / "RC_FEATURE_LOCK.json",receipt)
    print("ACTIVE_NINJA_BLINK_IMMEDIATE_OFF_EXACT")
    return True


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist",type=Path,required=True)
    parser.add_argument("--profile",choices=("rich51","rich47","legacy21"),required=True)
    parser.add_argument("--off-place",type=Path,required=True)
    args=parser.parse_args()
    apply(args.dist,args.profile,args.off_place)
