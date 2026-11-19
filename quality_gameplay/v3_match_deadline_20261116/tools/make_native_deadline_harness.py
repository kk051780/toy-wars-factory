#!/usr/bin/env python3
"""Run the original pure Luau policy, not a Python behavioral emulation."""
from pathlib import Path
import argparse

SOURCE = Path(__file__).resolve().parents[1] / "EGGRUMBLE_DeadlinePolicy.luau"
TESTS = r'''
local P=Deadline
local n=0
local function eq(a,b)
 n+=1
 assert(a==b, "check "..n..": got "..tostring(a).." expected "..tostring(b))
end
local function state(mode)
 return {mode=mode,phase="ACTIVE",winner=nil,events={},
  castles={A={alive=true,team="RED"},B={alive=true,team="BLUE"}}}
end
local s=state("TEAM")
local l=P.new(100,"match-1")
eq(P.DEFAULT_SECONDS,900)
eq(l.seconds,900)
local ok,reason=P.check(s,l,999,"match-1")
eq(ok,false);eq(reason,"BEFORE_DEADLINE")
ok,reason=P.check(s,l,1000,"another")
eq(ok,false);eq(reason,"STALE_MATCH")
ok,reason=P.check(s,l,99,"match-1")
eq(ok,false);eq(reason,"INVALID_CLOCK")
ok,reason=P.expire(s,l,1000,"match-1")
eq(ok,true);eq(reason,"TIME_LIMIT_DRAW")
eq(s.phase,"FINISHED");eq(s.winner,"DRAW")
eq(#s.events,1);eq(s.events[1].type,"TIME_LIMIT_DRAW")
eq(s.events[1].elapsed,900)
ok,reason=P.expire(s,l,1001,"match-1")
eq(ok,false);eq(reason,"ALREADY_APPLIED");eq(#s.events,1)
local completed=state("TEAM")
completed.winner="RED";completed.phase="FINISHED"
ok,reason=P.expire(completed,P.new(0,"m2"),1000,"m2")
eq(ok,false);eq(reason,"ALREADY_FINISHED");eq(completed.winner,"RED")
local noContest=state("TEAM")
noContest.castles.B.alive=false
ok,reason=P.expire(noContest,P.new(0,"m3"),900,"m3")
eq(ok,false);eq(reason,"NO_CONTEST")
local royale=state("BATTLE_ROYALE")
ok,reason=P.expire(royale,P.new(5,"m4"),905,"m4")
eq(ok,true);eq(royale.winner,"DRAW")
local former=state("TEAM")
ok,reason=P.expire(former,P.new(0,"m5"),math.huge,"m5")
eq(ok,false);eq(reason,"INVALID_CLOCK")
local zero=state("TEAM")
ok,reason=P.expire(zero,P.new(0,"m6"),900,"old-session")
eq(ok,false);eq(reason,"STALE_MATCH")
eq(zero.phase,"ACTIVE");eq(zero.winner,nil)
local early=state("TEAM")
ok,reason=P.expire(early,P.new(0,"m7",1200),901,"m7")
eq(ok,false);eq(reason,"BEFORE_DEADLINE")
local invalid=pcall(function() P.new(0,"",900) end)
eq(invalid,false)
invalid=pcall(function() P.new(0,"x",0) end)
eq(invalid,false)
print("EGGRUMBLE_V3_DEADLINE_NATIVE_ASSERTIONS_PASS="..n)
'''

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    source = SOURCE.read_text(encoding="utf-8").rstrip()
    assert source.endswith("return Deadline"), "source export changed"
    combined = source[: -len("return Deadline")] + TESTS
    dest = Path(args.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(combined, encoding="utf-8")

if __name__ == "__main__":
    main()
