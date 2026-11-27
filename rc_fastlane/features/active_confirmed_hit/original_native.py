#!/usr/bin/env python3
"""Generate native Luau tests using actual post-overlay Game.applyAttack and HUD ACK closure.
The real functions are extracted byte-for-byte from built RC80 source; only Roblox
services and the external scene/characters are mocked. Does not claim Roblox Studio QA.
"""
from __future__ import annotations
import argparse,hashlib
from pathlib import Path
# Exact 11,465-character original official FB019-V2 snapshotFor, source-pinned.
SNAPSHOT_V2_SHA256='fb8c461989ab000f912a637fd0bfb8e1e52849c2c06877c29ba46a91943a1fd2'
from apply_fb019_server_ack import read, GAME, HUD

PREFIX=r'''
-- Native executable real Game attack function. Minimal world stubs only.
local V
V=function(x,y,z)
    return setmetatable({X=x,Y=y,Z=z},{
        __sub=function(a,b) return V(a.X-b.X,a.Y-b.Y,a.Z-b.Z) end,
        __index=function(self,key)
            if key=="Magnitude" then
                return math.sqrt(self.X^2+self.Y^2+self.Z^2)
            elseif key=="Unit" then
                local m=math.sqrt(self.X^2+self.Y^2+self.Z^2)
                return if m>0 then V(self.X/m,self.Y/m,self.Z/m) else V(0,0,0)
            elseif key=="Dot" then
                return function(a,b) return a.X*b.X+a.Y*b.Y+a.Z*b.Z end
            end
            return nil
        end
    })
end
local env
local lastSeq,lastAttack,roles,match,map,Players,Rules,RunService,Config,remote,horde
local workspace,RaycastParams,Enum,SoloTeamBots,Dojo,SavedPvePolicy,First90Guide
local dojoStates,guideProgress,mobCombo,mobComboUntil,mobImpactSeq,mobLastHits,mobLastKOs
local invulnUntil,EXPERIMENTAL_FIVE_EGG_MODE
local function serverNow() return env.now end
local function getTeamName(player) return player.team end
local function snapshotFor(player)
    assert(player==env.player)
    -- This is only the native-service mock. The COMPLETE actual snapshotFor
    -- implementation is pinned byte-for-byte by the Python source SHA256
    -- check below, including all gameplay and save fields.
    return {kind="SNAPSHOT",serial=match.serial,phase=match.phase,updateId=1,
        scores={RED=match.scores.RED,BLUE=match.scores.BLUE},
        hp={RED=match.hp.RED,BLUE=match.hp.BLUE},
        musouImpactSeq=mobImpactSeq[player] or 0,
        musouLastHits=mobLastHits[player] or 0,
        musouLastKOs=mobLastKOs[player] or 0}
end
local function healthy(player)
    player.healthCalls=(player.healthCalls or 0)+1
    if not player.alive or (player.failSecond and player.healthCalls>=2)
        then return false,nil,nil end
    return true,player.root,player.hum
end
local function earnedDamageMultiplier(player,target) return 1 end
local function savedPveMinionMultiplier(player) return 1 end
local function twinBondOnlyNeutralMobBonus(player) return 1 end
local function stopRound(winner,reason) env.stopped=env.stopped+1 end
local function broadcast() env.broadcast=env.broadcast+1 end
local function setup()
    env={now=10,mobHits=0,mobKOs=0,players={},stopped=0,broadcast=0,blocked=false}
    lastSeq={}; lastAttack={}; roles={};dojoStates={};guideProgress={}
    mobCombo={};mobComboUntil={};mobImpactSeq={};mobLastHits={};mobLastKOs={}
    invulnUntil={};EXPERIMENTAL_FIVE_EGG_MODE=false
    local root={Position=V(0,0,0),CFrame={LookVector=V(1,0,0)}}
    local h={Health=100}
    function h:TakeDamage(damage) self.Health=self.Health-damage end
    env.player={team="RED",alive=true,root=root,hum=h,Character={}}
    env.players={env.player}
    map={teams={RED={core={Position=V(-40,0,0)}},
                BLUE={core={Position=V(40,0,0)}}}}
    match={phase="ACTIVE",serial=5,hp={RED=100,BLUE=100},
           scores={RED=0,BLUE=0}}
    Config={AttackReach=10,CastleReach=18,AttackCooldown=.85,
            CombatDamage={RAIDER=10},CastleAttackDamage={RAIDER=11},
            CapturesToWin=5}
    Players={GetPlayers=function(self) return env.players end}
    env.player.Parent=Players
    Rules={
        validSeq=function(seq,last) return type(seq)=="number" and seq>last end,
        opponent=function(team) return if team=="RED" then "BLUE" else "RED" end,
        damageCandidate=function(dist,aim,reach)
            return dist<=reach and aim>=.25
        end,
        canAttack=function(now,last,phase,alive,cooldown)
            return phase=="ACTIVE" and alive and now>=last+cooldown
        end,
        winner=function(scores,hp,goal) return nil end,
    }
    RunService={IsStudio=function() return true end}
    SavedPvePolicy={mergeWithEarned=function(a,b) return a end}
    Dojo={pveDamageMultiplier=function(a,b) return 1 end}
    First90Guide={mark=function(...) end}
    remote={sent={}}
    function remote:FireClient(person,packet)
        assert(person==env.player,"SERVER_ONLY_OWNER_RESPONSE")
        table.insert(self.sent,packet)
    end
    horde={hit=function(self,pos,look,damage,now,character)
        return env.mobHits,env.mobKOs
    end}
    workspace={Raycast=function(self,origin,delta,params)
        if not env.blocked then return nil end
        return {Instance={IsDescendantOf=function() return false end}}
    end}
    RaycastParams={new=function() return {} end}
    Enum={RaycastFilterType={Exclude=1}}
    SoloTeamBots={tryHumanHit=function(team,origin,look,reach,char)
        return env.bot
    end}
end
local function makeEnemy()
    local h={Health=100}
    function h:TakeDamage(x) self.Health=self.Health-x end
    env.enemy={team="BLUE",alive=true,hum=h,
        root={Position=V(5,0,0),CFrame={LookVector=V(-1,0,0)}},
        Character={}}
    table.insert(env.players,env.enemy)
    return env.enemy
end
'''
SERVER_TESTS=r'''
local checked=0
local function invoke(seq)
    applyAttack(env.player,{action="ATTACK",seq=seq or 1})
end
local function expect(status,target)
    local feedback={}
    local snapshots=0
    for _,packet in ipairs(remote.sent) do
        if packet.kind=="P0D_ATTACK_RESULT" then
            table.insert(feedback,packet)
        elseif packet.kind=="SNAPSHOT" then
            assert(packet.serial==match.serial and packet.phase==match.phase)
            assert(packet.updateId==1)
            assert(packet.hp.RED==match.hp.RED and packet.hp.BLUE==match.hp.BLUE)
            assert(packet.scores.RED==match.scores.RED and packet.scores.BLUE==match.scores.BLUE)
            assert(packet.musouImpactSeq==(mobImpactSeq[env.player] or 0))
            assert(packet.musouLastHits==(mobLastHits[env.player] or 0))
            assert(packet.musouLastKOs==(mobLastKOs[env.player] or 0))
            snapshots+=1
        else error("UNEXPECTED_REMOTE_PAYLOAD") end
    end
    assert(snapshots==(if env.mobHits>0 then 1 else 0),"V2_REAL_HIT_SNAPSHOT_MISSING")
    if status=="NONE" then
        assert(#feedback==0,"REJECTED_ATTACK_MUST_NOT_SEND_RESULT")
    else
        assert(#feedback==1,"EACH_ACCEPTED_ATTACK_EXACTLY_ONE_RESULT")
        local packet=feedback[1]
        assert(packet.kind=="P0D_ATTACK_RESULT","WRONG_PACKET")
        assert(packet.status==status and packet.target==target,
            "WRONG_ACK_"..tostring(packet.status).."/"..tostring(packet.target))
        assert(packet.serial==match.serial and packet.seq==1,"UNBOUND_ACK")
    end
    checked+=1
end
setup()
invoke()
expect("MISS","NONE")
setup()
env.mobHits=1
invoke()
expect("HIT","MINION")
setup()
local victim=makeEnemy()
invoke()
expect("HIT","PLAYER")
assert(victim.hum.Health==90,"ACTUAL_PLAYER_HP_NOT_CHANGED")
setup()
victim=makeEnemy()
function victim.hum:TakeDamage(dmg) end -- immune ForceField mock, real zero HP delta
invoke()
expect("MISS","NONE")
assert(victim.hum.Health==100,"IMMUNE_PLAYER_NO_DAMAGE")
setup()
victim=makeEnemy()
victim.failSecond=true
invoke()
expect("MISS","NONE")
assert(victim.hum.Health==100,"STALE_VICTIM_MUST_NOT_TAKE_DAMAGE")
setup()
victim=makeEnemy()
victim.failSecond=true
env.mobHits=1
invoke()
expect("HIT","MINION")
setup()
local botHum={Health=100}
function botHum:TakeDamage(damage) self.Health-=damage end
env.bot={hum=botHum}
invoke()
expect("HIT","BOT")
assert(botHum.Health==90,"ACTUAL_BOT_HP_NOT_CHANGED")
setup()
botHum={Health=100}
function botHum:TakeDamage(dmg) end
env.bot={hum=botHum}
invoke()
expect("MISS","NONE")
assert(botHum.Health==100,"IMMUNE_BOT_NO_DAMAGE")
setup()
map.teams.BLUE.core.Position=V(6,0,0)
invoke()
expect("HIT","CASTLE")
assert(match.hp.BLUE==89,"ACTUAL_CASTLE_HP_NOT_CHANGED")
setup()
map.teams.BLUE.core.Position=V(6,0,0)
Config.CastleAttackDamage.RAIDER=0
invoke()
expect("MISS","NONE")
assert(match.hp.BLUE==100,"IMMUNE_CASTLE_NO_DAMAGE")
setup()
map.teams.BLUE.core.Position=V(6,0,0)
env.blocked=true
invoke()
expect("MISS","BLOCKED")
assert(match.hp.BLUE==100,"BLOCKED_CASTLE_MUST_NOT_TAKE_DAMAGE")
setup()
match.phase="LOBBY"
invoke()
expect("NONE")
setup()
invoke()
expect("MISS","NONE")
remote.sent={}
invoke()
expect("NONE") -- replay sequence
setup()
lastAttack[env.player]=10
invoke()
expect("NONE") -- cooldown
setup()
env.player.alive=false
invoke()
expect("NONE") -- dead
setup()
env.player.team="NONE"
invoke()
expect("NONE") -- spectator
setup()
env.mobHits=1
map.teams.BLUE.core.Position=V(6,0,0)
invoke()
expect("HIT","MINION")
assert(match.hp.BLUE==100,"MOB_HIT_MUST_NOT_DUPLICATE_CASTLE_DAMAGE")
print("FB019_NATIVE_REAL_GAME_ATTACK_PATHS_PASS",checked)
'''
HUD_SETUP=r'''
-- Original HUD callback extracted without modification, mocked only its UI deps.
local attack={Text="⚔ 攻撃",BackgroundColor3="original",Visible=true,Parent={}}
local lastSerial=5
local queue={}
local task={delay=function(duration,callback)
    assert(duration==.28,"ONLY_TRANSIENT_CUE")
    table.insert(queue,callback)
end}
local Color3={fromRGB=function(r,g,b) return {r,g,b} end}
local listener
remote.OnClientEvent={Connect=function(self,callback)
    assert(listener==nil,"ONE_NEW_HUD_ACK_HANDLER")
    listener=callback
end}
'''
HUD_TESTS=r'''
local function ack(status,seq,serial)
    listener({kind="P0D_ATTACK_RESULT",status=status,seq=seq,
              serial=serial or 5,target="NONE"})
end
assert(type(listener)=="function","HUD_HANDLER_NOT_CONNECTED")
ack("HIT",1)
assert(attack.Text=="⚔ 命中!","HUD_HIT_WAS_NOT_DISPLAYED")
for _,cb in ipairs(queue) do cb() end
queue={}
assert(attack.Text=="⚔ 攻撃","HIT_CUE_DID_NOT_REVERT")
ack("MISS",2)
assert(attack.Text=="⚔ 空振り","HUD_MISS_WAS_NOT_DISPLAYED")
for _,cb in ipairs(queue) do cb() end
queue={}
assert(attack.Text=="⚔ 攻撃","MISS_CUE_DID_NOT_REVERT")
ack("HIT",1)
assert(attack.Text=="⚔ 攻撃","STALE_SEQ_SHOULD_IGNORE")
ack("HIT",3,4)
assert(attack.Text=="⚔ 攻撃","STALE_SERIAL_SHOULD_IGNORE")
attack.Visible=false
ack("HIT",3)
assert(attack.Text=="⚔ 攻撃","HIDDEN_UI_SHOULD_IGNORE")
attack.Visible=true
listener({kind="SNAPSHOT",seq=3,serial=5,status="HIT"})
assert(attack.Text=="⚔ 攻撃","WRONG_KIND_SHOULD_IGNORE")
print("FB019_NATIVE_REAL_HUD_ACK_CUES_PASS",6)
'''
def generate(dist:Path,out:Path):
    src=read(dist)
    assert len(src)==80
    game=src[GAME].decode("utf8")
    hud=src[HUD].decode("utf8")
    start="local function applyAttack(player: Player, data)"
    end="-- H1 RAIDER wind:"
    assert game.count(start)==game.count(end)==1
    block=game[game.index(start):game.index(end,game.index(start))]
    snapanchor="snapshotFor = function(player: Player)"
    assert game.count(snapanchor)==1
    snapstart=game.index(snapanchor)
    snapend=game.index("\nend\n",snapstart)+len("\nend")
    real_snapshot=game[snapstart:snapend]
    # Proves the FULL actual original snapshot builder (all 80+ fields, not
    # just this small executable mock) is unchanged vs the formal RC.
    assert hashlib.sha256(real_snapshot.encode("utf8")).hexdigest()==SNAPSHOT_V2_SHA256, "REAL_SNAPSHOT_PAYLOAD_SOURCE_DRIFT"
    for field in ('kind = "SNAPSHOT"', 'serial = match.serial',
                  'phase = match.phase', 'updateId = snapshotUpdateId',
                  'scores = {RED = match.scores.RED, BLUE = match.scores.BLUE}',
                  'hp = {RED = match.hp.RED, BLUE = match.hp.BLUE}',
                  'musouImpactSeq = mobImpactSeq[player] or 0',
                  'musouLastHits = mobLastHits[player] or 0',
                  'musouLastKOs = mobLastKOs[player] or 0'):
        assert field in real_snapshot,("SNAPSHOT_EXPECTED_FULL_CONTRACT",field)
    assert "kind=\"P0D_ATTACK_RESULT\"" in block
    assert 'remote:FireClient(player,snapshotFor(player))' in block
    assert "if ok and hum and hum.Health>0 then" in block
    assert "attackResponse(\"MISS\",\"NONE\")" in block
    cstart="local originalAttackText = attack.Text"
    cend="trapButton.MouseButton1Click:Connect"
    assert hud.count(cstart)==hud.count(cend)==1
    cue=hud[hud.index(cstart):hud.index(cend,hud.index(cstart))]
    assert "lastAttackFeedbackSeq" in cue
    assert "remote.OnClientEvent:Connect" in cue
    payload="\n".join((PREFIX,block,SERVER_TESTS,HUD_SETUP,cue,HUD_TESTS))
    assert not out.exists(),"NO_OVERWRITE_NATIVE_SCRIPT"
    out.write_text(payload,"utf8")
    print("FB019_NATIVE_GENERATED_FROM_REAL80_GAME_AND_HUD",len(payload))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args()
    generate(a.dist,a.out)
