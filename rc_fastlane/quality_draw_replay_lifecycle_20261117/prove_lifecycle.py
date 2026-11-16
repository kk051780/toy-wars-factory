#!/usr/bin/env python3
"""QA-only: attests real selected 31-script DRAW -> result -> replay -> lobby path.

This is source-contract and negative-mutation testing, NOT Roblox Studio runtime QA.
No new Lua, Game, Remote, Store, result implementation, or feature flag.
"""
import argparse
import json
from pathlib import Path

HOST="EGGRUMBLE_LobbyCastleModesPreview"
REPLAY="EGGRUMBLE_RoundReplay"
RESULT="EGGRUMBLE_MatchResultService"
CHECKED=(HOST,REPLAY,RESULT)

def flatten(project:Path):
    data=json.loads(project.read_text(encoding="utf8"))
    found={}
    def visit(node):
        for name,value in node.items():
            if not isinstance(value,dict):
                continue
            if "$path" in value:
                if set(value)!={"$path"} or name in found:
                    raise ValueError("RED_DUPLICATE_OR_NONEXACT_RUNTIME_SOURCE")
                found[name]=(project.parent/value["$path"]).resolve(strict=True)
            else:
                visit(value)
    visit(data["tree"])
    if len(found)!=31 or not all(n in found for n in CHECKED):
        raise ValueError("RED_SELECTED31_MISSING_REAL_LIFECYCLE_SCRIPTS")
    return {n:found[n].read_text(encoding="utf8") for n in CHECKED}

def require(source,anchor,label):
    if source.count(anchor)!=1:
        raise ValueError("RED_"+label+"_MISSING_OR_DUPLICATED")

def prove(s):
    host,replay,result=(s[n] for n in CHECKED)
    require(host,"-- MATCH_DEADLINE_DRAW_499 BEGIN ORIGINAL #499 POLICY","PINNED_DEADLINE")
    require(host,'state.winner="DRAW"',"DRAW_WINNER")
    require(host,"local deadlineLease=Deadline.new(os.clock(),deadlineId)","DEADLINE_LEASE")
    require(host,"if expired then\n    session.refresh()","EXPIRED_REFRESH")
    require(host,"ResultService.showIfFinished(session,queue,mode)","REAL_RESULT_DISPATCH")
    require(host,"RoundReplay.schedule(session,session.closeRound)","REAL_REPLAY_SCHEDULER")
    require(host,"if session.rules.winner~=nil then","WINNER_LIFECYCLE_GATE")
    require(host,"RoundReplay.resetHuman(player,root+Vector3.new(0,8,-5)","REAL_LOBBY_RETURN")
    require(host,"sessions[mode]=nil","SESSION_RELEASE")
    require(host,"queues[mode]={}","QUEUE_RELEASE")
    require(host,"queueEpoch[mode]+=1","COUNTDOWN_EPOCH")
    require(replay,"Replay.RESULT_HOLD_SECONDS=10","RESULT_HOLD")
    require(replay,'session.rules.phase~="FINISHED"',"FINISHED_ONLY")
    require(replay,"or session.rules.winner==nil then return false end","NO_FALSE_WIN")
    require(replay,"task.delay(Replay.RESULT_HOLD_SECONDS,function()","DELAYED_CLOSE")
    require(replay,'if session.rules.phase=="FINISHED" then closeRound() end',"LATE_CLOSE_FENCE")
    require(result,'session.rules.winner=="DRAW"',"DRAW_LABEL_SOURCE")
    require(result,"function ResultService.showIfFinished(session:any,queue:{Player},mode:string):boolean","RESULT_SERVICE")
    if not (host.index("ResultService.showIfFinished(session,queue,mode)") <
            host.index("RoundReplay.schedule(session,session.closeRound)")):
        raise ValueError("RED_RESULT_MUST_PRECEDE_REPLAY")
    return True

def mutation_tests(actual):
    mutations=[
        (HOST,'state.winner="DRAW"','state.winner="RED"'),
        (HOST,"if expired then\n    session.refresh()","if expired then\n    warn('skip')"),
        (HOST,"RoundReplay.schedule(session,session.closeRound)","RoundReplay.skip(session,session.closeRound)"),
        (HOST,"ResultService.showIfFinished(session,queue,mode)","ResultService.notShown(session,queue,mode)"),
        (HOST,"RoundReplay.resetHuman(player,root+Vector3.new(0,8,-5)","RoundReplay.noReset(player,root+Vector3.new(0,8,-5)"),
        (HOST,"sessions[mode]=nil","sessions[mode]={}"),
        (HOST,"queues[mode]={}","queues[mode]=nil"),
        (HOST,"queueEpoch[mode]+=1","queueEpoch[mode]+=0"),
        (REPLAY,"Replay.RESULT_HOLD_SECONDS=10","Replay.RESULT_HOLD_SECONDS=0"),
        (REPLAY,'if session.rules.phase=="FINISHED" then closeRound() end','if session.rules.phase=="ACTIVE" then closeRound() end'),
        (RESULT,'session.rules.winner=="DRAW"','session.rules.winner=="LOSS"'),
    ]
    count=0
    for name,old,new in mutations:
        if actual[name].count(old)!=1:
            raise ValueError("RED_MUTANT_ANCHOR_DRIFT_"+name)
        changed=dict(actual)
        changed[name]=actual[name].replace(old,new,1)
        try:
            prove(changed)
        except ValueError:
            count+=1
        else:
            raise ValueError("RED_MUTANT_NOT_DETECTED_"+name)
    if count!=len(mutations):
        raise ValueError("RED_INCOMPLETE_MUTANT_GATES")
    return count

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--project",type=Path,required=True)
    args=parser.parse_args()
    actual=flatten(args.project)
    prove(actual)
    n=mutation_tests(actual)
    print("GQ8_REAL_SELECTED31_DRAW_RESULT_REPLAY_LOBBY_SOURCE_PASS")
    print("GQ8_DRAW_REPLAY_NEGATIVE_MUTANTS_REJECTED",n)
    print("GQ8_NEW_GAMEPLAY_SOURCE=0 NEW_FEATURE_FLAGS=0")
    print("STUDIO_2CLIENT=NOT_TESTED ANDROID=NOT_TESTED OWNER_FUN=NO_GO")

if __name__=="__main__":
    main()
