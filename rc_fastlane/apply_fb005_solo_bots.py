#!/usr/bin/env python3
"""FB-005: source-exact Game-only bot transactions + physical Studio agents.
One ORIGINAL Game writes egg, score, HP, winner.  Bot module only navigates and
submits local server callbacks. OFF does not touch 66-source dist.
This FIRST slice supports ORIGINAL CLASSIC one-egg Solo only, not H2 five-egg.
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
MODULE=ROOT/"features/fb005_solo/SoloTeamBots.luau"
MODULE_BLOB="9e52ab2636058858dc2d0bc000b5e9fd2bb9e88f"
ID="FB005_STUDIO_SOLO_TEAM_BOTS_CLASSIC_V1"
GAME="server/Game.server.luau"
DEST="server/SoloTeamBots.luau"
def blob(b:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def sub(s:str,a:str,b:str)->str:
    assert s.count(a)==1,("FB005_GAME_AUTHORITY_DRIFT",a[:130],s.count(a))
    return s.replace(a,b,1)
def sources(dist:Path)->dict[str,bytes]:
    root=dist/"src"
    return {p.relative_to(root).as_posix():p.read_bytes() for p in sorted(root.rglob("*.luau"))}

BOT_CALLBACKS = '''-- FB005: Bot requests are local SERVER callbacks to ORIGINAL Game, not a Remote.
-- Standard S1 classic egg transaction rules remain authoritative for humans.
local botAuthority={
    steal=function(bot,eggTeam)
        if match.phase~="ACTIVE" or EXPERIMENTAL_FIVE_EGG_MODE
            or (bot.team~="RED" and bot.team~="BLUE")
            or bot.team==eggTeam or botEggOwners[eggTeam]~=nil
            or match.eggOwners[eggTeam]~=nil then return false end
        local egg=map.teams[eggTeam].egg
        if (bot.root.Position-egg.Position).Magnitude>Config.InteractDistance then return false end
        botEggOwners[eggTeam]=bot.id
        map.teams[eggTeam].egg.Transparency=1
        map.teams[eggTeam].eggPrompt.Enabled=false
        broadcast()
        return true
    end,
    drop=function(bot,eggTeam)
        if botEggOwners[eggTeam]~=bot.id then return end
        botEggOwners[eggTeam]=nil
        resetEgg(eggTeam)
    end,
    deposit=function(bot,homeTeam,eggTeam)
        if match.phase~="ACTIVE" or EXPERIMENTAL_FIVE_EGG_MODE
            or bot.team~=homeTeam or eggTeam==homeTeam
            or botEggOwners[eggTeam]~=bot.id
            or match.eggOwners[homeTeam]~=nil
            or botEggOwners[homeTeam]~=nil then return false end
        if (bot.root.Position-map.teams[homeTeam].scorePad.Position).Magnitude>
            Config.InteractDistance then return false end
        botEggOwners[eggTeam]=nil
        resetEgg(eggTeam)
        match.scores[homeTeam]+=1
        local winner=Rules.winner(match.scores,match.hp,Config.CapturesToWin)
        if winner then stopRound(winner,"STUDIO_BOT_EGG_CAPTURE")
        else broadcast() end
        return true
    end,
    attackHuman=function(bot,target,amount)
        if match.phase~="ACTIVE" or EXPERIMENTAL_FIVE_EGG_MODE
            or target.Team==nil or target.Team.Name==bot.team then return end
        local ok,root,hum=healthy(target)
        if not ok or not root or not hum
            or serverNow()<(invulnUntil[target] or 0)
            or (bot.root.Position-root.Position).Magnitude>8 then return end
        local params=RaycastParams.new()
        params.FilterType=Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances={bot.model}
        local hit=workspace:Raycast(bot.root.Position,root.Position-bot.root.Position,params)
        if hit and (not target.Character
            or not hit.Instance:IsDescendantOf(target.Character)) then return end
        hum:TakeDamage(math.clamp(amount,1,10))
    end,
    attackBot=function(bot,target,amount)
        if match.phase~="ACTIVE" or EXPERIMENTAL_FIVE_EGG_MODE or
            bot.team==target.team or not target.hum or target.hum.Health<=0
            or (bot.root.Position-target.root.Position).Magnitude>8 then return end
        local params=RaycastParams.new()
        params.FilterType=Enum.RaycastFilterType.Exclude
        params.FilterDescendantsInstances={bot.model}
        local hit=workspace:Raycast(bot.root.Position,
            target.root.Position-bot.root.Position,params)
        if hit and not hit.Instance:IsDescendantOf(target.model) then return end
        target.hum:TakeDamage(math.clamp(amount,1,10))
    end,
}

'''
def patch_game(text:str)->str:
    assert ID not in text, "BOT_PATCH_DUPLICATED"
    text=sub(text,
        'local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))',
        'local MapBuilder = require(script.Parent:WaitForChild("MapBuilder"))\n'
        'local SoloTeamBots = require(script.Parent:WaitForChild("SoloTeamBots"))\n'
        '-- '+ID)
    text=sub(text,'local match = {',
        'local botEggOwners: {[string]: string} = {}\nlocal match = {')
    text=sub(text,
        '    match.eggOwners[team] = nil\n    map.teams[team].egg.Transparency = 0',
        '    match.eggOwners[team] = nil\n    botEggOwners[team]=nil\n'
        '    map.teams[team].egg.Transparency = 0')
    text=sub(text,'else match.eggOwners[name] == nil)',
        'else match.eggOwners[name] == nil and botEggOwners[name] == nil)')
    text=sub(text,
        'local free = match.eggOwners[team] == nil',
        'local free = match.eggOwners[team] == nil and botEggOwners[team] == nil')
    text=sub(text,
        'local ownEggHome = match.eggOwners[team] == nil',
        'local ownEggHome = match.eggOwners[team] == nil and botEggOwners[team] == nil')
    text=sub(text,
        '    match.phase = "RESULTS"\n    match.phaseUntil = serverNow() + Config.ResultsSeconds',
        '    match.phase = "RESULTS"\n    SoloTeamBots.stop()\n'
        '    match.phaseUntil = serverNow() + Config.ResultsSeconds')
    text=sub(text,
        'local function resetRound()',
        BOT_CALLBACKS+'local function resetRound()')
    text=sub(text,
        'local function resetRound()\n    stopCanonical("ROUND_RESET")',
        'local function resetRound()\n    SoloTeamBots.stop()\n    stopCanonical("ROUND_RESET")')
    text=sub(text,
        '    match.eggOwners = {}',
        '    match.eggOwners = {}\n    table.clear(botEggOwners)')
    text=sub(text,
        '    setObjectiveEnabled(true)',
        '''    setObjectiveEnabled(true)
    -- Studio practice gets actual red/blue humanoid players; not five-egg mode.
    -- Deferral prevents spawn/reset and captures from overlapping this callback.
    if RunService:IsStudio() and studioSoloRoundStarted
        and not EXPERIMENTAL_FIVE_EGG_MODE then
        task.defer(function()
            if match.phase=="ACTIVE" and #Players:GetPlayers()==1 then
                local player=Players:GetPlayers()[1]
                local ok,started=pcall(SoloTeamBots.start,map,getTeamName(player),botAuthority)
                if not ok or started~=true then
                    warn("FB005_SOLO_START_FAIL_CLOSED",started)
                    SoloTeamBots.stop()
                    -- Never leave a player trapped in an ACTIVE but empty
                    -- solo match after a soft-fail (false) or hard exception.
                    if match.phase=="ACTIVE" and studioSoloRoundStarted
                        and #Players:GetPlayers()==1 then
                        stopRound("DRAW","SOLO_BOTS_NOT_READY")
                    end
                end
            end
        end)
    end''')
    text=sub(text,
        '    local enemy = Rules.opponent(team)',
        '''    -- Human can really hurt an enemy humanoid BOT within the same
    -- server-authorized seq/cooldown/phase and attack reach.
    if RunService:IsStudio() and not EXPERIMENTAL_FIVE_EGG_MODE then
        local victim=SoloTeamBots.tryHumanHit(team,root.Position,look,
            Config.AttackReach,player.Character)
        if victim and victim.hum and victim.hum.Health>0 then
            victim.hum:TakeDamage(Config.CombatDamage[roles[player] or "RAIDER"])
            return
        end
    end
    local enemy = Rules.opponent(team)''')
    text=sub(text,
        '        for _,impact in ipairs(horde:tick(now,Players:GetPlayers(),healthy)) do',
        '''        -- The same ORIGINAL Game tick drives Studio bots. No second match loop.
        if not EXPERIMENTAL_FIVE_EGG_MODE then
            local ok,err=pcall(SoloTeamBots.tick,now)
            if not ok then
                warn("FB005_SOLO_TICK_FAIL_CLOSED",err)
                SoloTeamBots.stop()
                -- Do not strand a solo player in an ACTIVE game with no opponents.
                if studioSoloRoundStarted and match.phase=="ACTIVE"
                    and #Players:GetPlayers()==1 then
                    stopRound("DRAW","SOLO_BOTS_TICK_FAILURE")
                end
                return
            end
        end
        for _,impact in ipairs(horde:tick(now,Players:GetPlayers(),healthy)) do''')
    assert text.count('remote.OnServerEvent:Connect(')==1
    assert text.count('local function resetRound()')==1
    assert text.count('local function tickRound()')==1
    assert text.count('pcall(SoloTeamBots.tick,now)')==1
    assert text.count('pcall(SoloTeamBots.start,map,')==1
    return text

def apply(dist:Path,enabled:bool)->bool:
    if not enabled:
        print("FB005_BOTS_OFF_EXACT_ZERO_WRITES")
        return False
    module=MODULE.read_bytes()
    assert blob(module)==MODULE_BLOB,"BOT_AUTHOR_SOURCE_DRIFT"
    s=module.decode("utf8")
    for term in ('Bot.start(', 'Bot.tick(', 'Bot.tryHumanHit(', 'Bot.stop()',
        'PathfindingService:CreatePath(', 'Humanoid', 'FB005_STUDIO_REAL_TEAM_BOTS',
        'MAX_BOTS=5','callbacks.steal(', 'callbacks.deposit(', 'callbacks.drop('):
        assert term in s,("BOT_SOURCE_REQUIRED",term)
    for forbidden in ('Instance.new("RemoteEvent")','OnServerEvent:Connect(',
                      'DataStoreService','MarketplaceService','UpdateAsync(',
                      'PromptProductPurchase('):
        assert forbidden not in s,("BOT_FORBIDDEN_SECOND_AUTHORITY",forbidden)
    original=sources(dist)
    assert len(original)==66,("REQUIRE_OFFICIAL66",len(original))
    assert GAME in original and DEST not in original
    pins={p:blob(v) for p,v in sorted(original.items())}
    lp=dist/"SOURCE_LOCK.json";fp=dist/"RC_FEATURE_LOCK.json"
    l=json.loads(lp.read_text("utf8"));f=json.loads(fp.read_text("utf8"))
    assert l["total_scripts"]==66 and l["blobs"]==pins,"SOURCE66_MISMATCH"
    assert f["total_sources"]==66 and f["source_gitblobs"]==pins,"FEATURE66_MISMATCH"
    assert ID not in f["feature_flags"]
    game=patch_game(original[GAME].decode("utf8")).encode("utf8")
    after={**original,GAME:game,DEST:module}
    assert len(after)==67
    assert {p for p in original if after[p]!=original[p]}=={GAME}
    newpins={p:blob(v) for p,v in sorted(after.items())}
    l["total_scripts"]=67;l["blobs"]=newpins
    l["fb005_bots"]={
        "id":ID,"source_added":DEST,"source_modified":GAME,
        "65_original_scripts_unchanged":True,
        "server_game_writes_eggs_hp_and_score":True,
        "solo_classic_only":True,
        "five_egg_ai":"NOT_SUPPORTED",
        "studio_physics":"NOT_TESTED",
        "human_fun":"FUN_NO_GO",
        "rollback":"omit optional post-assembly FB005 adapter"
    }
    f["total_sources"]=67;f["source_gitblobs"]=newpins
    f["feature_flags"][ID]=True
    (dist/"src"/GAME).write_bytes(game)
    (dist/"src"/DEST).write_bytes(module)
    lp.write_text(json.dumps(l,ensure_ascii=False,indent=2)+"\n","utf8")
    fp.write_text(json.dumps(f,ensure_ascii=False,indent=2)+"\n","utf8")
    assert sources(dist)==after
    print("FB005_SOLO_TEAM_AI_GAME_ONLY_AUTHORITY_PRIVATE67_SOURCE_LOCK_PASS")
    return True
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    args=p.parse_args()
    apply(args.dist,args.enabled=="true")
