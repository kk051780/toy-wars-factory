"""Select the existing #471 Mage armament and one authoritative neutral attack route."""
import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources

PACKAGE = Path(__file__).resolve().parent / "features/active_mage_armament"
FEATURE = "GQ470_FB020_ACTIVE_MAGE_ARMAMENT_V1"
GAME = "server/Game.server.luau"
HORDE = "server/MusouHorde.luau"
ARMAMENT = "server/SevenJobArmamentM1.luau"
AUTHOR_BLOB = "7468f143ef801ebc7bdeab75f13bb5b16f66b103"

EDITS = {
    GAME: [
        ('''SevenJobs.Undead = require(script.Parent:WaitForChild("UndeadSquad"))''',
         '''SevenJobs.Undead = require(script.Parent:WaitForChild("UndeadSquad"))
SevenJobs.Armament = require(script.Parent:WaitForChild("SevenJobArmamentM1"))'''),
        ('''function SevenJobs.growthEnabled()''',
         '''function SevenJobs.mageArmamentSelected(player: Player): boolean
    return RunService:IsStudio()
        and ServerStorage:GetAttribute("P0D_RC_ENABLE_SEVEN_JOBS_PVE")~=false
        and ServerStorage:GetAttribute("P0D_RC_ENABLE_ACTIVE_MAGE_M1")~=false
        and player.Parent==Players and player:GetAttribute("P0D_LateJoinSpectator")~=true
        and getTeamName(player)~="NONE"
        and sevenJobs[player]=="MAGE" and (sevenJobLastChoose[player] or -math.huge)>-math.huge
end

function SevenJobs.clearMageArmament(player: Player, character: Model?)
    SevenJobs.Armament.resetPlayer(player)
    SevenJobs.Armament.clear(character)
end

function SevenJobs.ensureMageStaff(character: Model?)
    if character and not character:FindFirstChild("P0D_JOB_HELD_WEAPON_RIGHT") then
        SevenJobs.Armament.equip(character,"MAGE")
    end
end

function SevenJobs.syncMageStaff(player: Player)
    local phase=match.phase
    if (phase=="LOBBY" or phase=="COUNTDOWN" or phase=="ACTIVE")
        and SevenJobs.mageArmamentSelected(player) and healthy(player) then
        SevenJobs.ensureMageStaff(player.Character)
    else
        SevenJobs.Armament.resetPlayer(player)
        local character=player.Character
        if character and character:FindFirstChild("P0D_JOB_HELD_WEAPON_RIGHT") then
            SevenJobs.Armament.clear(character)
        end
    end
end

function SevenJobs.growthEnabled()'''),
        ('''        cleanupScout(p)
        SevenJobs.Undead.clear(p)
    end
    match.phase = "RESULTS"''',
         '''        cleanupScout(p)
        SevenJobs.Undead.clear(p)
        SevenJobs.clearMageArmament(p,p.Character)
    end
    match.phase = "RESULTS"'''),
        ('''    table.clear(SevenJobs.GrowthStates)
    for _,p in ipairs(Players:GetPlayers()) do SevenJobs.Undead.clear(p) end''',
         '''    table.clear(SevenJobs.GrowthStates)
    for _,p in ipairs(Players:GetPlayers()) do
        SevenJobs.Undead.clear(p)
        SevenJobs.clearMageArmament(p,p.Character)
    end'''),
        ('''        hum.WalkSpeed = Config.RoleWalkSpeed[role]
        invulnUntil[player] = serverNow() + Config.RespawnInvulnerability
        hum.Died:Connect(function()''',
         '''        hum.WalkSpeed = Config.RoleWalkSpeed[role]
        invulnUntil[player] = serverNow() + Config.RespawnInvulnerability
        if sevenJobs[player]=="MAGE" then SevenJobs.syncMageStaff(player) end
        hum.Died:Connect(function()'''),
        ('''            SevenJobs.Undead.clear(player)
            dropEgg(player)
            invulnUntil[player] = 0''',
         '''            SevenJobs.Undead.clear(player)
            SevenJobs.clearMageArmament(player,character)
            dropEgg(player)
            invulnUntil[player] = 0'''),
        ('''        local touched,defeated = horde:hit(root.Position,look,
            Config.CombatDamage[roles[player] or "RAIDER"]
                *SavedPvePolicy.mergeWithEarned(
                    earnedDamageMultiplier(player,"MINION")
                    *Dojo.pveDamageMultiplier(dojoStates[player],"WEAPON"),
                    math.min(3.8,savedPveMinionMultiplier(player)
                    *twinBondOnlyNeutralMobBonus(player))),now,player.Character)''',
         '''        local neutralDamage=Config.CombatDamage[roles[player] or "RAIDER"]
            *SavedPvePolicy.mergeWithEarned(
                earnedDamageMultiplier(player,"MINION")
                *Dojo.pveDamageMultiplier(dojoStates[player],"WEAPON"),
                math.min(3.8,savedPveMinionMultiplier(player)
                *twinBondOnlyNeutralMobBonus(player)))
        local touched,defeated
        local avatar=player.Character
        local origin=root.Position
        if SevenJobs.mageArmamentSelected(player) then
            SevenJobs.ensureMageStaff(avatar)
            local stage=SevenJobs.Armament.comboStage(player,"MAGE",now)
            local cast={origin=origin,hitModels={} :: {[Model]: boolean}}
            local remaining=6
            local params=RaycastParams.new()
            params.FilterType=Enum.RaycastFilterType.Exclude
            params.FilterDescendantsInstances=if avatar then {avatar,horde.folder} else {horde.folder}
            local function visible(point: Vector3): boolean
                return workspace:Raycast(origin,point-origin,params)==nil
            end
            touched,defeated=SevenJobs.Armament.strike("MAGE",stage,origin,look,neutralDamage,
                function(muzzle,dir,damage)
                    if remaining==0 then return 0,0 end
                    local hits,kos=horde:hit(muzzle,dir,damage,now,avatar,nil,remaining,cast)
                    remaining-=hits
                    return hits,kos
                end,visible)
        else
            if sevenJobs[player]=="MAGE" then SevenJobs.syncMageStaff(player) end
            touched,defeated=horde:hit(origin,look,neutralDamage,now,avatar)
        end'''),
        ('''    sevenJobs[player]=job
    sevenJobLastChoose[player]=now
    remote:FireClient(player,snapshotFor(player))''',
         '''    SevenJobs.clearMageArmament(player,player.Character)
    sevenJobs[player]=job
    sevenJobLastChoose[player]=now
    if job=="MAGE" then SevenJobs.syncMageStaff(player) end
    remote:FireClient(player,snapshotFor(player))'''),
        ('''        cleanupScout(player)
        SevenJobs.Undead.clear(player)
        dropEgg(player)
        task.spawn(assignSpawn, player, character)''',
         '''        cleanupScout(player)
        SevenJobs.Undead.clear(player)
        SevenJobs.clearMageArmament(player,character)
        dropEgg(player)
        task.spawn(assignSpawn, player, character)'''),
        ('''    SevenJobs.Undead.clear(player)
    SevenJobs.GrowthStates[player]=nil''',
         '''    SevenJobs.Undead.clear(player)
    SevenJobs.clearMageArmament(player,player.Character)
    SevenJobs.GrowthStates[player]=nil'''),
        ('''        for _,player in ipairs(Players:GetPlayers()) do
            local state=dojoStates[player]
            if state then
                local previous=dojoLastTick[player] or now''',
         '''        for _,player in ipairs(Players:GetPlayers()) do
            if sevenJobs[player]=="MAGE" then SevenJobs.syncMageStaff(player) end
            local state=dojoStates[player]
            if state then
                local previous=dojoLastTick[player] or now'''),
    ],
    HORDE: [
        ('''function Horde:hit(origin: Vector3,facing: Vector3,damage: number,now: number,ignore: Instance?,
        reach: number?,targetLimit: number?): (number,number)''',
         '''type MageCastSweep={origin: Vector3,hitModels: {[Model]: boolean}}
function Horde:hit(origin: Vector3,facing: Vector3,damage: number,now: number,ignore: Instance?,
        reach: number?,targetLimit: number?,cast: MageCastSweep?): (number,number)'''),
        ('''    for _,m in ipairs(self.mobs) do
        if m.hp>0 and touched<maximumTargets then
            local unit,dist=horizontal(origin,m.pos)
            local vertical=origin.Y-m.pos.Y''',
         '''    local rayOrigin=if cast then cast.origin else origin
    for _,m in ipairs(self.mobs) do
        if m.hp>0 and touched<maximumTargets and (not cast or not cast.hitModels[m.model])
            and (not cast or (m.pos-rayOrigin).Magnitude<=18) then
            -- Close targets in front of the actual Mage can still be hit before the spell muzzle.
            local geometryOrigin=if cast and (m.pos-origin):Dot(direction)<0 then rayOrigin else origin
            local unit,dist=horizontal(geometryOrigin,m.pos)
            local vertical=geometryOrigin.Y-m.pos.Y'''),
        ('''                local ray=workspace:Raycast(origin,m.pos-origin,params)
                if Combat.canSweep(dist,vertical,facingDot,ray==nil) then
                    touched+=1''',
         '''                -- All Mage rays start at the actual avatar, never beyond an obstruction.
                local ray=workspace:Raycast(rayOrigin,m.pos-rayOrigin,params)
                if Combat.canSweep(dist,vertical,facingDot,ray==nil) then
                    if cast then cast.hitModels[m.model]=true end
                    touched+=1'''),
    ],
    ARMAMENT: [
        ('''    baseDamage:number,hitCallback:(Vector3,Vector3,number)->(number,number)):(number,number)''',
         '''    baseDamage:number,hitCallback:(Vector3,Vector3,number)->(number,number),
    effectClear:((Vector3)->boolean)?):(number,number)'''),
        ('''        local arc=Instance.new("Part")
        arc.Name="P0D_M1_HIT_ARC_"..job
        arc.Size=Vector3.new(if job=="WARRIOR" then 6 elseif job=="NINJA" then 2.5 else 4,
            .18, if job=="BEAST_TAMER" then 5 else 2.3)
        arc.Anchored=true;arc.CanCollide=false;arc.CanTouch=false;arc.CanQuery=false
        arc.CastShadow=false
        arc.Material=Enum.Material.Neon
        local color=JOBS[job].rgb
        arc.Color=Color3.fromRGB(color[1],color[2],color[3])
        arc.Transparency=.38
        local impact=origin+dir*(shot.s+2)
        arc.CFrame=CFrame.lookAt(impact,impact+dir)
        arc.Parent=workspace
        Debris:AddItem(arc,.20)''',
         '''        local impact=origin+dir*(shot.s+2)
        if not effectClear or effectClear(impact+dir*1.2) then
            local arc=Instance.new("Part")
            arc.Name="P0D_M1_HIT_ARC_"..job
            arc.Size=Vector3.new(if job=="WARRIOR" then 6 elseif job=="NINJA" then 2.5 else 4,
                .18, if job=="BEAST_TAMER" then 5 else 2.3)
            arc.Anchored=true;arc.CanCollide=false;arc.CanTouch=false;arc.CanQuery=false
            arc.CastShadow=false
            arc.Material=Enum.Material.Neon
            local color=JOBS[job].rgb
            arc.Color=Color3.fromRGB(color[1],color[2],color[3])
            arc.Transparency=.38
            arc.CFrame=CFrame.lookAt(impact,impact+dir)
            arc.Parent=workspace
            Debris:AddItem(arc,.20)
        end'''),
    ],
}


