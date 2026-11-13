#!/usr/bin/env python3
"""Execute the actual source-pinned H1 server mode vote Lua policy with the Luau interpreter.
Only this generated /tmp test fixture is synthetic. No Roblox engine is run here.
"""
from pathlib import Path
import argparse,hashlib
ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"inputs/ModeVoteRules.luau"
EXPECTED="f929a7cd4c211f29d02bd8a129d38109dc492d6e"
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
p=argparse.ArgumentParser();p.add_argument("--write",type=Path,required=True)
a=p.parse_args()
raw=INPUT.read_bytes()
assert blob(raw)==EXPECTED,("FROZEN_VOTE_RULE_TAMPERED",blob(raw))
source=raw.decode()
test=r'''
local Vote=(function()
'''+source+r'''
end)()
local tests=0
local function check(got,expected,tag)
 tests+=1
 assert(got==expected,tag.." wanted="..tostring(expected).." got="..tostring(got))
end
check(Vote.validMode("CLASSIC"),true,"classic")
check(Vote.validMode("SCORE_5"),true,"five")
for _,wrong in ipairs({"five","SCORE5","","ALL","ROBLOX","SCORE_5\n","CLASSIC "}) do
 check(Vote.validMode(wrong),false,"invalid")
end
check(Vote.validMode(nil),false,"nil")
check(Vote.validMode({}),false,"table")
check(Vote.canVote("LOBBY","CLASSIC",true,1,-math.huge),true,"lobby")
check(Vote.canVote("COUNTDOWN","SCORE_5",true,10,-math.huge),true,"countdown")
check(Vote.canVote("LOBBY","SCORE_5",false,10,-math.huge),false,"live_score_gate")
check(Vote.canVote("LOBBY","CLASSIC",false,10,-math.huge),true,"live_only_classic")
check(Vote.canVote("LOBBY","SCORE_5","true",10,-math.huge),false,"spoof_studio")
for _,phase in ipairs({"ACTIVE","RESULTS","PLAYING","", "LOBBY ", "COUNT DOWN"}) do
 check(Vote.canVote(phase,"SCORE_5",true,10,-math.huge),false,"phase_reject")
end
check(Vote.canVote(nil,"CLASSIC",true,10,-math.huge),false,"nilphase")
check(Vote.canVote("LOBBY","CLASSIC",true,10,9.8),false,"spam")
check(Vote.canVote("LOBBY","CLASSIC",true,10,9.6),true,"rate_limit_boundary")
check(Vote.canVote("LOBBY","CLASSIC",true,-2,-math.huge),false,"negative_now")
check(Vote.canVote("LOBBY","CLASSIC",true,math.huge,-math.huge),false,"infinite_now")
check(Vote.canVote("LOBBY","CLASSIC",true,0/0,-math.huge),false,"nan_now")
check(Vote.canVote("LOBBY","CLASSIC",true,"10",-math.huge),false,"string_now")
check(Vote.canVote("LOBBY","CLASSIC",true,10,0/0),false,"nan_previous")
local playerA,playerB,playerC,playerD="A","B","C","D"
local votes={}
local roster={playerA,playerB}
local chosen,c,f=Vote.tally(votes,roster)
check(chosen,"CLASSIC","no_votes_default")
check(c,0,"zero_classic")
check(f,0,"zero_five")
votes[playerA]="SCORE_5"
chosen,c,f=Vote.tally(votes,roster)
check(chosen,"SCORE_5","majority_one_five")
check(c,0,"no_classic")
check(f,1,"one_five")
votes[playerB]="CLASSIC"
chosen,c,f=Vote.tally(votes,roster)
check(chosen,"CLASSIC","one_one_tie_familiar")
check(c,1,"tied_classic")
check(f,1,"tied_score")
votes[playerB]="SCORE_5"
chosen,c,f=Vote.tally(votes,roster)
check(chosen,"SCORE_5","both_choose_score")
check(c,0,"two_score_no_classic")
check(f,2,"two_score")
votes[playerC]="CLASSIC"
chosen,c,f=Vote.tally(votes,roster)
check(chosen,"SCORE_5","leaver_not_in_roster_ignored")
check(c,0,"ghost_not_counted")
votes[playerB]="CLASSIC"
chosen,c,f=Vote.tally(votes,{playerA,playerA,playerB})
check(chosen,"CLASSIC","duplicate_roster_cannot_farm")
check(c,1,"duplicate_count_classic")
check(f,1,"duplicate_count_five")
votes[playerA]="SCORE_5"
votes[playerB]="SCORE_5"
votes[playerC]="CLASSIC"
chosen,c,f=Vote.tally(votes,{playerA,playerB,playerC})
check(chosen,"SCORE_5","two_vs_one_score")
votes[playerB]="CLASSIC"
chosen,c,f=Vote.tally(votes,{playerA,playerB,playerC})
check(chosen,"CLASSIC","two_vs_one_classic")
votes[playerD]="SCORE_5"
chosen,c,f=Vote.tally(votes,{playerA,playerB,playerC,playerD})
check(chosen,"CLASSIC","two_vs_two_tie")
check(c,2,"tie_classic")
check(f,2,"tie_five")
chosen,c,f=Vote.tally({},nil)
check(chosen,"CLASSIC","missing_roster_fails_closed")
check(c,0,"missing_roster_no_count")
chosen,c,f=Vote.tally(nil,roster)
check(chosen,"CLASSIC","missing_votes_fails_closed")
check(f,0,"missing_votes_count")
votes[playerA]="SCORE_5"
votes[playerB]="SCORE_5"
for i=1,75 do
 chosen,c,f=Vote.tally(votes,{playerA,playerB})
 check(chosen,"SCORE_5","deterministic_selection"..i)
 check(f,2,"count_has_no_randomness"..i)
end
print("EGG_RUMBLE_ACTUAL_LUAU_LOBBY_MODE_VOTE_PASS_"..tostring(tests))
'''
a.write.parent.mkdir(parents=True,exist_ok=True)
a.write.write_text(test,encoding="utf-8")
print("EGG_RUMBLE_ORIGINAL_VOTE_RULE_SOURCE_INLINED_NATIVE_HARNESS",len(source))
