"""Integrate the fixed MAGE-025 chain with the current ACTIVE neutral authority."""
import argparse
import hashlib
import json
from pathlib import Path

from apply_active_ready import write_json
from apply_egg_relay_classic import patch
from integrate import gitblob, sources

PACKAGE = Path(__file__).resolve().parent / "features/active_mage_chain"
FEATURE = "GQ219_MAGE_025_ACTIVE_LIGHTNING_CHAIN_V1"
GAME = "server/Game.server.luau"
HORDE = "server/MusouHorde.luau"
GROWTH = "server/MatchRoleGrowth.luau"
HUD = "client/HUD.client.luau"
CHAIN = "server/MageChain.luau"


def fragment(name):
    return (PACKAGE / name).read_text(encoding="utf8").rstrip() + "\n\n"


def game_edits():
    return (
        ('SevenJobs.Water = require(script.Parent:WaitForChild("MageWaterCatalog"))',
         'SevenJobs.Water = require(script.Parent:WaitForChild("MageWaterCatalog"))\n'
         'SevenJobs.Chain = require(script.Parent:WaitForChild("MageChain"))'),
        ("function SevenJobs.blinkSelected(player: Player): boolean",
         '''function SevenJobs.chainSelected(player: Player): boolean
    return match.phase=="ACTIVE" and SevenJobs.growthEnabled()
        and ServerStorage:GetAttribute("P0D_RC_ENABLE_MAGE_CHAIN")~=false
        and player.Parent==Players and player:GetAttribute("P0D_LateJoinSpectator")~=true
        and getTeamName(player)~="NONE" and sevenJobs[player]=="MAGE"
        and (sevenJobLastChoose[player] or -math.huge)>-math.huge
end

function SevenJobs.chainCooldown(state,now: number): number
    return math.max(0,math.ceil((state.lastChain or -math.huge)+SevenJobs.Chain.cooldown-now))
end

function SevenJobs.blinkSelected(player: Player): boolean'''),
        ("    local jobCooldown=math.max(0,math.ceil((sevenJobLastUse[player] or -math.huge)",
         '''    local chainSelected=SevenJobs.chainSelected(player)
    local chain=if chainSelected and SevenJobs.growthCastReady(player,growth,now) then growth else nil
    local jobCooldown=math.max(0,math.ceil((sevenJobLastUse[player] or -math.huge)'''),
        ('''        roleBlink = blinkSelected,
        roleGrowthStage = if growth and ((not halfMoonSelected and not waterSelected and not blinkSelected)
            or halfMoon~=nil or water~=nil or blink~=nil) then SevenJobs.Growth.stage(growth) else nil,
        roleEnergy = if halfMoon or water or blink then math.floor((halfMoon or water or blink).energy) else nil,''',
         '''        roleBlink = blinkSelected,
        roleChain = chainSelected,
        roleChainCooldown = if chain then SevenJobs.chainCooldown(chain,now) else nil,
        roleGrowthStage = if growth and ((not halfMoonSelected and not waterSelected and not blinkSelected
            and not chainSelected) or halfMoon~=nil or water~=nil or blink~=nil or chain~=nil)
            then SevenJobs.Growth.stage(growth) else nil,
        roleEnergy = if halfMoon or water or blink or chain then math.floor((halfMoon or water or blink or chain).energy) else nil,'''),
        ('''        reach:number?,targetLimit:number?,qualifiesForGrowth:boolean?,waterStage:number?):number
    local hits,kos
    if waterStage~=nil then''',
         '''        reach:number?,targetLimit:number?,qualifiesForGrowth:boolean?,waterStage:number?,chainImpact:any?):number
    local hits,kos
    if chainImpact then
        hits,kos,chainImpact.positions=horde:castMageChain(chainImpact.first,source,damage,serverNow(),
            chainImpact.stage,chainImpact.clear)
    elseif waterStage~=nil then'''),
        ("local function useSevenJob(player:Player,data:any)",
         fragment("game.luau") + "local function useSevenJob(player:Player,data:any)"),
        ('    elseif data.action == "JOB_SKILL" then useSevenJob(player,data)',
         '    elseif data.action == "JOB_SKILL" then useSevenJob(player,data)\n'
         '    elseif data.action == "MAGE_CHAIN" then SevenJobs.useMageChain(player,data)'),
    )


