#!/usr/bin/env python3
"""Execute exact helper from generated ITEM (not a hand-transcribed alternate)."""
from pathlib import Path
import sys
src=Path(sys.argv[1]).read_text(encoding="utf-8")
start=src.index("-- GQ_HEAL_NO_WASTE_BEGIN\n")+len("-- GQ_HEAL_NO_WASTE_BEGIN\n")
stop=src.index("-- GQ_HEAL_NO_WASTE_END",start)
helper=src[start:stop]
assert helper.startswith("local function healUseful(")
checks=r'''
local pass=0
local function check(kind,health,maxHealth,expected)
 local actual=healUseful(kind,health,maxHealth)
 assert(actual==expected,tostring(kind)..":"..tostring(health).."/"..tostring(maxHealth))
 pass+=1
end
check("HEAL",100,100,false)
check("HEAL",99,100,true)
check("HEAL",1,100,true)
check("HEAL",0,100,false)
check("HEAL",-1,100,false)
check("HEAL",105,100,false)
check("HEAL",100,0,false)
check("HEAL",0/0,100,false)
check("HEAL",40,0/0,false)
check("HEAL",100,100000,true)
check("DASH",100,100,true)
check("SHIELD",100,100,true)
-- The actual item callback calls the pure predicate before spending a claim.
local claims=0
local cooldownWrites=0
local health=100
local function attemptHeal()
 if not healUseful("HEAL",health,100) then return false end
 claims+=1
 cooldownWrites+=1
 health=math.min(100,health+35)
 return true
end
assert(attemptHeal()==false and claims==0 and cooldownWrites==0)
health=66
assert(attemptHeal()==true and health==100 and claims==1 and cooldownWrites==1)
assert(attemptHeal()==false and claims==1 and cooldownWrites==1)
print("GQ_HEAL_NATIVE_REAL_POLICY_PASS",pass,"and consumption sim PASS")
'''
out=Path(sys.argv[2])
out.write_text(helper+checks,encoding="utf-8")
print("HEAL_NATIVE_EXACT_EXTRACT_PASS",len(helper))
