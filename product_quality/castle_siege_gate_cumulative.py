#!/usr/bin/env python3
"""P0D #470 FB-CASTLE: real walk-in castle gate and 8s tactical lockdown.

Source-exact private 82-script child of verified original Beast+SoloAI Game.
MapBuilder only; retains original Game, SoloTeamBots, egg, score, HUD.
No official RC/main writes, no new Game or Remote/Event score authority.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from xml.etree import ElementTree as ET
from role7_respawn_guard import extract,verify,blob

PARENT_PLACE="P0D_RC82_BEAST_COMPANION_SOLO_AI_CUMULATIVE_PRIVATE.rbxlx"
PARENT_SHA="eb9ccd5bb516328ce61da3b0c82c5dcccdb6cc6ad0e60076d4c9f15db19de1eb"
PARENT_MAP_BLOB="7494ef0f5cd013b55c74bc2b8534905d19ce9399"
PARENT_GAME_BLOB="d704792acbc8f7cf0568ed612b97c53a3cd7a22b"
PARENT_SOLO_BLOB="a77176fdcfe3351b5dc9ed4aa23fcf48a28edd53"
OFFICIAL="d2f3ed1a47558fdaf07be0181c83c698bdb2ce34"
OUTPUT_PLACE="P0D_CASTLE_WALKIN_SIEGE_GATE_BEAST_SOLO_PRIVATE_RC82.rbxlx"
MAP="server/MapBuilder.luau"
GAME="server/Game.server.luau"
BOTS="server/SoloTeamBots.luau"
EXPECTED_PLACE_SHA="c0c74efab8b63716a7b4cef1f8884b4270309c659478e194e1ecf3b8421111a4"
EXPECTED_PLACE_BYTES=792844
EXPECTED_MAP_BLOB="52e677d208412483b744c7ac464eb0ffbc9e6ecd"

# All parts are real server world geometry. Existing studio art arches are
# at x +/-85, ground passage z +/-14, so gates stay below the old arch.
# The door is normally raised/noncolliding, so private solo bots can raid eggs.
GATE_IMPL='''-- P0D_FB_CASTLE_WALKIN_SIEGE_V1: real walk-through castle entrance.
-- No additional heartbeat/Remote/egg/score authority. Mobile: 2 gates, 2 prompts.
local function makeDefensibleGate(base,name,sign,accent)
    local x=sign*85
    local port=Instance.new("Folder")
    port.Name=name.."_WALKIN_GATE"
    port.Parent=base
    local stone=Color3.fromRGB(137,148,163)
    local iron=Color3.fromRGB(64,75,91)
    -- Front curtain consists of TWO segments, leaving a genuine 16-stud door.
    for _,bank in ipairs({-1,1}) do
        part(port,"CURTAIN_FRONT_"..bank,Vector3.new(5,14,38),
            Vector3.new(x,7,bank*27),stone,Enum.Material.Cobblestone)
        for _,z in ipairs({bank*16,bank*28,bank*39}) do
            part(port,"MERLON_"..tostring(z),Vector3.new(5.6,3.1,6),
                Vector3.new(x,15.6,z),stone,Enum.Material.Brick)
        end
    end
    local gate=part(port,name.."_PORTCULLIS",Vector3.new(2,14,15),
        Vector3.new(x,22,0),iron,Enum.Material.Metal,false)
    gate.Transparency=.23
    gate:SetAttribute("GateRaised",true)
    gate:SetAttribute("DurationSeconds",9)
    local console=part(port,name.."_GATE_CONTROL",Vector3.new(2,2.8,2),
        Vector3.new(sign*79,1.4,11),accent,Enum.Material.Metal,false)
    local action=Instance.new("ProximityPrompt")
    action.Name="SiegeGateAction"
    action.ActionText="城門を操作"
    action.ObjectText="守備側は閉門・攻撃側は突破"
    action.HoldDuration=1.4
    action.MaxActivationDistance=10
    action.RequiresLineOfSight=false
    -- Public mode remains noninteractive; private pilot requires opt-in.
    local function pilotAllowed()
        return game:GetService("RunService"):IsStudio() or
            (game.PrivateServerId~="" and
             workspace:GetAttribute("P0D_PRIVATE_SIEGE_GATES")==true)
    end
    action.Enabled=pilotAllowed()
    action.Parent=console
    local tween=game:GetService("TweenService")
    local raised=CFrame.new(x,22,0)
    local lowered=CFrame.new(x,7,0)
    local opened=true
    local epoch=0
    local breachLock=0
    local lastCommand=-math.huge
    local function doorwayClear()
        -- Prevent trapping both real characters and physical AI Humanoids.
        local parts=workspace:GetPartBoundsInBox(CFrame.new(x,7,0),
            Vector3.new(12,15,18))
        for _,hit in ipairs(parts) do
            local actor=hit:FindFirstAncestorOfClass("Model")
            if actor and actor:FindFirstChildOfClass("Humanoid") then
                return false
            end
        end
        return true
    end
    local function slide(to,opening)
        epoch+=1
        local serial=epoch
        opened=opening
        gate:SetAttribute("GateRaised",opening)
        if opening then gate.CanCollide=false end
        tween:Create(gate,TweenInfo.new(.7,Enum.EasingStyle.Quad,
            Enum.EasingDirection.Out),{CFrame=to}):Play()
        if not opening then
            task.delay(.75,function()
                if serial~=epoch then return end
                if doorwayClear() then
                    gate.CanCollide=true
                else
                    -- The exit must always remain safe for people and bots.
                    slide(raised,true)
                end
            end)
        end
    end
    local function openGate()
        if not opened then slide(raised,true) end
    end
    -- A private owner may enable pilot after MapBuilder.build; the attribute
    -- is not required to be present at boot. OFF immediately opens any gate.
    workspace:GetAttributeChangedSignal("P0D_PRIVATE_SIEGE_GATES"):Connect(function()
        action.Enabled=pilotAllowed()
        if not action.Enabled then openGate() end
    end)
    action.Triggered:Connect(function(player)
        if not action.Enabled or player:GetAttribute("P0D_LateJoinSpectator")==true then
            return
        end
        local t=player.Team
        if not t or (t.Name~="RED" and t.Name~="BLUE") then return end
        local character=player.Character
        local root=character and character:FindFirstChild("HumanoidRootPart")
        if not root or (root.Position-console.Position).Magnitude>12 then return end
        local now=os.clock()
        if now-lastCommand<1.25 then return end
        if t.Name==name then
            if not opened or now<breachLock or not doorwayClear() then return end
            lastCommand=now
            slide(lowered,false)
            local scheduled=epoch
            task.delay(9,function()
                if epoch==scheduled then openGate() end
            end)
        else
            if opened then return end
            -- A raider can breach; defenders cannot instantly relock on top
            -- of the attacker. No permanent trap/egg access denial.
            lastCommand=now
            breachLock=now+10
            openGate()
        end
    end)
    return {door=gate,control=console,action=action}
end

'''
FUNCTION_ANCHOR="function MapBuilder.build(config)"
TEAM_ANCHOR="        result.teams[name] = {core = core, egg = egg, eggPrompt = eggPrompt,"
SPAWN_ANCHOR="            spawn = CFrame.new(sign * 68, 5, 0)}"

def sha(raw):return hashlib.sha256(raw).hexdigest()
def build_source(src):
    if src.count(FUNCTION_ANCHOR)!=1 or src.count(TEAM_ANCHOR)!=1 or src.count(SPAWN_ANCHOR)!=1:
        raise ValueError("AUTHOR_MAP_SOURCE_DRIFT")
    if "P0D_FB_CASTLE_WALKIN_SIEGE_V1" in src:
        raise ValueError("CASTLE_PATCH_ALREADY_PRESENT")
    new=src.replace(FUNCTION_ANCHOR,GATE_IMPL+FUNCTION_ANCHOR,1)
    new=new.replace(TEAM_ANCHOR,"        local gate = makeDefensibleGate(base,name,sign,accent)\n"+TEAM_ANCHOR,1)
    new=new.replace(SPAWN_ANCHOR,"            spawn = CFrame.new(sign * 68, 5, 0), gate = gate}",1)
    for keep in ('eggPrompt = prompt(egg, "卵を取る"','scorePrompt = prompt(pad, "卵を届ける"',
        'spawn = CFrame.new(sign * 68, 5, 0)',"part(folder, \"GrassArena\"",
        'part(folder, "CenterRoad"'):
        if keep not in new:raise ValueError("ORIGINAL_MAP_GAMEPLAY_LOST:"+keep)
    for proof in ("P0D_PRIVATE_SIEGE_GATES","GateRaised",
        "workspace:GetPartBoundsInBox","t.Name==name","task.delay(9",
        "t.Name~=\"RED\"","t.Name~=\"BLUE\""):
        if proof not in new:raise ValueError("SIEGE_GATE_MISSING:"+proof)
    return new

def build(parent,out,extract_dir=None):
    with ZipFile(parent) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(
            n.startswith("/") or ".." in Path(n).parts for n in names
        ):raise ValueError("UNSAFE_PARENT_ZIP")
        raw=z.read(PARENT_PLACE)
        lock=json.loads(z.read("SOURCE_LOCK.json"))
        fl=json.loads(z.read("RC_FEATURE_LOCK.json"))
        receipt=json.loads(z.read("RECEIPT.json"))
    if sha(raw)!=PARENT_SHA or receipt.get("official_rc_head")!=OFFICIAL:
        raise ValueError("WRONG_GAME_PARENT")
    if lock["blobs"].get(MAP)!=PARENT_MAP_BLOB or lock["blobs"].get(GAME)!=PARENT_GAME_BLOB or lock["blobs"].get(BOTS)!=PARENT_SOLO_BLOB:
        raise ValueError("WRONG_ORIGINAL_GAME_BEAST_AI_MAP")
    original=verify(raw,lock,fl)
    tree,els=extract(raw)
    before=original["MapBuilder"].text
    after=build_source(before)
    els["MapBuilder"].text=after
    place=ET.tostring(tree,encoding="utf-8")
    actual=extract(place)[1]
    if len(actual)!=82 or any(
        actual[n].text!=original[n].text for n in original if n!="MapBuilder"
    ):raise ValueError("OTHER_81_SCRIPTS_CHANGED")
    newblob=blob(after)
    if EXPECTED_PLACE_SHA and (sha(place)!=EXPECTED_PLACE_SHA
        or len(place)!=EXPECTED_PLACE_BYTES or newblob!=EXPECTED_MAP_BLOB):
        raise ValueError("FINAL_PLACE_OR_MAP_HASH_DRIFT")
    lock["blobs"][MAP]=fl["source_gitblobs"][MAP]=newblob
    verify(place,lock,fl)
    r={"schema":"P0D_FB_CASTLE_GATE_REAL_WALKIN_SIEGE_V1",
       "official_rc_head":OFFICIAL,"official_rc_write":False,
       "parent_sha256":PARENT_SHA,"place_sha256":sha(place),
       "place_bytes":len(place),"new_map_gitblob":newblob,
       "scripts":82,"unchanged_parent_scripts":81,
       "other_game_solo_score_sources_exact":True,
       "source_lock_exact":True,"castle_entrance_real_collision":True,
       "gate_default_open_for_bots":True,"private_gate_optin":"P0D_PRIVATE_SIEGE_GATES",
       "studio_preview":True,"private_default_off":True,
       "native":"NOT_RUN","rojo":"NOT_RUN","studio":"NOT_RUN",
       "android":"NOT_RUN","owner":False,"product":"NO_GO"}
    with ZipFile(out,"w",ZIP_DEFLATED) as z:
        z.writestr(OUTPUT_PLACE,place)
        z.writestr("SOURCE_LOCK.json",json.dumps(lock,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RC_FEATURE_LOCK.json",json.dumps(fl,ensure_ascii=False,indent=2)+"\n")
        z.writestr("RECEIPT.json",json.dumps(r,ensure_ascii=False,indent=2)+"\n")
    if extract_dir:
        extract_dir.mkdir(parents=True,exist_ok=True)
        for name,item in actual.items():
            (extract_dir/(name+".luau")).write_text(item.text,encoding="utf-8")
    return r

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--parent",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--extract",type=Path)
    a=p.parse_args()
    print(json.dumps(build(a.parent,a.out,a.extract),ensure_ascii=False,indent=2))
