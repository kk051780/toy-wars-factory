#!/usr/bin/env python3
"""GQ-DRAW: localized source-true result label in original RC31 ResultService.

One existing result source changes; 30 others byte-identical. True Rojo Source
and Class are checked, and the real original resultText is executed in native
Luau for TEAM/BR DRAW, normal wins/losses and unchanged ranked statistics.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

RESULT=("ServerScriptService","EGGRUMBLE_MatchResultService")
TOTAL=31
FEATURE="RESULT_DRAW_LABEL_20261117"
OLD='local status=if won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"'
NEW='local status=if session.rules.winner=="DRAW" then "引き分け" elseif won then (if castle.alive then "勝利！" else "チーム勝利！") else "試合終了"'
FILE="GQ_DRAW_MATCH_RESULT.luau"
RECEIPT="GQ_DRAW_RC31_RECEIPT.json"

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def scan(project:Path):
    project=project.resolve(strict=True)
    content=json.loads(project.read_text(encoding="utf8"))
    found={}
    def walk(tree,route=()):
        for name,item in tree.items():
            if name.startswith("$"):continue
            if not isinstance(item,dict):raise ValueError("RED_NON_SCRIPT_NODE")
            path=route+(name,)
            if "$path" in item:
                if set(item)!={"$path"} or path in found:
                    raise ValueError("RED_DUPLICATE_SCRIPT_AUTHORITY")
                found[path]=(project.parent/item["$path"]).resolve(strict=True)
            else:walk(item,path)
    walk(content["tree"])
    if len(found)!=TOTAL or len({p[-1] for p in found})!=TOTAL or RESULT not in found:
        raise ValueError("RED_EXPECT_CANONICAL_31_WITH_RESULT")
    return content,found

def patch(raw:bytes)->bytes:
    source=raw.decode("utf8")
    if source.count(OLD)!=1 or source.count(NEW)!=0:
        raise ValueError("RED_RESULT_AUTHOR_ORIGINAL_STATUS_CHANGED")
    for anchor in ('function ResultRetry.deliver(', 'ScoreBalance.build(', 'session.resultsDelivered=true',
                   'local function resultText(', 'local function makeResultGui('):
        if anchor not in source:
            raise ValueError("RED_RESULT_ORIGINAL_RETRY_OR_SCORE_DRIFT_"+anchor)
    result=source.replace(OLD,NEW,1)
    if result.replace(NEW,OLD,1)!=source:
        raise ValueError("RED_RESULT_NOT_ONE_HUNK_REVERSIBLE")
    return result.encode("utf8")

def prepare(base:Path,out:Path):
    if out.exists() or out.parent.resolve()!=base.parent.resolve():
        raise ValueError("RED_OUTPUT_EXISTS_OR_NOT_SIBLING")
    project,scripts=scan(base)
    original=scripts[RESULT].read_bytes()
    selected=patch(original)
    dest=out.parent/FILE
    if dest.exists():raise ValueError("RED_SELECTED_ALREADY_EXISTS")
    dest.write_bytes(selected)
    modified=copy.deepcopy(project)
    modified["tree"][RESULT[0]][RESULT[1]]["$path"]=FILE
    out.write_text(json.dumps(modified,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,next_map=scan(out)
    if set(scripts)!=set(next_map) or [p for p in scripts if scripts[p].read_bytes()!=next_map[p].read_bytes()]!=[RESULT]:
        raise ValueError("RED_OTHER_30_SOURCES_CHANGED")
    receipt={
      "feature_id":FEATURE,"source_count":TOTAL,
      "changed_existing_authority":"/".join(RESULT),
      "original_result_sha256":sha(original),
      "selected_result_sha256":sha(selected),
      "other30_bytes_exact":True,"off_inverse_result_exact":True,
      "real_rojo_exact":"NOT_RUN","native_actual_result_cases":"NOT_RUN",
      "formal_rc_adopted":False,"studio_2client":"NOT_TESTED","android_15min":"NOT_TESTED",
      "owner_fun":"NO_GO"
    }
    (out.parent/RECEIPT).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("GQ_DRAW_ONE_EXISTING_RESULT_OTHER30_BYTES_EXACT_OFF_PASS")

def verify(base:Path,out:Path,place:Path):
    _,before=scan(base);_,after=scan(out)
    expected=patch(before[RESULT].read_bytes())
    if after[RESULT].read_bytes()!=expected:
        raise ValueError("RED_RESULT_NOT_ORIGINAL_ONE_HUNK")
    if set(before)!=set(after) or [p for p in before if before[p].read_bytes()!=after[p].read_bytes()]!=[RESULT]:
        raise ValueError("RED_CHANGED_OTHER_THAN_ORIGINAL_RESULT")
    embedded={}
    for item in ET.parse(place).getroot().iter("Item"):
        kind=item.attrib.get("class")
        if kind not in ("Script","ModuleScript","LocalScript"):continue
        prop=item.find("Properties")
        if prop is None:raise ValueError("RED_PLACE_SCRIPT_PROPERTIES")
        name=prop.findtext("string[@name='Name']")
        src=prop.findtext("ProtectedString[@name='Source']")
        if src is None:src=prop.findtext("string[@name='Source']")
        if not name or src is None or name in embedded:raise ValueError("RED_PLACE_SOURCE_MISSING_OR_DUP")
        embedded[name]=(kind,src.replace("\r\n","\n"))
    if len(embedded)!=TOTAL or set(embedded)!={r[-1] for r in after}:
        raise ValueError("RED_PLACE_NOT_EXACT31")
    for route,path in after.items():
        cls="Script" if path.name.endswith(".server.luau") else (
            "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
        if embedded[route[-1]]!=(cls,path.read_text(encoding="utf8").replace("\r\n","\n")):
            raise ValueError("RED_PLACE_SOURCE_CLASS_"+route[-1])
    rfile=out.parent/RECEIPT
    r=json.loads(rfile.read_text(encoding="utf8"))
    if r["selected_result_sha256"]!=sha(expected) or r["original_result_sha256"]!=sha(before[RESULT].read_bytes()):
        raise ValueError("RED_RECEIPT_DRIFT")
    r.update(real_rojo_exact="31/31",place_bytes=place.stat().st_size,place_sha256=sha(place.read_bytes()))
    rfile.write_text(json.dumps(r,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf8")
    print("GQ_DRAW_REAL_ROJO31_SOURCE_CLASS_OFF_EXACT_PASS",r["place_bytes"])

TESTS=r'''
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

def native(out:Path,selected:Path,mutant:bool):
    s=selected.read_text(encoding="utf8")
    prefix="local function castleEliminations("
    suffix="\nlocal function makeResultGui("
    i=s.find(prefix);j=s.find(suffix,i)
    if i<0 or j<=i or s.count(prefix)!=1 or s.count(suffix)!=1:
        raise ValueError("RED_RESULTTEXT_NATIVE_HARNESS_NOT_SOURCE_DERIVED")
    body=s[i:j]
    if mutant:
        if body.count(NEW)!=1:raise ValueError("RED_MUTANT_NOT_ONE_ANCHOR")
        body=body.replace(NEW,OLD,1)
    out.write_text("--!strict\n"+body+"\n"+TESTS,encoding="utf8")
    print("GQ_DRAW_ACTUAL_SOURCE_LUAU_HARNESS_READY",out)

def main():
    a=argparse.ArgumentParser()
    a.add_argument("action",choices=("prepare","verify","native"))
    a.add_argument("--base",type=Path)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--place",type=Path)
    a.add_argument("--selected",type=Path)
    a.add_argument("--mutant",action="store_true")
    opts=a.parse_args()
    if opts.action=="native":
        if not opts.selected:a.error("--selected required")
        native(opts.out,opts.selected,opts.mutant)
    elif opts.action=="prepare":
        if not opts.base:a.error("--base required")
        prepare(opts.base,opts.out)
    else:
        if not opts.base or not opts.place:a.error("--base and --place required")
        verify(opts.base,opts.out,opts.place)
if __name__=="__main__":main()