H_RECIPES = (
    ('local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))',
     'local Combat=require(script.Parent:WaitForChild("MusouCombatRules"))\n'
     'local MageChain=require(script.Parent:WaitForChild("MageChain"))'),
)


def hud_edits():
    return (
        ('''jobCast.MouseButton1Click:Connect(function() action("JOB_SKILL",nil) end)
UserInputService.InputBegan:Connect(function(input,processed)
    if processed then return end
    if input.KeyCode==Enum.KeyCode.Q then action("JOB_SKILL",nil)''',
         '''jobCast.MouseButton1Click:Connect(function() action("JOB_SKILL",nil) end)
local chainCast=button(gui,"MageChainAbility","連鎖雷 Cキー",
    UDim2.fromOffset(94,56),UDim2.new(0,252,1,-17),Color3.fromRGB(104,73,43))
chainCast.Visible=false
chainCast.Active=false
chainCast.Activated:Connect(function()
    if chainCast.Visible and chainCast.Active then action("MAGE_CHAIN",nil) end
end)
UserInputService.InputBegan:Connect(function(input,processed)
    if processed then return end
    if input.KeyCode==Enum.KeyCode.Q then action("JOB_SKILL",nil)
    elseif input.KeyCode==Enum.KeyCode.C and chainCast.Active then action("MAGE_CHAIN",nil)'''),
        ('''local function touchAttackPosition(view: Vector2, jump: Rect, occupied: {Rect}): (Vector2?, number)
    local size = math.clamp(math.floor(math.min(view.X, view.Y) * .23), 56, 74)''',
         '''local function touchAttackPosition(view: Vector2, jump: Rect, occupied: {Rect}, buttonSize: number?): (Vector2?, number)
    local size = buttonSize or math.clamp(math.floor(math.min(view.X, view.Y) * .23), 56, 74)'''),
        ('''local attackInBattle = false
local function restoreDesktopAttack()''',
         '''local attackInBattle = false
local chainInBattle = false
local chainDesktopSize,chainDesktopPosition=chainCast.Size,chainCast.Position
local function restoreDesktopAttack()'''),
        ('''local function layoutTouchAttack()
    if not UserInputService.TouchEnabled''',
         '''local function layoutTouchAttack()
    chainCast.Visible=chainInBattle and not UserInputService.TouchEnabled and gui.AbsoluteSize.X>=512
    chainCast.Size,chainCast.Position=chainDesktopSize,chainDesktopPosition
    if not UserInputService.TouchEnabled'''),
        ('''    if not attackInBattle or not jump or not jump:IsA("GuiButton") then''',
         '''    chainCast.Visible=false
    if not attackInBattle or not jump or not jump:IsA("GuiButton") then'''),
        ('''    local position, size = touchAttackPosition(gui.AbsoluteSize, Rect.new(at, at + jump.AbsoluteSize), occupied)''',
         '''    local jumpRect=Rect.new(at,at+jump.AbsoluteSize)
    local position, size = touchAttackPosition(gui.AbsoluteSize,jumpRect,occupied)'''),
        ('''        attack.Visible = true
    else
        -- A viewport with no usable slot must leave the platform controls available.''',
         '''        attack.Visible = true
        table.insert(occupied,Rect.new(position,position+Vector2.new(size,size)))
    else
        -- A viewport with no usable slot must leave the platform controls available.'''),
        ('''        attack.Visible = false
    end
end
gui:GetPropertyChangedSignal("AbsoluteSize")''',
         '''        attack.Visible = false
    end
    if chainInBattle then
        local point,dimension=touchAttackPosition(gui.AbsoluteSize,jumpRect,occupied,52)
        if point then
            chainCast.Size=UDim2.fromOffset(dimension,dimension)
            chainCast.Position=UDim2.fromOffset(point.X,point.Y+dimension)
            chainCast.Visible=true
        end
    end
end
gui:GetPropertyChangedSignal("AbsoluteSize")'''),
        ('''    local carryingEgg = type(s.carrying) == "string" and s.carrying ~= ""
    windButton.Visible''',
         r'''    local carryingEgg = type(s.carrying) == "string" and s.carrying ~= ""
    local chainCd=if type(s.roleChainCooldown)=="number" and s.roleChainCooldown>=0
        and s.roleChainCooldown<=20 then math.ceil(s.roleChainCooldown) else nil
    chainInBattle=jobCast.Visible and picked=="MAGE" and s.roleChain==true
    chainCast.Active=chainInBattle and chainCd==0 and not carryingEgg and not currentNetBound
        and type(s.roleEnergy)=="number" and s.roleEnergy>=40
    chainCast.AutoButtonColor=chainCast.Active
    chainCast.Text=if not chainCd then "連鎖雷\n準備中"
        elseif chainCd>0 then "連鎖雷\nあと"..tostring(chainCd).."秒"
        elseif not UserInputService.TouchEnabled then "連鎖雷 C\nE40" else "連鎖雷\nE40"
    windButton.Visible'''),
    )


