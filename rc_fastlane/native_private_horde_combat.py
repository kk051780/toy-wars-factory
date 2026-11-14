#!/usr/bin/env python3
"""Use real patched official Game code condition lines, not invented mock guards."""
from __future__ import annotations
import argparse
from pathlib import Path
from apply_private_horde_combat import GAME,RESET_AUTH,HIT_NEW,TICK_NEW,BOT_NEW

def emit(dist:Path,out:Path):
    source=(dist/"src"/GAME).read_text("utf8")
    assert source.count(RESET_AUTH)==1
    assert source.count(HIT_NEW)==source.count(TICK_NEW)==source.count(BOT_NEW)==1
    attack_line=HIT_NEW.splitlines()[1]
    tick_line=TICK_NEW.splitlines()[1]
    reset_line=RESET_AUTH
    assert "game.PrivateServerId" in attack_line and "game.PrivateServerId" in tick_line
    assert 'game.PrivateServerId' in reset_line
    intro=r'''--!nocheck
-- Actual original Game gate predicates, deterministic native QA only.
local studio=true
local allow=false
local game={PrivateServerId=""}
local workspace={GetAttribute=function(_,key)
 assert(key=="P0D_PRIVATE_LIVE_HORDE_NINE")
 return allow
end}
local RunService={IsStudio=function()return studio end}
local match={serial=3,phase="ACTIVE"}
local resetCount=0
local horde={reset=function(_,serial,t)
 assert(serial==match.serial and t==7)
 resetCount+=1
end}
local function serverNow()return 7 end
local function doReset()
'''
    middle=r'''
end
local function attackAllowed()
'''
    tickIntro=r'''
        return true
    end
    return false
end
local function tickAllowed()
'''
    endcode=r'''
        return true
    end
    return false
end
local function check(label,isStudio,id,privateAttr,expected)
 studio=isStudio;game.PrivateServerId=id;allow=privateAttr
 resetCount=0
 doReset()
 assert(resetCount==(if expected then 1 else 0),label..":RESET")
 assert(attackAllowed()==expected,label..":ATTACK")
 assert(tickAllowed()==expected,label..":HORDE_TICK")
end
check("STUDIO",true,"",false,true)
check("PUBLIC_OFF",false,"",false,false)
check("PUBLIC_ATTR_SPOOF",false,"",true,false)
check("PRIVATE_OFF",false,"private-test-id",false,false)
check("PRIVATE_STRING_NOT_BOOLEAN",false,"private-test-id","true",false)
check("PRIVATE_ON",false,"private-test-id",true,true)
match.serial=4
check("PRIVATE_NEXT_EPOCH",false,"private-test-id",true,true)
check("PRIVATE_OWNER_REVOKED",false,"private-test-id",false,false)
match.phase="LOBBY"
assert(not tickAllowed(),"HORDE_TICK_FORBIDDEN_IN_LOBBY")
print("P0D_REAL_GAME_HORDE_RESET_HIT_TICK_PRIVATE8_NATIVE_PASS")
'''
    native=intro+reset_line+middle+attack_line+tickIntro+tick_line+endcode
    out.write_text(native,"utf8")
    print("P0D_ISSUE444_REAL_AUTHOR_GAME_THREE_GUARDS_EXTRACTED",len(native))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();emit(a.dist,a.out)
