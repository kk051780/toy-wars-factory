#!/usr/bin/env python3
"""Create actual one-Game H1 auto-training preview from exact original 43 Luau build.
This is a Studio-only/SESSION-only PvE experiment; no DataStore schema changes.
Only Game & original HUD modified, one pure DojoRules ModuleScript added.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve();OWN=HERE.parents[1];REPO=HERE.parents[3]
UP=REPO/"handoffs/P0D-B42-V7-SKYCASTLE-SOLO-20261113-01"
OLD=UP/"dist/EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_STUDIO_SOLO_UNPUBLISHED"
NEW=OWN/"dist/EGG_RAID_RUMBLE_B42_V7_SKY_SOLO_AUTO_DOJO_PRIVATE"
DOJO_BLOB="120bac439c979310c9ddeb2fcf2ffa002b6d1add"
BEFORE_HORDE="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
BEFORE_SKY="0a6360392f4384dc2f0ab1e9afc1d840d66a22b8"
BEFORE_SOLO="22e7e22e8837dbf44c57fdfb30efd480457022fb"

def blob(data):return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def sources(root):
 return {p.relative_to(root/"src").as_posix():p.read_bytes() for p in sorted((root/"src").rglob("*.luau"))}
def replace_one(s,needle,replacement,reason):
 count=s.count(needle)
 assert count==1,(reason,count)
 return s.replace(needle,replacement)

MAP_STATIONS = '''-- Studio-only mirrored on-the-ground AUTO dojo. Both colors have exactly same pads.
-- Decorative only; never a separate Game/Remote/Score or new DataStore writer.
local dojoPads: {[string]: {[string]: Part}} = {}
local dojoStates: {[Player]: any} = {}
local dojoLastTick: {[Player]: number} = {}
local dojoFriends: {[Player]: {[number]: boolean}} = {}
if RunService:IsStudio() then
    for _,side in ipairs({"RED","BLUE"}) do
        dojoPads[side]={}
        local sign=if side=="RED" then -1 else 1
        for _,kind in ipairs({"BEAST","WEAPON"}) do
            local pad=Instance.new("Part")
            pad.Name="PRIVATE_AUTO_DOJO_"..side.."_"..kind
            pad.Size=Vector3.new(11,0.25,11)
            pad.Position=Vector3.new(sign*56,-0.8,if kind=="BEAST" then -15 else 15)
            pad.Anchored=true;pad.CanCollide=false
            pad.CanTouch=false;pad.CanQuery=false
            pad.Material=Enum.Material.Neon
            pad.Color=if kind=="BEAST" then Color3.fromRGB(91,220,169)
                else Color3.fromRGB(242,172,83)
            pad.Transparency=0.10;pad.Parent=map.model
            pad:SetAttribute("P0DTrainingSkill",kind)
            pad:SetAttribute("FreeTraining",true)
            pad:SetAttribute("StudioSessionOnly",true)
            local billboard=Instance.new("BillboardGui")
            billboard.Name="AUTO_DOJO_SIGN"
            billboard.Size=UDim2.fromOffset(180,48)
            billboard.StudsOffsetWorldSpace=Vector3.new(0,5,0)
            billboard.MaxDistance=75;billboard.AlwaysOnTop=true
            billboard.Parent=pad
            local title=Instance.new("TextLabel")
            title.Size=UDim2.fromScale(1,1)
            title.BackgroundColor3=Color3.fromRGB(23,39,55)
            title.BackgroundTransparency=.16
            title.TextColor3=Color3.new(1,1,1)
            title.TextScaled=true
            title.TextWrapped=true
            title.Font=Enum.Font.GothamBold
            title.Text=if kind=="BEAST"
                then "🐉 まじゅう道場\\\\n乗るだけで修行"
                else "⚔ ぶき道場\\\\n乗るだけで修行"
            title.Parent=billboard
            dojoPads[side][kind]=pad
        end
    end
end
local function dojoFriendHere(player:Player): boolean
    local known=dojoFriends[player]
    if known==nil then return false end
    for _,other in ipairs(Players:GetPlayers()) do
        if other~=player and other.Parent==Players and other.UserId>0
            and known[other.UserId]==true then return true end
    end
    return false
end
'''

ONJOIN = '''    -- No manual minigame: only server records time near original team pad.
    dojoStates[player]=Dojo.new()
    dojoLastTick[player]=serverNow()
    dojoFriends[player]={}
    if RunService:IsStudio() and player.UserId>0 then
        for _,other in ipairs(Players:GetPlayers()) do
            if other~=player and other.UserId>0 then
                -- Friend check can yield: NEVER call it from the 0.5sec game tick.
                task.spawn(function()
                    local ok,isFriend=pcall(function()
                        return player:IsFriendsWith(other.UserId)
                    end)
                    if ok and isFriend and player.Parent==Players and other.Parent==Players
                        and dojoFriends[player]~=nil and dojoFriends[other]~=nil then
                        dojoFriends[player][other.UserId]=true
                        dojoFriends[other][player.UserId]=true
                    end
                end)
            end
        end
    end
'''

TICK = '''    -- The ORIGINAL Game clock alone owns auto-training; no added heartbeat/thread.
    -- A single real player stands on a mirrored home pad; session levels are not saved.
    if RunService:IsStudio() then
        for _,player in ipairs(Players:GetPlayers()) do
            local state=dojoStates[player]
            if state then
                local previous=dojoLastTick[player] or now
                dojoLastTick[player]=now
                state.current="NONE";state.friendBonus=false
                local dt=math.clamp(now-previous,0,1.5)
                local alive,root=healthy(player)
                local team=getTeamName(player)
                local pads=dojoPads[team]
                if dt>0 and alive and root and pads
                    and match.phase~="RESULTS" and carry[player]==nil
                    and root.Position.Y>=-2 and root.Position.Y<=12 then
                    for kind,pad in pairs(pads) do
                        local dx=root.Position.X-pad.Position.X
                        local dz=root.Position.Z-pad.Position.Z
                        if dx*dx+dz*dz<=36 then
                            Dojo.tick(state,kind,dt,dojoFriendHere(player),true)
                            break
                        end
                    end
                end
            end
        end
    end
'''

def patch_game(s):
 s=replace_one(s,
  'local StudioSolo = require(script.Parent:WaitForChild("StudioSoloPreviewRules"))',
  'local StudioSolo = require(script.Parent:WaitForChild("StudioSoloPreviewRules"))\n'
  'local Dojo = require(script.Parent:WaitForChild("DojoRules"))',
  "single authoritative dojo import")
 s=replace_one(s,'local map = MapBuilder.build(Config)',
   'local map = MapBuilder.build(Config)\n'+MAP_STATIONS,
   "original map 1")
 s=replace_one(s,
  '    chooseTeam(player)\n    modeVotes[player]=nil',
  '    chooseTeam(player)\n'+ONJOIN+'    modeVotes[player]=nil',
  "original player join only once")
 s=replace_one(s,
  '    guideProgress[player]=nil\n    local state=earnedPower[player]',
  '    guideProgress[player]=nil\n    dojoStates[player]=nil\n'
  '    dojoLastTick[player]=nil\n    dojoFriends[player]=nil\n'
  '    local state=earnedPower[player]',
  "original remove cleanup")
 s=replace_one(s,'    tickTraps(now)\n',
   '    tickTraps(now)\n'+TICK,"one authoritative original tick")
 s=replace_one(s,
  '        powerMinionMultiplier = earnedDamageMultiplier(player,"MINION"),',
  '        powerMinionMultiplier = earnedDamageMultiplier(player,"MINION"),\n'
  '        dojo=if RunService:IsStudio() then Dojo.view(dojoStates[player]) else nil,',
  "snapshot only server-authorized read-only dojo state")
 s=replace_one(s,
  '                *earnedDamageMultiplier(player,"MINION"),now,player.Character)',
  '                *earnedDamageMultiplier(player,"MINION")\n'
  '                *Dojo.pveDamageMultiplier(dojoStates[player],"WEAPON"),now,player.Character)',
  "PvE minion attack only; PvP damage remains original")
 s=replace_one(s,
  '                    if stage>=3 then 40 else 26,serverNow(),player.Character)',
  '                    (if stage>=3 then 40 else 26)\n'
  '                    *Dojo.pveDamageMultiplier(dojoStates[player],"BEAST"),\n'
  '                    serverNow(),player.Character)',
  "earned actual beast scout ONLY hits original Horde")
 assert s.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert s.count('remote.OnServerEvent:Connect(')==1
 assert s.count("local function tickRound()")==1
 assert s.count("local function resetRound()")==1
 assert s.count("local function stopRound(")==1
 assert s.count("Dojo.pveDamageMultiplier(")==2
 assert s.count("Dojo.tick(")==1
 assert s.count("Dojo.view(")==1
 assert s.count('local dojoPads:')==1
 assert s.count("player:IsFriendsWith(other.UserId)")==1
 assert 'hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"]\n                *earnedDamageMultiplier(player,"PLAYER"))' in s
 assert 'if not RunService:IsStudio() then' in s
 assert s.count("StudioSolo.canStart(")==2 and s.count("StudioSolo.emptyWinner(")==1
 return s

DOJO_HUD = '''-- Studio-only read-only dojo indicator, never a client XP request.
local dojoBadge=label(gui,"BeastWeaponSessionAutoDojo",
    UDim2.new(.57,0,0,48),UDim2.new(.025,0,.38,0),
    Color3.fromRGB(174,255,212),12)
dojoBadge.Visible=false
dojoBadge.Active=false
dojoBadge.Text=""
'''

def patch_hud(s):
 s=replace_one(s,
  'progressBadge.Text="Lv1 | 0/60 XP | 🎯 フォーカス1 | 🐉 熟練1"\n',
  'progressBadge.Text="Lv1 | 0/60 XP | 🎯 フォーカス1 | 🐉 熟練1"\n'+DOJO_HUD,
  "one real HUD progress badge")
 s=replace_one(s,
  '    status.Text = phaseText(s)\n',
  '''    status.Text = phaseText(s)
    local training=s.dojo
    local valid=type(training)=="table"
        and type(training.beast)=="number" and training.beast>=1
        and training.beast<=5 and training.beast%1==0
        and type(training.weapon)=="number" and training.weapon>=1
        and training.weapon<=5 and training.weapon%1==0
    local kind=if valid and (training.active=="BEAST" or training.active=="WEAPON")
        then training.active else "NONE"
    dojoBadge.Visible=valid and s.hatchEnabled==true
        and (kind~="NONE" or training.beast>1 or training.weapon>1)
    if dojoBadge.Visible then
        local prog=if type(training.xp)=="number" and training.xp>=0
            and training.xp<=40 then math.floor(training.xp) else 0
        local need=if type(training.need)=="number" and training.need>=0
            and training.need<=40 then math.floor(training.need) else 0
        local name=if kind=="BEAST" then "🐉魔獣" elseif kind=="WEAPON"
            then "⚔武器" else "道場をはなれた"
        dojoBadge.Text="魔獣 Lv"..tostring(training.beast)
            .."  武器 Lv"..tostring(training.weapon)
            .."  "..(if training.friendBonus==true then "👥×1.5" else "")
            .."\\\\n"..name.." "..tostring(prog).."/"..tostring(need)
            .." (このプレイ中 / 対NPC)"
    end
''',
  "one original authoritative snapshot render")
 assert s.count("local dojoBadge=")==1
 assert s.count("dojoBadge.Visible=valid")==1
 assert s.count("remote:FireServer(")==3
 return s
def main():
 assert not OLD.exists() and not NEW.exists(),"FAIL_CLOSED_NO_OVERWRITE"
 policy=(OWN/"inputs/DojoRules.luau").read_bytes()
 assert blob(policy)==DOJO_BLOB,"OWN_DOJO_SOURCE_DRIFT"
 subprocess.run([sys.executable,"-B",str(UP/"tools/assemble.py"),"--assemble"],
                 check=True,cwd=REPO)
 before=sources(OLD)
 assert len(before)==43
 for p,sha in [("server/MusouHorde.luau",BEFORE_HORDE),
               ("server/H1FunWorld.server.luau",BEFORE_SKY),
               ("server/StudioSoloPreviewRules.luau",BEFORE_SOLO)]:
  assert blob(before[p])==sha,(p,"UPSTREAM_DRIFT")
 assert sum(p.endswith("/Game.server.luau") for p in before)==1
 assert sum(p.endswith(".server.luau") for p in before)==2
 assert sum(p.endswith(".client.luau") for p in before)==5
 shutil.copytree(OLD,NEW)
 (NEW/"src/server/DojoRules.luau").write_bytes(policy)
 (NEW/"src/server/Game.server.luau").write_text(
     patch_game(before["server/Game.server.luau"].decode("utf8")),encoding="utf8")
 (NEW/"src/client/HUD.client.luau").write_text(
     patch_hud(before["client/HUD.client.luau"].decode("utf8")),encoding="utf8")
 after=sources(NEW)
 assert len(after)==44
 assert sorted(set(after)-set(before))==["server/DojoRules.luau"]
 assert sorted(p for p in before if after[p]!=before[p])==[
     "client/HUD.client.luau","server/Game.server.luau"]
 assert all(after[p]==before[p] for p in before
            if p not in ("server/Game.server.luau","client/HUD.client.luau"))
 assert blob(after["server/DojoRules.luau"])==DOJO_BLOB
 assert sum(p.endswith(".server.luau") for p in after)==2
 assert sum(p.endswith(".client.luau") for p in after)==5
 project=NEW/"default.project.json";d=json.loads(project.read_text("utf8"))
 assert d["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 d["name"]="P0D_B42_V7_SKY_SOLO_AUTO_DOJO_PRIVATE_UNPUBLISHED"
 project.write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n","utf8")
 receipt={
  "packet":"P0D-H1-AUTO-DOJO-20261113-01",
  "base_commit":"ebc4f58e37f8315df5a02049825811430df0e3d6",
  "source_scripts":44,"original_unchanged":41,
  "original_changed":["server/Game.server.luau","client/HUD.client.luau"],
  "new_module":["server/DojoRules.luau"],
  "new_module_blob":DOJO_BLOB,"one_Game":True,"original_Remote_only":True,
  "beast_weapon_automatic_server_pad":True,"friends_bonus":1.5,
  "max_session_level":5,"max_pve_bonus":1.2,"pvp_bonus":1.0,
  "session_only":True,"real_datastore_persistence":False,"paid":False,
  "studio2client":"NOT_TESTED","android":"NOT_TESTED",
  "owner_fun":"NOT_TESTED","official_rc_adopted":False,"published":False,
  "script_git_blobs":{k:blob(v) for k,v in sorted(after.items())}}
 (NEW/"SOURCE_LOCK.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
 print("P0D_PRIVATE_AUTO_DOJO_ONE_GAME_44_SOURCE_INTEGRATION_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--assemble",required=True,action="store_true")
 p.parse_args();main()
