"""Run the exact ACTIVE departure, result, READY and kickoff bodies in Luau."""
import argparse
import re
from pathlib import Path

from apply_active_h2_exit import CALLBACK, REASON, split_callback
from apply_active_solo_bots import GAME


def extract(source, header):
    assert source.count(header) == 1, header
    tail = source.split(header,1)[1]
    end = re.search(r'(?m)^end$', tail)
    assert end, header
    return header + tail[:end.end()]


TABLES = '''lastFreeHatch persistenceState persistentProfiles delayedRestore progressionProfile
progressionRound progressionEvents progressionStatus progressionLastAward evolutionPending
guideProgress dojoStates dojoLastTick v4WindowStart v4WindowSkill v4SavePending dojoFriends
earnedPower h2Ids modeVotes lastModeVote traps roles sevenJobs sevenJobLastChoose sevenJobLastUse
lastSeq relayAcceptedSeq lastAttack lastRoleChange lastTrap lastWind lastNet netImmuneUntil
mobCombo mobComboUntil mobImpactSeq mobLastHits mobLastKOs windUntil windHighlight invulnUntil
roundReady lobbyRecoveryRound profileFailure equipNotice relayVersions relayLastAt roundEligible rewardState'''.split()

SETUP = r'''
local studio,now,online=true,100,{}
local Players={PlayerRemoving={}}
local remove
function Players:GetPlayers() return online end
function Players.PlayerRemoving:Connect(cb) remove=cb end
local RunService={IsStudio=function() return studio end}
local teamInstances={RED={Name="RED"},BLUE={Name="BLUE"}}
local function makePlayer(side,spectator)
    local player={Parent=Players,Team=teamInstances[side],root={},loaded=0}
    function player:GetAttribute(key) return key=="P0D_LateJoinSpectator" and spectator end
    function player:LoadCharacter() self.loaded+=1 end
    return player
end
local red,blue,redTwo,observer,taggedObserver,neutral=makePlayer("RED"),makePlayer("BLUE"),
    makePlayer("RED"),makePlayer("NONE",true),makePlayer("RED",true),makePlayer("NONE")
local match,h2ScoreState,lastOutcome,progressMode
local settled,hatches,closed,hordeStarts,broadcasts=0,0,0,0,0
local objective,EXPERIMENTAL_FIVE_EGG_MODE,studioSoloRoundStarted=true,true,false
local canonicalHost=nil
local botEggOwners,botAuthority={},{}
local botStarts=0
local SoloTeamBots={stop=function() end,start=function()
    botStarts+=1
    return true
end}
local task={defer=function(callback) callback() end}
local Config={ResultsSeconds=8,IntermissionSeconds=4,MinPlayers=2,MatchSeconds=900,CastleMaxHp=300}
local function serverNow() return now end
local function noOp() end
local cleanupScout,clearEarnedPowerVisual,stopWind,restoreSlow=noOp,noOp,noOp,noOp
local clearTraps,dropEgg,restoreSavedProfile,resetEgg,startCanonical=noOp,noOp,noOp,noOp,noOp
local function stopCanonical(reason) if reason=="ROUND_END" then closed+=1 end end
local function settleProgressAtRealEnd(winner) settled+=1;lastOutcome=winner end
local function giveFreeHatchAtRealEnd() hatches+=1 end
local function setObjectiveEnabled(new) objective=new end
local function broadcast() broadcasts+=1 end
local function beginProgressRounds(mode) progressMode=mode end
local RewardRules={startRound=function() return true end}
local First90Guide={newRound=function(serial) return serial end}
local Power={endRound=noOp}
local horde={clear=noOp,reset=function() hordeStarts+=1 end}
local function chooseTeam() error("OBSERVERS_ARE_NOT_IN_THE_REPLAY_FIXTURE") end
local rebalanceLobbyTeams=noOp
local function healthy(p) return true,p.root end
local Vector3={new=function() return 1 end,zero=0}
local CFrame={new=noOp}
local map={teams={RED={spawn=1},BLUE={spawn=2}}}
local h2Eggs={{id="R1",part={},prompt={}},{id="R2",part={},prompt={}},
    {id="B1",part={},prompt={}},{id="B2",part={},prompt={}},{id="N1",part={},prompt={}}}
'''