def apply_edits(raw, route):
    if route == GAME:
        edits = game_edits()
    elif route == HORDE:
        anchor = "function Horde:tick("
        edits = H_RECIPES + ((anchor, fragment("horde.luau") + anchor),)
    elif route == GROWTH:
        edits = (("    lastJobUse: number?,", "    lastJobUse: number?,\n    lastChain: number?,"),)
    elif route == HUD:
        edits = hud_edits()
    else:
        raise ValueError(f"Unexpected chain source route: {route}")
    return patch(raw.decode("utf8"), [
        {"anchor": before, "replace": after} for before, after in edits
    ]).encode("utf8")


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
    hashes = {route: gitblob(raw) for route, raw in prior.items()}
    lock = json.loads((dist / "SOURCE_LOCK.json").read_bytes())
    receipt = json.loads((dist / "RC_FEATURE_LOCK.json").read_bytes())
    assert len(hashes) == 74 and hashes == lock["blobs"] == receipt["source_gitblobs"]
    assert lock["rc_active_crowd_cap"] == receipt["rc_active_crowd_cap"]
    assert lock["rc_active_ninja_blink"] == receipt["rc_active_ninja_blink"]
    assert lock["rc_active_mage_water"] == receipt["rc_active_mage_water"]
    routes = pins["routes"]
    assert set(routes) == {GAME, HORDE, GROWTH, HUD, CHAIN}
    assert all(hashes.get(route) == row["before"] for route, row in routes.items())
    updated = {route: apply_edits(prior[route], route) for route in (GAME, HORDE, GROWTH, HUD)}
    updated[CHAIN] = (PACKAGE / Path(CHAIN).name).read_bytes()
    assert all(gitblob(raw) == routes[route]["after"] for route, raw in updated.items())
    for route, raw in updated.items():
        (dist / "src" / route).write_bytes(raw)
    assert sources(dist) == prior | updated
    current = hashes | {route: gitblob(raw) for route, raw in updated.items()}
    entry = {"feature": FEATURE, "profile": profile, "routes": routes,
             "source_origin": pins["source_origin"], "off_place": pins["off_place"],
             "studio_selected_role_only": True, "engine": "NOT_TESTED"}
    lock.update(blobs=current, total_scripts=len(current), rc_active_mage_chain=entry)
    receipt.update(source_gitblobs=current, total_sources=len(current), rc_active_mage_chain=entry)
    write_json(dist / "SOURCE_LOCK.json", lock)
    write_json(dist / "RC_FEATURE_LOCK.json", receipt)
    print("ACTIVE_MAGE_CHAIN_IMMEDIATE_OFF_EXACT")
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--profile", choices=("rich51", "rich47", "legacy21"), required=True)
    parser.add_argument("--off-place", type=Path, required=True)
    args = parser.parse_args()
    apply(args.dist, args.profile, args.off_place)
