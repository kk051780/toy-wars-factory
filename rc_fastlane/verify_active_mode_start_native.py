"""Verify current rich51 kickoff and HUD with the #395/#397 reuse fixtures."""
import argparse
from pathlib import Path

from test_p0_ready_composed_native import unique_function as function

GAME = "src/server/Game.server.luau"
HUD = "src/client/HUD.client.luau"


def region(source, start, end):
    assert source.count(start)==1, start
    tail=source.split(start,1)[1]
    assert end in tail, end
    return start+tail.split(end,1)[0]


SERVER_SETUP = r'''
local studio,now,online=true,100,{}
local RunService,Players={},{}
function RunService:IsStudio() return studio end
function Players:GetPlayers() return online end
local function player(name,side,spectator)
    local p={Name=name,Team=if side then {Name=side} else nil,loaded=0}
    function p:GetAttribute(key) return key=="P0D_LateJoinSpectator" and spectator end
    function p:LoadCharacter() self.loaded+=1 end
    return p
end
local red=player("Solo","RED",false)
local blue=player("Away","BLUE",false)
local observer=player("Observer",nil,true)
local attributedObserver=player("AssignedObserver","BLUE",true)
local neutral=player("Neutral",nil,false)
local Config={MatchSeconds=900,CastleMaxHp=300}
local function serverNow() return now end
local function getTeamName(p) return if p.Team then p.Team.Name else "NONE" end
local function teamCount(side)
    local n=0
    for _,p in ipairs(online) do if getTeamName(p)==side then n+=1 end end
    return n
end
local match,h2ScoreState,hordeStarts,objectiveEnabled,canonicalStarted,progressMode
local modeVotes,lastSeq,lastModeVote={},{},{}
local EXPERIMENTAL_FIVE_EGG_MODE=false
local studioSoloRoundStarted=false
local relayVersions,relayLastAt,relayAcceptedSeq={},{},{}
local earnedPower,lastAttack,lastTrap,lastWind,lastNet,netImmuneUntil={},{},{},{},{},{}
local mobCombo,mobComboUntil,mobLastHits,mobLastKOs,guideProgress={},{},{},{},{}
local delayedRestore,h2Ids,roundEligible,rewardState={},{},{},{}
local h2Eggs={
    {id="R1",part={},prompt={}},{id="R2",part={},prompt={}},
    {id="B1",part={},prompt={}},{id="B2",part={},prompt={}},{id="N1",part={},prompt={}},
}
local function nop() end
local stopCanonical,clearTraps,restoreSavedProfile,cleanupScout=nop,nop,nop,nop
local stopWind,clearEarnedPowerVisual,resetEgg=nop,nop,nop
local oldModeAtDrop={}
local function dropEgg(p) oldModeAtDrop[p]=EXPERIMENTAL_FIVE_EGG_MODE end
local First90Guide={newRound=function(serial) return serial end}
local Power={endRound=nop}
local RewardRules={startRound=function() return true end}
local CFrame={new=nop}
local horde={reset=function() hordeStarts+=1 end}
local function startCanonical() canonicalStarted=true end
local function setObjectiveEnabled(enabled) objectiveEnabled=enabled end
local function beginProgressRounds(mode) progressMode=mode end
local broadcasts=0
local function broadcast() broadcasts+=1 end
'''


