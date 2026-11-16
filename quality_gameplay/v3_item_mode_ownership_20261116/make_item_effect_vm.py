#!/usr/bin/env python3
"""Execute the REAL #489 prompt/effect suite on the REAL composed #489+#517+#525 ITEM.

Original source-owner #489 owns the original native ITEM+Guard suite. Reuse
its unchanged PRELUDE/FieldItems.start/Guard, add only session ownership stubs
and negative TEAMS/BR transitions. This does not pretend to be Roblox Studio.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from compose_author26 import scripts, ITEM, HOST
from make_native_vm import extract_authority_functions
from patch_sources import HOST_NAME, ITEM_NAME, ITEM_INSERT

ORIGINAL_489_AUTHOR_HARNESS_GIT_BLOB="eda5f10b70fedc9b7974322360c58551a55196f8"
ORIGINAL_489_SHARED_GUARD_GIT_BLOB="ac51ce2077814c7509b8eaf6dafbd05b04a9a1fe"

def git_blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode("ascii")+b"\x00"+raw).hexdigest()

ORIGINAL_FACTORY='''local function makeSession(mode)
 return {world={Parent=true},mode=mode,
  rules={phase="ACTIVE",castles={["101"]={alive=true,heldEggs=0}}}}
end
'''
ATTACHED_FACTORY='''local function makeSession(mode)
 local s={world={Parent=true},mode=mode,
  rules={phase="ACTIVE",castles={["101"]={alive=true,heldEggs=0}}}}
 if mode=="TEAM" or mode=="BATTLE_ROYALE" then
  joined[101]=mode
  sessions[mode]=s
  attach(s,mode)
 end
 return s
end
'''
EXTRA_TESTS=r'''
-- GQ525 ONLY: this extends original #489 suite, with source-selected #517 HEAL.
-- Validate the REAL original pickup prompt callback, not just its canUse() helper.
local rejoined=makeSession("TEAM")
FieldItems.start(rejoined,{
 Vector3.new(0,0,0),Vector3.new(4,0,0),Vector3.new(8,0,0)})
local realHeal=created[#created-2]
local realHealPrompt=getPrompt(realHeal)
humanoid.Health=humanoid.MaxHealth
realHealPrompt.trigger(human)
check(realHeal.CanQuery and humanoid.Health==humanoid.MaxHealth,
 "existing #517 full-HP HEAL must not consume the pickup")
humanoid.Health=15
joined[101]="BATTLE_ROYALE"
realHealPrompt.trigger(human)
check(realHeal.CanQuery and humanoid.Health==15,
 "stale TEAM player in BR cannot consume original HEAL prompt")
joined[101]="TEAM"
local previousSession=sessions.TEAM
sessions.TEAM=makeSession("TEAM")
realHealPrompt.trigger(human)
check(realHeal.CanQuery and humanoid.Health==15,
 "old TEAM session must not claim from newer TEAM epoch")
sessions.TEAM=previousSession
human.Parent=nil
realHealPrompt.trigger(human)
check(realHeal.CanQuery and humanoid.Health==15,
 "disconnected owner cannot claim original item")
human.Parent=mockPlayers
rejoined.rules.phase="FINISHED"
realHealPrompt.trigger(human)
check(realHeal.CanQuery and humanoid.Health==15,
 "finished round cannot claim original item")
rejoined.rules.phase="ACTIVE"
realHealPrompt.trigger(human)
check(not realHeal.CanQuery and humanoid.Health==50,
 "valid TEAM claimant can HEAL after denied attempts; no cooldown consumed")
rejoined.itemStop()
-- Real original server ITEM fails closed even if a hostile script provides no
-- host callback, or throws after the match is active.
local noCallback=makeSession("TEAM")
noCallback.canCollectWorldItem=nil
FieldItems.start(noCallback,{Vector3.new(0,0,0)})
local noCallbackHeal=created[#created]
humanoid.Health=20
getPrompt(noCallbackHeal).trigger(human)
check(noCallbackHeal.CanQuery and humanoid.Health==20,
 "missing server MODE auth must preserve original HEAL item")
noCallback.itemStop()
local throwing=makeSession("TEAM")
throwing.canCollectWorldItem=function() error("invalid session") end
FieldItems.start(throwing,{Vector3.new(0,0,0)})
local throwingHeal=created[#created]
getPrompt(throwingHeal).trigger(human)
check(throwingHeal.CanQuery and humanoid.Health==20,
 "throwing server MODE auth fails closed without consuming ITEM")
throwing.itemStop()
-- Preserve original #489 per-player item cooldown across TEAM and BR.
-- A valid cross-mode pickup must wait for that ORIGINAL cooldown, not bypass it.
runTo(now+40)
-- Verify BR is actually viable: same actor and world interaction after TEAM.
local brLive=makeSession("BATTLE_ROYALE")
FieldItems.start(brLive,{Vector3.new(0,0,0)})
local brHeal=created[#created]
getPrompt(brHeal).trigger(human)
check(not brHeal.CanQuery and humanoid.Health==55,
 "real original BR HEAL pickup works after rejected TEAM/invalid hooks")
brLive.itemStop()
print("GQ525_REAL_ITEM_PROMPT_EFFECT_INTEGRATION", assertions,
 "checks PASS: original #489 Guard/ITEM + original #517 HEAL + exact #525 Lobby hook")
'''
HOOK_PRELUDE='''-- GQ525 only: bring actual #482+#484 Lobby session hook into original #489
-- headless item suite; no replacement source algorithm is invented.
local joined:{[number]:string}={}
local sessions:{[string]:any}={}
local function attach(session:any,mode:string)
{HOOK}
end
'''

def load_author_harness(source:Path):
    raw=source.read_bytes()
    if git_blob(raw)!=ORIGINAL_489_AUTHOR_HARNESS_GIT_BLOB:
        raise ValueError("original #489 native suite drift; do not replace")
    spec=importlib.util.spec_from_file_location("original489_native_harness",source)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def emit(project:Path,receipt_path:Path,author_harness:Path,out:Path,mutant:bool=False):
    found=scripts(project)
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    assert set(receipt["source_sha256"])==set(found)
    for name,(_,path) in found.items():
        assert hashlib.sha256(path.read_bytes()).hexdigest()==receipt["source_sha256"][name],name
    guard=found["EGGRUMBLE_InteractionGuard"][1]
    if git_blob(guard.read_bytes())!=ORIGINAL_489_SHARED_GUARD_GIT_BLOB:
        raise ValueError("original #489 Guard source drift")
    orig=load_author_harness(author_harness)
    # Source-author module still owns the original harness and is not copied.
    orig.GUARD=guard
    orig.ITEM=found[ITEM][1]
    # Pinned #489 author suite actual output from its own build() function.
    if out.exists():
        raise ValueError("refuse to overwrite existing harness")
    out.parent.mkdir(parents=True,exist_ok=True)
    orig.build(out)
    baseline=out.read_text(encoding="utf-8")
    suite=orig.SUITE
    if suite.count(ORIGINAL_FACTORY)!=1:
        raise ValueError("original suite makeSession fixture changed")
    if suite.count('print("[EGGRUMBLE ORIGINAL ITEM + ORIGINAL GUARD VM] PASS"')!=1:
        raise ValueError("original suite end anchor changed")
    new_suite=suite.replace(ORIGINAL_FACTORY,ATTACHED_FACTORY,1)
    new_suite=new_suite.replace(
        'print("[EGGRUMBLE ORIGINAL ITEM + ORIGINAL GUARD VM] PASS"',
        EXTRA_TESTS+'\nprint("[EGGRUMBLE ORIGINAL ITEM + ORIGINAL GUARD VM] PASS"',1)
    hook,_=extract_authority_functions(found[HOST][1].parent)
    # Parent dir holds exactly the generated host/item overlay from our composer.
    additional=HOOK_PRELUDE.replace("{HOOK}",hook)
    if baseline.count(suite)!=1:
        raise ValueError("cannot locate original source author's exact native suite")
    if baseline.count("local FieldItems=Items")!=1:
        raise ValueError("FieldItems author runtime alias missing")
    output=baseline.replace(suite,additional+"\n"+new_suite,1)
    if mutant:
        if output.count(ITEM_INSERT)!=1:
            raise ValueError("cannot mutate real GQ525 guard")
        output=output.replace(ITEM_INSERT,"",1)
    out.write_text(output,encoding="utf-8")
    print("GQ525_REAL_ITEM_VM_AUTHOR_SUITE_REUSED",
          "mutant=UNGUARDED" if mutant else "mutant=NONE",
          hashlib.sha256(out.read_bytes()).hexdigest())

def main():
    p=argparse.ArgumentParser()
    for k in ("project","receipt","author_harness","out"):
        p.add_argument("--"+k.replace("_","-"),type=Path,required=True)
    p.add_argument("--mutant",action="store_true")
    o=p.parse_args()
    emit(o.project,o.receipt,o.author_harness,o.out,o.mutant)

if __name__=="__main__":
    main()