CHECKS = r'''
local function reset(roster,isStudio,isH2,phase)
    online,studio,now=roster,isStudio,100
    match={phase=phase or "ACTIVE",serial=8,startedAt=70,deadline=310,phaseUntil=108,
        winner="",reason="",scores={RED=19,BLUE=7},hp={RED=240,BLUE=145}}
    EXPERIMENTAL_FIVE_EGG_MODE,studioSoloRoundStarted=isH2,false
    h2ScoreState=if isH2 then H2Score.new() else nil
    table.clear(roundReady);table.clear(lastSeq);table.clear(modeVotes);table.clear(lobbyRecoveryRound)
    for _,p in ipairs(online) do roundReady[p]=true;modeVotes[p]=ModeVote.SCORE;p.loaded=0 end
    settled,hatches,closed,hordeStarts,broadcasts,botStarts=0,0,0,0,0,0
    objective,lastOutcome,progressMode=true,nil,nil
end
local function report(name,condition)
    print((if condition then "PASS:" else "FAIL:")..name)
end
local function draw()
    return match.phase=="RESULTS" and match.winner=="DRAW" and match.reason=="REASON"
        and lastOutcome=="DRAW"
end

reset({red,blue,observer},true,true)
local scoreTable,h2State=match.scores,h2ScoreState
remove(red)
report("H2_TWO_TO_ONE_BEFORE_ROSTER_DROP", draw())
report("SOLE_RESULT_PRESERVES_SCORE_AND_MODE", settled==1 and hatches==1 and closed==1
    and not objective and match.scores==scoreTable and match.scores.RED==19 and match.scores.BLUE==7
    and EXPERIMENTAL_FIVE_EGG_MODE and h2ScoreState==h2State and H2Score.assertConserved(h2ScoreState)
    and roundReady[blue]==false and match.serial==8)
online={blue}
remove(red)
report("DUPLICATE_REMOVAL_CANNOT_AWARD_AGAIN", settled==1 and hatches==1 and closed==1)
now=match.phaseUntil-1
tickRoundFlow(now)
report("RESULTS_WAIT_OUT_SERVER_TIMER", match.phase=="RESULTS")
now+=1
tickRoundFlow(now)
now+=30
tickRoundFlow(now)
report("NO_AUTORESTART_AFTER_LOBBY_RETURN", match.phase=="LOBBY" and not roundReady[blue]
    and match.serial==8 and blue.loaded==0 and next(modeVotes)==nil and hordeStarts==0 and botStarts==0)
applyReady(blue,{action="READY",ready=true,seq=42})
tickRoundFlow(now)
report("FRESH_READY_REQUIRED_AND_ACCEPTED", match.phase=="COUNTDOWN" and roundReady[blue]==true
    and lastSeq[blue]==42 and match.serial==8)
now=match.phaseUntil
tickRoundFlow(now)
report("FRESH_KICKOFF_IS_CLASSIC", match.phase=="ACTIVE" and match.serial==9
    and not EXPERIMENTAL_FIVE_EGG_MODE and h2ScoreState==nil and hordeStarts==1
    and blue.loaded==1 and studioSoloRoundStarted and progressMode=="CLASSIC" and botStarts==1)

reset({blue,observer},true,true)
remove(red)
report("H2_TWO_TO_ONE_AFTER_ROSTER_DROP", draw() and settled==1)

reset({blue,observer},true,true)
remove(observer)
report("NEUTRAL_SPECTATOR_IGNORED", match.phase=="ACTIVE" and settled==0 and objective)

reset({blue,taggedObserver},true,true)
remove(taggedObserver)
report("TEAM_TAGGED_SPECTATOR_IGNORED", match.phase=="ACTIVE" and settled==0 and objective)

reset({blue,neutral},true,true)
remove(neutral)
report("UNASSIGNED_CONNECTION_IGNORED", match.phase=="ACTIVE" and settled==0 and objective)

reset({red,redTwo,blue,observer},true,true)
remove(red)
report("H2_THREE_TO_TWO_BOTH_TEAMS_CONTINUE", match.phase=="ACTIVE" and settled==0 and objective)

reset({red,redTwo,blue,observer},true,true)
remove(blue)
report("H2_THREE_TO_TWO_EXISTING_EMPTY_TEAM_RESULT", match.phase=="RESULTS"
    and match.reason=="OPPONENT_LEFT" and match.winner=="RED" and settled==1)

reset({red,observer},true,true)
remove(red)
report("H2_NO_SURVIVOR_KEEPS_EXISTING_RESULT", match.phase=="RESULTS"
    and match.reason=="OPPONENT_LEFT" and match.winner=="BLUE" and settled==1)

reset({red,blue},true,true,"RESULTS")
match.winner,match.reason="RED","FIVE_EGG_SCORE_240S"
remove(red)
report("FINISHED_H2_RESULT_CANNOT_BE_OVERRIDDEN", match.winner=="RED"
    and match.reason=="FIVE_EGG_SCORE_240S" and settled==0)

reset({red,blue},true,true,"COUNTDOWN")
remove(red)
report("COUNTDOWN_HAS_NO_H2_DEPARTURE_RESULT", match.phase=="COUNTDOWN" and settled==0)

reset({red,blue},true,false)
remove(red)
report("CLASSIC_FORFEIT_UNCHANGED", match.phase=="RESULTS" and match.winner=="BLUE"
    and match.reason=="OPPONENT_LEFT" and settled==1)

reset({red,blue},false,true)
remove(red)
report("NONSTUDIO_H2_GUARD", match.phase=="RESULTS" and match.winner=="BLUE"
    and match.reason=="OPPONENT_LEFT" and settled==1)
'''


