#!/usr/bin/env python3
"""FB-007: physical lobby/dojo separation from the CURRENT assembled RC66.

A-PREP only. Never touch canonical RC directly. Existing Game remains sole
authority; V4 still uses the original scheduler, Model and saved-profile rules.
OFF is a strict no-op. All 66 original source gitblobs validated before ON.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parent
MODULE=ROOT/"features/fb007_lobby/LobbyDojoIsland.luau"
MODULE_BLOB="0ea8a0957841bcbd92def235726cc9a21be1231f"
FEATURE="FB007_LOBBY_DOJO_PHYSICAL_V1"
GAME="server/Game.server.luau"
V4="server/V4TrainingBridge.server.luau"
DEST="server/LobbyDojoIsland.luau"

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def replace1(s:str, old:str, new:str)->str:
    count=s.count(old)
    assert count==1,("FB007_SOURCE_ANCHOR_CHANGED",old[:110],count)
    return s.replace(old,new,1)

def patch_game(source:str)->str:
    assert FEATURE not in source,"DOJO_PATCH_ALREADY_INSTALLED"
    s=replace1(source,
       'local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))',
       'local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))\n'
       'local LobbyIsland = require(script.Parent:WaitForChild("LobbyDojoIsland"))')
    s=replace1(s,'local map = MapBuilder.build(Config)',
       'local map = MapBuilder.build(Config)\n'
       '-- FB007_LOBBY_DOJO_PHYSICAL_V1: build BEFORE joins/spawns.\n'
       'if RunService:IsStudio() then LobbyIsland.build(map.model) end')
    s=replace1(s,
       'pad.Position=Vector3.new(sign*56,-0.8,if kind=="BEAST" then -15 else 15)',
       'pad.Position=LobbyIsland.padPosition(side,kind)')
    s=replace1(s,
       'and match.phase~="RESULTS" and carry[player]==nil\n'
       '                    and root.Position.Y>=-2 and root.Position.Y<=12 then',
       'and match.phase=="LOBBY" and carry[player]==nil\n'
       '                    and root.Position.Y>=41 and root.Position.Y<=55 then')
    s=replace1(s,'broadcast = function()\n',
       'broadcast = function()\n'
       '    -- Server-authenticated phase feed; Studio V4 cannot invent match state.\n'
       '    map.model:SetAttribute("P0D_PHASE",match.phase)\n')
    marker='local function assignSpawn(player: Player, character: Model)'
    assert s.count(marker)==1,"ASSIGN_SPAWN_AMBIGUOUS"
    before,spawn=s.split(marker,1)
    spawn=replace1(spawn,'root.CFrame = map.teams[team].spawn + Vector3.new(0, 2, 0)',
        'root.CFrame = if RunService:IsStudio() and match.phase~="ACTIVE"\n'
        '                then LobbyIsland.spawn(team)\n'
        '                else map.teams[team].spawn + Vector3.new(0, 2, 0)')
    s=before+marker+spawn
    tickmarker='local function tickRound()'
    assert s.count(tickmarker)==1,"TICK_ROUND_AMBIGUOUS"
    head,tick=s.split(tickmarker,1)
    tick=replace1(tick,
        'match.phase = "LOBBY"\n            match.winner = ""',
        '''match.phase = "LOBBY"
            -- Move real players to the separated lobby AFTER result display.
            if RunService:IsStudio() then
                for _,p in ipairs(Players:GetPlayers()) do
                    local team=getTeamName(p)
                    local alive,root=healthy(p)
                    if alive and root and (team=="RED" or team=="BLUE") then
                        root.AssemblyLinearVelocity=Vector3.zero
                        root.AssemblyAngularVelocity=Vector3.zero
                        root.CFrame=LobbyIsland.spawn(team)
                    end
                end
            end
            match.winner = ""''')
    tick=replace1(tick,
        'if position.Y < -30 or math.abs(position.X) > 130\n'
        '                or math.abs(position.Z) > 76 then',
        '''if (match.phase=="ACTIVE" and (position.Y < -30
                or math.abs(position.X) > 130 or math.abs(position.Z) > 76))
                or (RunService:IsStudio()
                and (match.phase=="LOBBY" or match.phase=="COUNTDOWN")
                and not LobbyIsland.inLobby(position)) then''')
    tick=replace1(tick,
       'root.CFrame = map.teams[team].spawn + Vector3.new(0, 4, 0)',
       'root.CFrame = if RunService:IsStudio() and match.phase~="ACTIVE"\n'
       '                        then LobbyIsland.spawn(team)\n'
       '                        else map.teams[team].spawn + Vector3.new(0, 4, 0)')
    s=head+tickmarker+tick
    assert s.count('remote.OnServerEvent:Connect(')==1
    assert s.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert s.count('Dojo.tick(')==1
    assert s.count('local function tickRound()')==1
    return s

def patch_v4(source:str)->str:
    assert FEATURE not in source,"V4_PATCH_ALREADY_INSTALLED"
    s=replace1(source,
       'local Model = require(script.Parent:WaitForChild("SessionSixSkillXPPreview"))',
       'local Model = require(script.Parent:WaitForChild("SessionSixSkillXPPreview"))\n'
       'local LobbyIsland = require(script.Parent:WaitForChild("LobbyDojoIsland"))')
    s=replace1(s,
       '''local positions = {
    BEAST={56,-15}, WEAPON={56,15},
    MAGIC={54,-49}, ZOMBIE={54,49},
    VEHICLE={74,-49}, BUILDING={74,49}
}
''',
       '-- All 12 physical pads share the same lobby coordinate authority.\n')
    s=replace1(s,
       '        local at = positions[skill]\n'
       '        local pad = Instance.new("Part")',
       '        local pad = Instance.new("Part")')
    s=replace1(s,
       'pad.Position = Vector3.new(sign*at[1],-0.74,at[2])',
       'pad.Position = LobbyIsland.padPosition(side,skill)')
    s=replace1(s,
       'local function standingOn(player)\n',
       'local function standingOn(player)\n'
       '    if arena:GetAttribute("P0D_PHASE")~="LOBBY" then return nil end\n')
    s=replace1(s,
       '        local at=positions[skill]\n'
       '        local px,pz=sign*at[1],at[2]',
       '        local at=LobbyIsland.padPosition(team,skill)\n'
       '        local px,pz=at.X,at.Z')
    s=replace1(s,
       'math.abs(root.Position.Y-1)<10',
       'math.abs(root.Position.Y-45)<10')
    assert s.count('Scheduler.settle(')==1
    assert s.count('Model.apply(')==1
    assert s.count('player:IsFriendsWithAsync(other.UserId)')==1
    assert 'NoSavedXP' in s and 'NoCombatBuff' in s
    assert not any(z in s for z in ('Instance.new("RemoteEvent")','DataStoreService','MarketplaceService'))
    return s

def sources(dist:Path)->dict[str,bytes]:
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes() for p in sorted(root.rglob("*.luau"))}

def apply(dist:Path,enabled:bool)->bool:
    if not enabled:
        print("FB007_OFF_BYTE_IDENTICAL_ALL_SOURCE_AND_LOCKS")
        return False
    raw=MODULE.read_bytes()
    assert blob(raw)==MODULE_BLOB, "LOBBY_MODULE_SOURCE_DRIFT"
    before=sources(dist)
    assert len(before)==66,("REQUIRES_OFFICIAL66",len(before))
    assert GAME in before and V4 in before and DEST not in before
    original={p:blob(b) for p,b in sorted(before.items())}
    lp=dist/"SOURCE_LOCK.json";fp=dist/"RC_FEATURE_LOCK.json"
    lk=json.loads(lp.read_text("utf8"));fl=json.loads(fp.read_text("utf8"))
    assert lk["total_scripts"]==66 and lk["blobs"]==original
    assert fl["total_sources"]==66 and fl["source_gitblobs"]==original
    assert FEATURE not in fl["feature_flags"]
    proj=json.loads((dist/"default.project.json").read_text("utf8"))
    assert proj["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    text_game=patch_game(before[GAME].decode("utf8"))
    text_v4=patch_v4(before[V4].decode("utf8"))
    after={**before,GAME:text_game.encode("utf8"),V4:text_v4.encode("utf8"),DEST:raw}
    assert len(after)==67
    assert {p for p in before if after[p]!=before[p]}=={GAME,V4}
    assert all(before[p]==after[p] for p in before if p not in (GAME,V4))
    pins={p:blob(b) for p,b in sorted(after.items())}
    lk["total_scripts"]=67;lk["blobs"]=pins
    lk["rc_fb007_physical_lobby"]={
        "id":FEATURE,"modified":[GAME,V4],"added":[DEST],
        "original_64_unchanged":True,"single_Game_Remote_Store":True,
        "no_new_XP_or_Damage_owner":True,
        "studio_engine":"NOT_TESTED","two_client":"NOT_TESTED",
        "owner_fun":"NOT_TESTED",
        "rollback":"omit FB007 overlay, preserve exact prior66",
    }
    fl["total_sources"]=67;fl["source_gitblobs"]=pins
    fl["feature_flags"][FEATURE]=True
    (dist/"src"/GAME).write_text(text_game,encoding="utf8")
    (dist/"src"/V4).write_text(text_v4,encoding="utf8")
    (dist/"src"/DEST).write_bytes(raw)
    lp.write_text(json.dumps(lk,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    fp.write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    assert sources(dist)==after
    print("FB007_LOBBY_DOJO_67_SOURCE_TWO_PATCH_ONE_MODULE_64_OLD_SCRIPTS_EXACT")
    return True

if __name__=="__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("--dist",type=Path,required=True)
    cli.add_argument("--enabled",choices=("true","false"),required=True)
    args=cli.parse_args()
    apply(args.dist,args.enabled=="true")