SERVER_CHECKS = r'''
local function resetInput(roster, isStudio, previousScore)
    online,studio=roster,isStudio
    match={phase="COUNTDOWN",serial=30}
    hordeStarts,canonicalStarted,objectiveEnabled,progressMode=0,false,false,nil
    EXPERIMENTAL_FIVE_EGG_MODE,h2ScoreState=previousScore,nil
    red.loaded,blue.loaded,observer.loaded,attributedObserver.loaded=0,0,0,0
    table.clear(modeVotes)
    table.clear(lastSeq)
    table.clear(lastModeVote)
    table.clear(oldModeAtDrop)
    broadcasts=0
end
local function report(name, condition)
    print((if condition then "PASS:" else "FAIL:")..name)
end
local function classic()
    return match.phase=="ACTIVE" and not EXPERIMENTAL_FIVE_EGG_MODE
        and h2ScoreState==nil and match.deadline==now+Config.MatchSeconds
        and h2Eggs[1].part.Transparency==0 and h2Eggs[2].part.Transparency==1
        and h2Eggs[3].part.Transparency==0 and h2Eggs[4].part.Transparency==1
        and h2Eggs[5].part.Transparency==1 and canonicalStarted and objectiveEnabled
end
local function score()
    return match.phase=="ACTIVE" and EXPERIMENTAL_FIVE_EGG_MODE
        and h2ScoreState~=nil and H2Score.assertConserved(h2ScoreState)
        and match.deadline==now+H2Score.LENGTH_SECONDS
        and h2Eggs[5].part.Transparency==0 and canonicalStarted and objectiveEnabled
end
resetInput({red},true,false)
modeVotes[red]=ModeVote.SCORE
report("SOLO_PROJECTED_CLASSIC", modeVoteSnapshot()==ModeVote.CLASSIC)
resetRound()
report("SOLO_SCORE_FALLBACK", classic() and studioSoloRoundStarted and red.loaded==1
    and hordeStarts==1 and progressMode=="CLASSIC")

resetInput({red,observer,attributedObserver,neutral},true,false)
modeVotes[red],modeVotes[observer],modeVotes[attributedObserver]=ModeVote.SCORE,ModeVote.SCORE,ModeVote.SCORE
resetRound()
report("SPECTATORS_CANNOT_ENABLE_SCORE", classic() and red.loaded==1 and observer.loaded==0
    and attributedObserver.loaded==0 and hordeStarts==1)

resetInput({red,blue},true,false)
modeVotes[red],modeVotes[blue]=ModeVote.SCORE,ModeVote.SCORE
table.remove(online,2)
resetRound()
report("DEPARTED_SECOND_VOTER_FALLBACK", classic() and progressMode=="CLASSIC")

resetInput({red,observer},true,false)
local before=broadcasts
applyModeVote(red,{action="MODE_VOTE",mode="SCORE_5",seq=1})
report("SERVER_REJECTS_SOLO_SCORE_VOTE", modeVotes[red]==nil and lastModeVote[red]==nil
    and broadcasts==before and lastSeq[red]==1)
now+=1
applyModeVote(red,{action="MODE_VOTE",mode="CLASSIC",seq=2})
report("SERVER_ACCEPTS_SOLO_CLASSIC_VOTE",modeVotes[red]==ModeVote.CLASSIC and lastSeq[red]==2)

resetInput({red,blue,observer},true,false)
applyModeVote(red,{action="MODE_VOTE",mode="SCORE_5",seq=1})
applyModeVote(blue,{action="MODE_VOTE",mode="SCORE_5",seq=1})
report("TWO_HUMANS_PROJECT_SCORE", modeVoteSnapshot()==ModeVote.SCORE)
resetRound()
report("TWO_HUMANS_SCORE_KICKOFF", score() and red.loaded==1 and blue.loaded==1
    and observer.loaded==0 and not studioSoloRoundStarted and hordeStarts==1 and progressMode=="SCORE")

resetInput({red,blue},true,true)
modeVotes[red],modeVotes[blue]=ModeVote.CLASSIC,ModeVote.SCORE
resetRound()
report("TIE_FALLBACK_AND_OLD_MODE_CLEANUP", classic() and oldModeAtDrop[red] and oldModeAtDrop[blue])

resetInput({red,blue},false,false)
modeVotes[red],modeVotes[blue]=ModeVote.SCORE,ModeVote.SCORE
resetRound()
report("NONSTUDIO_STAYS_CLASSIC", classic() and hordeStarts==0 and progressMode==nil)
'''


HUD_TESTS = r'''
local function update(s)
    local canChoose=(s.phase=="LOBBY" or s.phase=="COUNTDOWN") and s.modeScoreAvailable==true
    HUD_UPDATE
end
update({phase="LOBBY",modeScoreAvailable=true,soloFiveEggUnavailable=true,myModeVote="SCORE_5"})
click()
assert(actions==0 and not scoreMode.Active and string.find(scoreMode.Text,"2人から",1,true),"HUD_SOLO_SCORE")
update({phase="LOBBY",modeScoreAvailable=true,soloFiveEggUnavailable=false,myModeVote="SCORE_5"})
click()
assert(actions==1 and scoreMode.Active and string.find(scoreMode.Text,"✓",1,true),"HUD_TWO_HUMAN_SCORE")
update({phase="ACTIVE",modeScoreAvailable=true,soloFiveEggUnavailable=false})
click()
assert(actions==1 and not scoreMode.Active,"HUD_ACTIVE_SCORE")
print("PASS:HUD_SOLO_TWO_CLIENT_ACTIVE")
'''


def server_harness(dist):
    source=(dist/GAME).read_text('utf8')
    parts=[]
    for module in ('ModeVoteRules','S1Rules','StudioSoloPreviewRules','H2FiveEggRules'):
        name={'ModeVoteRules':'ModeVote','S1Rules':'Rules','StudioSoloPreviewRules':'StudioSolo',
              'H2FiveEggRules':'H2Score'}[module]
        parts.extend((f'local {name}=(function()',
                      (dist/'src/server'/f'{module}.luau').read_text('utf8'),'end)()'))
    parts.extend((SERVER_SETUP,function(source,'local function eligibleSoloPlayers(): {Player}')))
    if 'local function scoreModeAllowed(' in source:
        parts.append(function(source,'local function scoreModeAllowed(roster: {Player}): boolean'))
    parts.extend(function(source,header) for header in ('local function modeVoteSnapshot()',
        'local function applyModeVote(player: Player,data)','local function resetRound()'))
    return '\n'.join(parts+[SERVER_CHECKS])


def hud_harness(dist):
    source=(dist/HUD).read_text('utf8')
    click=region(source,'local scoreModeSelectable=false','scoutButton.MouseButton1Click:Connect')
    update=region(source,'    scoreModeSelectable=canChoose','    local hatchAvailable=')
    return '''local scoreMode={MouseButton1Click={}}
local click,actions=nil,0
function scoreMode.MouseButton1Click:Connect(callback) click=callback end
local function action(kind,mode)
    assert(kind=="MODE_VOTE" and mode=="SCORE_5","HUD_ACTION_DRIFT")
    actions+=1
end
'''+click+HUD_TESTS.replace('    HUD_UPDATE',update)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--hud", type=Path, required=True)
    args = parser.parse_args()
    args.server.write_bytes(server_harness(args.dist).encode())
    args.hud.write_bytes(hud_harness(args.dist).encode())