def fixture(dist):
    source=(dist/'src'/GAME).read_text('utf8')
    modules=dist/'src/server'
    names={'ModeVoteRules':'ModeVote','S1Rules':'Rules','StudioSoloPreviewRules':'StudioSolo',
           'H2FiveEggRules':'H2Score'}
    bodies=[]
    for path,name in names.items():
        bodies.extend((f'local {name}=(function()', (modules/f'{path}.luau').read_text('utf8'), 'end)()'))
    bodies.extend((SETUP, f'local {",".join(TABLES)} = {",".join("{}" for _ in TABLES)}'))
    for header in ('local function getTeamName(player: Player): string',
                   'local function teamCount(name: string): number',
                   'local function eligibleSoloPlayers(): {Player}',
                   'local function everybodyReady(): boolean',
                   'local function scoreModeAllowed(roster: {Player}): boolean',
                   'local function modeVoteSnapshot()', 'local function stopRound(winner: string, reason: string)',
                   'local function resetRound()', 'local function applyReady(player: Player, data)'):
        bodies.append(extract(source,header))
    _,callback,_=split_callback(source)
    bodies.append(CALLBACK+callback+'\nend)')
    tick=extract(source,'local function tickRound()')
    before='    local count = #eligibleSoloPlayers()'
    after='    -- Recovery uses the existing server-only authoritative tick.'
    assert tick.count(before)==tick.count(after)==1
    bodies.extend(('local function tickRoundFlow(now)',before+tick.split(before,1)[1].split(after,1)[0],
                   'end',CHECKS.replace('REASON',REASON)))
    return '\n'.join(bodies)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.write_bytes(fixture(args.dist).encode("utf-8"))
