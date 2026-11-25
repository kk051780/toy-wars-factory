#!/usr/bin/env python3
"""Independent QA-only execution of the ALREADY OFFICIAL #663 ResultService.

Reads the actual source selected in the current canonical31 project, uses the
actual resultText function, and builds two disposable native Luau harnesses.
This does NOT patch, author or reselect any gameplay script.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

MAPPED="rc_fastlane/quality_draw_result_label_rc31/select_draw_label.py"
STATUS='local status=if session.rules.winner=="DRAW" then "引き分け"'
MUTATION= 'local status=if won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"'
CHECKS=r'''
local tests=0
local function eq(actual,expected)
 tests+=1
 if actual~=expected then error("TEST_"..tostring(tests)..": got "..tostring(actual).." expected "..tostring(expected)) end
end
local function session(winner,alive,team)
 return {
   rules={winner=winner,castles={["101"]={
     team=team or "RED",alive=alive,depositedEggs=2
   }},events={{type="TIME_LIMIT_DRAW",matchId="m"}}
   },
   swarm={kills={["101"]=7}}
 }
end
local p={UserId=101}
local ranking={rows={{id="101",score=680,stolen=3,securedSteals=2,
 teamCastleSupport=1,specialty="戦士"}}}
local a,b=resultText(session("DRAW",true,"RED"),p,"TEAM",ranking)
eq(a,"引き分け・戦士")
eq(b,"1位 680点｜KO7 奪3(帰2) 納2 城0 団1")
a,b=resultText(session("DRAW",true),p,"BATTLE_ROYALE",ranking)
eq(a,"引き分け・戦士")
eq(b,"1位 680点｜KO7 奪3(帰2) 納2 城0")
a,b=resultText(session("RED",true),p,"TEAM",ranking)
eq(a,"勝利！・戦士")
a,b=resultText(session("RED",false),p,"TEAM",ranking)
eq(a,"チーム勝利！・戦士")
a,b=resultText(session("BLUE",true),p,"TEAM",ranking)
eq(a,"試合終了・戦士")
a,b=resultText(session("101",true),p,"BATTLE_ROYALE",ranking)
eq(a,"勝利！・戦士")
a,b=resultText(session("202",true),p,"BATTLE_ROYALE",ranking)
eq(a,"試合終了・戦士")
a,b=resultText(session("DRAW",false),p,"TEAM",ranking)
eq(a,"引き分け・戦士")
local unknown=resultText({rules={winner="DRAW",castles={}}},p,"TEAM",ranking)
eq(unknown,"試合終了")
print("GQ_DRAW_ORIGINAL_RESULTTEXT_NATIVE_PASS "..tostring(tests))
'''

def read_result(project:Path)->tuple[str,str]:
    spec=importlib.util.spec_from_file_location("official_draw_selector",MAPPED)
    if spec is None or spec.loader is None:raise ValueError("RED_OFFICIAL_DRAW_SELECTOR_MISSING")
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    _,actual,key=mod.mapped(project.resolve(strict=True))
    if len(actual)!=31 or key[-1]!="EGGRUMBLE_MatchResultService":
        raise ValueError("RED_NOT_LATEST_SELECTED_31_RESULT")
    source=actual[key].read_text(encoding="utf8")
    if source.count(STATUS)!=1 or source.count("function ResultRetry.deliver(")!=1 or source.count("ScoreBalance.build(")!=1:
        raise ValueError("RED_DRAW_OR_OLDER_RESULT_SCORE_RETRY_MISSING")
    if source.count('session.resultsDelivered=true')!=1 or 'GQ_DRAW_LABEL_RESULT' not in source:
        raise ValueError("RED_OFFICIAL_RESULT_ALREADY_DRIFTED")
    return source,hashlib.sha256(actual[key].read_bytes()).hexdigest()

def compile_harness(source:str,mutant:bool)->str:
    original='local function castleEliminations('
    next_func='\nlocal function makeResultGui('
    start=source.find(original)
    stop=source.find(next_func,start)
    if source.count(original)!=1 or source.count(next_func)!=1 or start<0 or stop<=start:
        raise ValueError("RED_NOT_ACTUAL_RESULTTEXT_FUNCTION")
    body=source[start:stop]
    if mutant:
        # Mutate only a temporary QA snippet; the current official Result stays untouched.
        old=' local status=if session.rules.winner=="DRAW" then "引き分け"\n  elseif won then (if castle.alive then "勝利！" else "チーム勝利！")\n  else "試合終了"'
        if body.count(old)!=1:raise ValueError("RED_NOT_EXACT_OFFICIAL_DRAW_LABEL")
        body=body.replace(old," "+MUTATION,1)
    return "--!strict\n"+body+"\n"+CHECKS

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--mutant",action="store_true")
    ap.add_argument("--receipt",type=Path)
    a=ap.parse_args()
    source,source_sha=read_result(a.project)
    a.out.write_text(compile_harness(source,a.mutant),encoding="utf8")
    if a.receipt:
        data={"source_only":True,"existing_runtime_script_count":31,
              "real_source":"EGGRUMBLE_MatchResultService",
              "selected_existing_result_sha256":source_sha,
              "native_real_outcome_cases":11,"mutant":a.mutant,
              "studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
              "owner_fun":"NO_GO"}
        a.receipt.write_text(json.dumps(data,indent=2,ensure_ascii=False,sort_keys=True)+"\n")
    print("GQ_DRAW_INDEPENDENT_ACTUAL_RESULT_NATIVE_HARNESS_PREPARED",a.out)

if __name__=="__main__":main()
