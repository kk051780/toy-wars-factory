#!/usr/bin/env python3
"""Extract actual assembled patched Game private reset branch into native Luau.

Only tests the actual private gating statement; Roblox engine and genuine
Horde 9-mob spawn are NOT tested by these deterministic stubs.
"""
from __future__ import annotations
import argparse,re
from pathlib import Path
from apply_live_horde_private import GAME,FEATURE

def emit(dist:Path,out:Path):
    s=(dist/"src"/GAME).read_text("utf8")
    assert s.count(FEATURE)==1
    start='if RunService:IsStudio() or ('
    assert s.count(start)==1
    begin=s.index(start)
    end=s.index('\n    end',begin)
    branch=s[begin:end+len('\n    end')]
    assert branch.count('horde:reset(match.serial,serverNow())')==1
    assert 'game.PrivateServerId ~= ""' in branch
    assert 'workspace:GetAttribute("P0D_PRIVATE_LIVE_HORDE") == true' in branch
    luau=r'''--!nocheck
-- Original Game branch extracted exactly from built RC81, NOT engine live evidence.
local studio=true
local allowed=false
local game={PrivateServerId=""}
local RunService={IsStudio=function() return studio end}
local workspace={GetAttribute=function(_,name)
 assert(name=="P0D_PRIVATE_LIVE_HORDE")
 return allowed
end}
local match={serial=7}
local reset_count=0
local seenSerial={}
local horde={reset=function(_,serial,now)
 reset_count+=1
 table.insert(seenSerial,serial)
 assert(now==42)
end}
local function serverNow() return 42 end
local function start()
''' + branch + r'''
end
local function check(label,s,p,allowedAttr,want)
 studio=s
 game.PrivateServerId=p
 allowed=allowedAttr
 reset_count=0
 table.clear(seenSerial)
 start()
 assert(reset_count==want,label.." wrong reset count")
 if want>0 then assert(seenSerial[1]==match.serial,label.." bad serial") end
end
check("STUDIO_ORIGINAL",true,"",false,1)
check("PUBLIC_OFF",false,"",false,0)
check("PUBLIC_UNTRUSTED_ATTRIBUTE",false,"",true,0)
check("PRIVATE_NO_ATTR",false,"private-unique",false,0)
check("PRIVATE_ATTR_NON_BOOLEAN",false,"private-unique","true",0)
check("PRIVATE_OWNER_OPTIN",false,"private-unique",true,1)
match.serial=8
check("PRIVATE_NEXT_ROUND_SERIAL",false,"private-unique",true,1)
check("PRIVATE_DISABLED_AFTER_OPTIN",false,"private-unique",false,0)
print("P0D_REAL_GAME_PRIVATE_HORDE_NATIVE8_GUARD_CASES_PASS")
'''
    out.write_text(luau,"utf8")
    print("P0D_REAL_GAME_PRIVATE_HORDE_GUARD_EXTRACTED",len(branch))
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();emit(a.dist,a.out)
