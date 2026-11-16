#!/usr/bin/env python3
"""Create native Luau VM cases from the ACTUAL generated host callback.

No mock-only rewriting: the callback under test is extracted verbatim from the
pinned, source-selective patched host.
"""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument("--patched-host", type=Path, required=True)
parser.add_argument("--out", type=Path, required=True)
args = parser.parse_args()

host = args.patched_host.read_text(encoding="utf-8")
matches = re.findall(
    r"  session\.isCurrentHuman=function\(player:Player\):boolean\n.*?\n  end",
    host,
    re.DOTALL,
)
if len(matches) != 1:
    raise SystemExit("RED: expected exactly one authentic embedded host membership callback")
callback = matches[0].strip()
cases = r'''
local Players={}
local mode="TEAM"
local session={rules={phase="ACTIVE",castles={["101"]={alive=true}}}}
local sessions={TEAM=session, BATTLE_ROYALE={}}
local joined={[101]="TEAM"}
local player={UserId=101,Parent=Players}
''' + callback + r'''
local checks=0
local function check(label,expected)
 local got=session.isCurrentHuman(player)
 assert(got==expected,label..": wanted "..tostring(expected).." got "..tostring(got))
 checks+=1
end
check("live same-mode human",true)
joined[101]=nil
check("disconnected but castle still alive",false)
joined[101]="BATTLE_ROYALE"
check("rejoined opposite mode while castle still alive",false)
joined[101]="TEAM"
player.Parent=nil
check("detached player object",false)
player.Parent=Players
session.rules.phase="FINISHED"
check("finished round",false)
session.rules.phase="LOBBY"
check("waiting lobby, not active",false)
session.rules.phase="ACTIVE"
sessions.TEAM={}
check("stale session replaced by newer TEAM session",false)
sessions.TEAM=session
session.rules.castles["101"]=nil
check("not rostered in this session",false)
session.rules.castles["101"]={alive=true,isAI=true}
check("AI takeover not a human participant",false)
session.rules.castles["101"].isAI=false
check("returns to valid human only",true)
print("GQ BOT HUMAN MEMBERSHIP real host callback native PASS "..tostring(checks).."/"..tostring(checks))
'''
args.out.write_text(cases, encoding="utf-8")
print("Native test harness generated from exact host function:", args.out)
