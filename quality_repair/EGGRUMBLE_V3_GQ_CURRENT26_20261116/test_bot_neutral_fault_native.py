#!/usr/bin/env python3
"""Execute actual BotActors neutral-call safety in native Luau.
Optional neutral runtime failures must not abort the bot's siege/egg loop.
Source-only functional test; Studio/Android performance remains unverified.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess
import tempfile

SOURCE=Path("handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_BotActors.luau")
PREFIX=r"""
local warnings={}
local function warn(message,detail)
 table.insert(warnings,tostring(message).." / "..tostring(detail))
end
"""
SUFFIX=r"""
local cases=0
local botId="AI_BLUE_7"
local where={X=3,Y=1,Z=20}
local s={swarm=nil}
-- An optional missing neutral service must leave all castle/egg AI running.
hitNeutralSafely(s,botId,where)
assert(s.botNeutralFaults==nil and #warnings==0)
cases+=1
local attackCalls=0
s.swarm={damageFromBot=function(id,at)
 attackCalls+=1
 assert(id==botId and at==where)
 return 4
end}
hitNeutralSafely(s,botId,where)
assert(attackCalls==1 and s.botNeutralFaults==nil and #warnings==0)
cases+=1
-- A runtime failure is YELLOW, not a fatal controller exit.
s.swarm={damageFromBot=function() error("destroyed neutral Humanoid") end}
local continueCastleAndEgg=false
hitNeutralSafely(s,botId,where)
continueCastleAndEgg=true
assert(continueCastleAndEgg==true and s.botNeutralFaults==1)
assert(s.botNeutralStatus=="YELLOW_NEUTRAL_HIT" and #warnings==1)
cases+=1
-- Repeated transient failures still account every error without log-spamming.
for _=1,3 do hitNeutralSafely(s,botId,where) end
assert(s.botNeutralFaults==4 and #warnings==3)
cases+=1
-- Malformed optional neutral API is also contained.
s.swarm={}
hitNeutralSafely(s,botId,where)
assert(s.botNeutralFaults==5 and #warnings==3)
cases+=1
-- Recovery permits neutral damage and doesn't corrupt prior error count.
s.swarm={damageFromBot=function(id,at)
 assert(id==botId and at==where)
 return 2
end}
hitNeutralSafely(s,botId,where)
assert(s.botNeutralFaults==5 and s.botNeutralStatus=="YELLOW_NEUTRAL_HIT")
cases+=1
print("GQ_BOT_NEUTRAL_FAULT_NATIVE_PASS cases="..cases)
"""

def extract(content:str)->str:
    a=content.index("local function hitNeutralSafely(")
    b=content.index("-- Actor pathfinding is in the reusable",a)
    section=content[a:b]
    assert "pcall(function()" in section,"neutral guard absent"
    assert 'session.botNeutralStatus="YELLOW_NEUTRAL_HIT"' in section,"fault status absent"
    return section

def run(luau:Path,code:str)->subprocess.CompletedProcess[str]:
    with tempfile.TemporaryDirectory(prefix="gq-neutral-fault-") as td:
        p=Path(td)/"neutral_fault.spec.luau"
        p.write_text(PREFIX+code+SUFFIX,encoding="utf-8")
        return subprocess.run([str(luau),str(p)],capture_output=True,text=True,check=False)

def main()->None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--luau",type=Path,required=True)
    args=parser.parse_args()
    assert args.luau.is_file(),args.luau
    actual=extract(SOURCE.read_text(encoding="utf-8"))
    good=run(args.luau,actual)
    assert good.returncode==0,(good.stdout,good.stderr)
    assert "GQ_BOT_NEUTRAL_FAULT_NATIVE_PASS cases=6" in good.stdout
    # Regressing to an unguarded optional neutral call must fail.
    unguarded=actual.replace("local ok,reason=pcall(function()", "local ok,reason=true,nil\n do")
    unguarded=unguarded.replace("return swarm.damageFromBot(id,at)", "swarm.damageFromBot(id,at)")
    unguarded=unguarded.replace(" end)\n if not ok then", " end\n if not ok then")
    assert unguarded!=actual
    bad=run(args.luau,unguarded)
    assert bad.returncode!=0,(bad.stdout,bad.stderr)
    # Silent error swallowing must also fail: diagnostic evidence required.
    silent=actual.replace("session.botNeutralFaults=faults","-- diagnostics accidentally disabled")
    assert silent!=actual
    bad=run(args.luau,silent)
    assert bad.returncode!=0,(bad.stdout,bad.stderr)
    print(good.stdout.strip())
    print("GQ_BOT_NEUTRAL_FAULT_NEGATIVE_2_OF_2_PASS")

if __name__=="__main__":
    main()
