#!/usr/bin/env python3
"""Native Luau exercises exact 3 selected Host castle prompt guards.

A mutant restores prior siege guard and MUST fail stale same-mode session test.
"""
import argparse
from pathlib import Path
from select_castle import PAIR,HOST,mapping

HARNESS="""local joined={}
local sessions={}
local session={mode="TEAM",rules={},isCurrentHuman=function(player) return player.current==true end}
local entry={id="101"}
local p={UserId=101,current=true}
joined[101]="TEAM"
sessions.TEAM=session
<<GUARDS>>
local function checkYes()
 assert(canSiege(p)==true,"GQ8_SIEGE_VALID_HUMAN")
 assert(canDeco(p)==true,"GQ8_DECO_VALID_OWNER")
 assert(canVault(p)==true,"GQ8_VAULT_VALID_HUMAN")
end
checkYes()
-- A player previously joined this same mode, but their old match was replaced.
sessions.TEAM={mode="TEAM",rules={}}
assert(canSiege(p)==nil,"GQ8_CASTLE_STALE_SESSION_SIEGE_MUTANT_RED")
assert(canDeco(p)==nil,"GQ8_CASTLE_STALE_SESSION_DECO_MUTANT_RED")
assert(canVault(p)==nil,"GQ8_CASTLE_STALE_SESSION_VAULT_MUTANT_RED")
sessions.TEAM=session
p.current=false
assert(canSiege(p)==nil and canDeco(p)==nil and canVault(p)==nil,"GQ8_REMOVED_PARTICIPANT")
p.current=true
session.isCurrentHuman=nil
assert(canSiege(p)==nil and canDeco(p)==nil and canVault(p)==nil,"GQ8_MISSING_SERVER_AUTHORITY")
session.isCurrentHuman=function(player) return player.current==true end
joined[101]="BATTLE_ROYALE"
assert(canSiege(p)==nil and canVault(p)==nil,"GQ8_WRONG_QUEUE")
joined[101]="TEAM"
entry.id="202"
assert(canDeco(p)==nil,"GQ8_NOT_OWN_CASTLE")
print("GQ8_CASTLE_CURRENT_ROUND_NATIVE_8_CASES_PASS")
"""

def native_function(name,anchor):
    # Verify the raw guard was actually sourced from the CURRENT selected Host.
    return "local function "+name+"(p)\n"+anchor+"\n return true\nend\n"

def generate(project,out,mutant):
    _,files=mapping(project.resolve(strict=True))
    src=files[HOST].read_text(encoding="utf-8")
    guards=[b for _,b in PAIR]
    if any(src.count(x)!=1 for x in guards):
        raise ValueError("RED_SELECTED3_CASTLE_GUARDS_NOT_CURRENT_SOURCE")
    functions="".join(native_function(name,anchor) for name,anchor in zip(
      ("canSiege","canDeco","canVault"),guards))
    out.write_text(HARNESS.replace("<<GUARDS>>",functions)+"\n",encoding="utf-8")
    muted=[PAIR[0][0],guards[1],guards[2]]
    mfunc="".join(native_function(name,anchor) for name,anchor in zip(
      ("canSiege","canDeco","canVault"),muted))
    mutant.write_text(HARNESS.replace("<<GUARDS>>",mfunc)+"\n",encoding="utf-8")
    print("GQ8_CASTLE_EXACT_CURRENT_HOST_NATIVE_AND_OLD_SIEGE_MUTANT_GENERATED")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--project",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--mutant",type=Path,required=True)
    v=ap.parse_args()
    generate(v.project,v.out,v.mutant)