def apply_edits(source, route):
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
    assert pins["off_place"] == {"bytes": len(off), "sha256": hashlib.sha256(off).hexdigest()}
    prior = sources(dist)
    prior_hashes = {name: gitblob(raw) for name, raw in prior.items()}
    lock = json.loads((dist / "SOURCE_LOCK.json").read_bytes())
    receipt = json.loads((dist / "RC_FEATURE_LOCK.json").read_bytes())
    assert len(prior_hashes) == 71 and prior_hashes == lock["blobs"] == receipt["source_gitblobs"]
    assert lock["rc_active_role_growth"] == receipt["rc_active_role_growth"]
    routes = pins["routes"]
    assert set(routes) == set(EDITS) and all(prior_hashes.get(route) == pins["routes"][route]["before"]
                                            for route in routes)
    donor = (PACKAGE / Path(ARMAMENT).name).read_bytes()
    assert gitblob(donor) == pins["source_origin"]["blob"] == AUTHOR_BLOB
    transformed = {route: apply_edits(prior[route], route) for route in (GAME, HORDE)}
    transformed[ARMAMENT] = apply_edits(donor, ARMAMENT)
    assert all(gitblob(raw) == routes[route]["after"] for route, raw in transformed.items())
    for route, raw in transformed.items():
        (dist / "src" / route).write_bytes(raw)
    assert sources(dist) == prior | transformed
    final = prior_hashes | {route: gitblob(raw) for route, raw in transformed.items()}
    mounted = {"feature": FEATURE, "profile": profile, "routes": routes,
               "source_origin": pins["source_origin"], "off_place": pins["off_place"],
               "studio_selected_role_only": True, "engine": "NOT_TESTED"}
    lock.update(blobs=final, total_scripts=len(final), rc_active_mage_armament=mounted)
    receipt.update(source_gitblobs=final, total_sources=len(final), rc_active_mage_armament=mounted)
    write_json(dist / "SOURCE_LOCK.json", lock)
    write_json(dist / "RC_FEATURE_LOCK.json", receipt)
    print("ACTIVE_MAGE_ARMAMENT_IMMEDIATE_OFF_EXACT")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    parser.add_argument("--off-place", type=Path, required=True)
    args = parser.parse_args()
    apply(args.dist, args.profile, args.off_place)
