#!/usr/bin/env python3
"""Run REAL #509 Rules + #489 FieldItems + #482 Guard in ONE Luau native VM.
The original #489 suite executes unmodified first, followed by actual cross-module
test cases. Source is embedded unchanged except replacement of terminal return.
"""
import argparse
import importlib.util
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RULES=ROOT.parent/"P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"/"EGGRUMBLE_CastleMatchRules.luau"
RULES_BLOB="ed87d70e7df94279af737871e8e439b9fc108d4f"
ITEM_BLOB="107046cb0bf81fed9e3cba1699ada31571e44a22"
GUARD_BLOB="ac51ce2077814c7509b8eaf6dafbd05b04a9a1fe"

TESTS=r'''
local coupled=0
local function confirm(value,msg)
 coupled+=1
 assert(value,"COUPLED_RULES_ITEM_"..msg)
end
local function actual(mode,cap)
 local humans=if mode=="TEAM" then {"101","202"} else {"101","202","303"}
 local roster=Rules.makeRoster(mode,humans,#humans)
 local rules=Rules.new(mode,roster,3)
 Rules.start(rules)
 local session={mode=mode,world={Parent=true},rules=rules}
 local pos={}
 for i=1,cap do table.insert(pos,Vector3.new((i-1)*4,0,0)) end
 FieldItems.start(session,pos)
 local h,d,s=created[#created-cap+1],created[#created-cap+2],created[#created-cap+3]
 return rules,session,h,d,s
end
runTo(now+1)
humanoid.Health=45
humanoid.WalkSpeed=16
local a,team,h,d,s=actual("TEAM",6)
confirm(Rules.auditEggConservation(a).valid,"TEAM_INITIAL_CONSERVATION")
local teamH,teamD,teamS=getPrompt(h),getPrompt(d),getPrompt(s)
local oldForce=#forces
-- Real Rules.takeFieldEgg must change the SAME session.rules table read by ITEM.
confirm(Rules.takeFieldEgg(a,"101","FIELD_1")==1,"TEAM_REAL_FIELD_PICKUP")
confirm(a.castles["101"].heldEggs==1,"TEAM_SHARED_CARGO")
teamD.trigger(human)
teamS.trigger(human)
confirm(d.CanQuery and s.CanQuery and humanoid.WalkSpeed==16,"TEAM_CARGO_REFUSES_DASH")
confirm(#forces==oldForce,"TEAM_CARGO_REFUSES_SHIELD")
teamH.trigger(human)
confirm(humanoid.Health==80 and not h.CanQuery,"TEAM_CARRIER_HEAL_ALLOWED")
confirm(Rules.depositEggs(a,"101",1)==1 and a.castles["101"].heldEggs==0,
 "TEAM_DEPOSIT_REMOVES_CARGO")
teamD.trigger(human)
confirm(humanoid.WalkSpeed==27 and not d.CanQuery,"TEAM_POST_DEPOSIT_DASH_ALLOWED")
confirm(Rules.takeFieldEgg(a,"101","FIELD_2")==1,"TEAM_REAL_SECOND_PICKUP")
runTo(now+.25)
confirm(humanoid.WalkSpeed==16,"TEAM_CARGO_CLEARS_RUNNING_DASH")
local dropped,dropIds=Rules.onCarrierEliminated(a,"101")
confirm(dropped==1 and #dropIds==1 and a.castles["101"].heldEggs==0,
 "TEAM_LIVE_DEATH_DROPS_REAL_TOKEN")
confirm(Rules.auditEggConservation(a).valid,"TEAM_LIVE_DEATH_CONSERVATION")
teamS.trigger(human)
confirm(#forces==oldForce+1 and forces[#forces].Parent==avatar,"TEAM_POST_DROP_SHIELD_ALLOWED")
Rules.takeFieldEgg(a,"101","FIELD_3")
runTo(now+.25)
confirm(forces[#forces].Parent==nil and forces[#forces].destroyed,
 "TEAM_CARGO_CLEARS_RUNNING_SHIELD")
confirm(Rules.auditEggConservation(a).valid,"TEAM_PRE_WIN_CONSERVATION")
for _=1,4 do Rules.damageCastle(a,"202","101",250) end
confirm(a.phase=="FINISHED" and a.winner=="RED","TEAM_REAL_CASTLE_WIN")
local preSerial,preField,preEvent=a.eggSerial,a.fieldEggs,#a.events
local noDrop,noIds=Rules.onCarrierEliminated(a,"101")
confirm(noDrop==0 and #noIds==0 and a.eggSerial==preSerial and a.fieldEggs==preField
 and #a.events==preEvent,"TEAM_LATE_DEATH_IS_FROZEN")
confirm(Rules.auditEggConservation(a).valid,"TEAM_POSTWIN_CONSERVATION")
local unusedHeal=created[#created-2]
confirm(unusedHeal.Name=="ITEM_4_HEAL","TEAM_SECOND_HEAL_EXISTS")
getPrompt(unusedHeal).trigger(human)
confirm(unusedHeal.CanQuery,"TEAM_FINISHED_DENIES_NEW_ITEM")
team.itemStop()
runTo(now+6)
humanoid.Health=50
humanoid.WalkSpeed=16
local b,royale,bh,bd,bs=actual("BATTLE_ROYALE",3)
local brDash,brShield=getPrompt(bd),getPrompt(bs)
local beforeShield=#forces
confirm(Rules.takeEggs(b,"101",1,"202")==1,"BR_REAL_ENEMY_CASTLE_STEAL")
brDash.trigger(human)
brShield.trigger(human)
confirm(bd.CanQuery and bs.CanQuery and humanoid.WalkSpeed==16,
 "BR_CARGO_REFUSES_BUFFS")
confirm(Rules.depositEggs(b,"101",1)==1 and b.castles["101"].heldEggs==0,
 "BR_REAL_DEPOSIT_REMOVES_CARGO")
brShield.trigger(human)
confirm(#forces==beforeShield+1 and forces[#forces].Parent==avatar,
 "BR_POST_DEPOSIT_SHIELD_ALLOWED")
Rules.takeEggs(b,"101",1,"303")
runTo(now+.25)
confirm(forces[#forces].Parent==nil,"BR_REAL_CARGO_CLEARS_SHIELD")
confirm(Rules.auditEggConservation(b).valid,"BR_CONSERVATION")
for _,enemy in ipairs({"202","303"}) do
 for _=1,4 do Rules.damageCastle(b,enemy,"101",250) end
end
confirm(b.phase=="FINISHED" and b.winner=="101","BR_REAL_CASTLES_WIN")
local oldSerial,oldField,oldEvents=b.eggSerial,b.fieldEggs,#b.events
local zero,ids=Rules.onCarrierEliminated(b,"101")
confirm(zero==0 and #ids==0 and oldSerial==b.eggSerial
 and oldField==b.fieldEggs and oldEvents==#b.events,
 "BR_LATE_DEATH_IS_FROZEN")
brDash.trigger(human)
confirm(bd.CanQuery and humanoid.WalkSpeed==16,"BR_FINISHED_DENIES_NEW_ITEM")
confirm(Rules.auditEggConservation(b).valid,"BR_POSTWIN_CONSERVATION")
royale.itemStop()
print("COUPLED_REAL_RULES_ITEM_GUARD_NATIVE_PASS",coupled)
'''

