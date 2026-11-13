#!/usr/bin/env python3
"""Execute exact committed pure DojoRules in native Luau, not a Python imitation."""
from pathlib import Path
import argparse,hashlib
ROOT=Path(__file__).resolve().parents[1]
S=ROOT/"inputs/DojoRules.luau"
raw=S.read_bytes()
assert hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()=="120bac439c979310c9ddeb2fcf2ffa002b6d1add"
source=raw.decode("utf8")
assert source.rstrip().endswith("return Dojo")
header=source.rstrip()[:-len("return Dojo")]
tests=r'''
local n=0
local function eq(tag,got,expected)
    n+=1
    if got~=expected then error("P0D_DOJO_NATIVE_TEST_FAIL:"..tag.." got="..tostring(got).." expected="..tostring(expected)) end
end
local function near(tag,got,want)
    n+=1
    if math.abs(got-want)>0.0001 then error("P0D_DOJO_NATIVE_TEST_FAIL:"..tag.." got="..tostring(got).." expected="..tostring(want)) end
end
local s=Dojo.new()
eq("default beast level",s.level.BEAST,1)
eq("default weapon level",s.level.WEAPON,1)
eq("default beast xp",s.xp.BEAST,0)
eq("default weapon xp",s.xp.WEAPON,0)
eq("default active",s.current,"NONE")
eq("public/offline cannot train",Dojo.tick(s,"BEAST",1,true,false),false)
eq("no public abuse",s.xp.BEAST,0)
eq("reject unknown kind",Dojo.tick(s,"MONEY",1,true,true),false)
eq("reject zero delta",Dojo.tick(s,"BEAST",0,true,true),false)
eq("reject negative delta",Dojo.tick(s,"BEAST",-2,true,true),false)
eq("reject oversized delta",Dojo.tick(s,"BEAST",20,true,true),false)
eq("reject nil state",Dojo.tick(nil,"BEAST",.5,true,true),false)
eq("single no-friend training",Dojo.tick(s,"BEAST",1,false,true),true)
near("plain earned XP",s.xp.BEAST,1)
near("plain elapsed",s.trainedSeconds.BEAST,1)
eq("single friend training",Dojo.tick(s,"BEAST",1,true,true),true)
near("friend earned 1.5 XP",s.xp.BEAST,2.5)
eq("friend state true",s.friendBonus,true)
eq("active beast",s.current,"BEAST")
for i=1,5 do Dojo.tick(s,"BEAST",1,true,true) end
eq("level2 after 10 XP",s.level.BEAST,2)
near("level2 pending XP",s.xp.BEAST,0)
near("weapon not trained",s.xp.WEAPON,0)
near("beast PvE bonus 1.05",Dojo.pveDamageMultiplier(s,"BEAST"),1.05)
near("untrained weapon PvE bonus1",Dojo.pveDamageMultiplier(s,"WEAPON"),1)
local first=Dojo.view(s)
eq("view beast level",first.beast,2)
eq("view weapon level",first.weapon,1)
eq("view active beast",first.active,"BEAST")
eq("view friend yes",first.friendBonus,true)
eq("view is not saved",first.sessionOnly,true)
eq("view level2 need15",first.need,15)
eq("view level2 pve",first.beastPve,1.05)
eq("baseline missing",Dojo.pveDamageMultiplier(nil,"BEAST"),1)
eq("unknown kind no buff",Dojo.pveDamageMultiplier(s,"OTHER"),1)
for i=1,140 do Dojo.tick(s,"BEAST",1,false,true) end
eq("max beast level5",s.level.BEAST,5)
near("max beast buff1.2",Dojo.pveDamageMultiplier(s,"BEAST"),1.2)
near("cap max trained minutes",s.trainedSeconds.BEAST,148)
for i=1,50 do Dojo.tick(s,"BEAST",1,false,true) end
near("no session time above180",s.trainedSeconds.BEAST,180)
eq("cap after180",Dojo.tick(s,"BEAST",1,false,true),false)
eq("still no weapon XP",s.xp.WEAPON,0)
eq("other station works",Dojo.tick(s,"WEAPON",1,false,true),true)
eq("weapon becomes active",s.current,"WEAPON")
near("weapon XP1",s.xp.WEAPON,1)
local v=Dojo.view(nil)
eq("nil baseline level",v.beast,1)
eq("nil baseline PVE",v.weaponPve,1)
eq("nil inactive",v.active,"NONE")
eq("no paid status",v.sessionOnly,true)
eq("noninteger level fails closed",Dojo.pveDamageMultiplier({level={BEAST=2.5}},"BEAST"),1)
assert(n>=45)
print("P0D_H1_DOJO_NATIVE_"..tostring(n).."_ASSERTIONS_PASS")
'''
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--write",required=True,type=Path)
 args=p.parse_args()
 args.write.parent.mkdir(parents=True,exist_ok=True)
 args.write.write_text(header+tests,encoding="utf8")
 print("P0D_H1_NATIVE_ORIGINAL_DOJO_TEST_GENERATED",args.write)