def blob(path):
 return subprocess.check_output(["git","hash-object",str(path)],text=True).strip()

def build(builder_file,out,negative=False):
 spec=importlib.util.spec_from_file_location("original_gq489_builder",builder_file)
 lib=importlib.util.module_from_spec(spec)
 spec.loader.exec_module(lib)
 assert blob(RULES)==RULES_BLOB,("patch drift",blob(RULES))
 assert blob(lib.ITEM)==ITEM_BLOB,("item author drift",blob(lib.ITEM))
 assert blob(lib.GUARD)==GUARD_BLOB,("guard author drift",blob(lib.GUARD))
 lib.build(out)
 script=out.read_text(encoding="utf-8")
 rules=RULES.read_text(encoding="utf-8")
 assert rules.rstrip().endswith("return M")
 rules=rules[:rules.rfind("\nreturn M")]+"\nlocal Rules=M\n"
 if negative:
  after=rules.replace("actor.heldEggs+=1\n table.insert(m.events",
      "actor.heldEggs+=0\n table.insert(m.events",1)
  assert after!=rules and after.count("actor.heldEggs+=0")==1
  rules=after
 marker="\nlocal FieldItems=Items\n"
 assert script.count(marker)==1
 out.write_text(script.replace(marker,marker+"\n"+rules+"\n",1)+"\n"+TESTS,encoding="utf-8")
 print("REAL_RULES_ITEM_GUARD_PINNED_SOURCE_PASS",out,negative)

def main():
 p=argparse.ArgumentParser()
 p.add_argument("--original-item-builder",type=Path,required=True)
 p.add_argument("--out",type=Path,required=True)
 p.add_argument("--mutant-out",type=Path,required=True)
 a=p.parse_args()
 assert a.out.resolve()!=a.mutant_out.resolve()
 src=a.original_item_builder.resolve(strict=True)
 build(src,a.out)
 build(src,a.mutant_out,True)

if __name__=="__main__":main()
