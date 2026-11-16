#!/usr/bin/env python3
"""Execute the actual #489 full ITEM callback and original InteractionGuard; only extend QA.
Never generate a second ITEM controller or alter the original author's harness.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
from pathlib import Path

ORIGINAL_HARNESS_BLOB = "eda5f10b70fedc9b7974322360c58551a55196f8"
INSERT_AFTER = "fresh.itemStop()\n"
EXTRA = r'''
-- GQ #517 regressions execute ORIGINAL server ITEM.start and ORIGINAL Guard.allow
-- (not a mirrored helper implementation): preserve full-health HEAL, re-trigger
-- immediately after real damage, shared-world claim, and regular 35s respawn.
local healedMatch=makeSession("TEAM")
FieldItems.start(healedMatch,{
 Vector3.new(0,0,0),Vector3.new(4,0,0),Vector3.new(8,0,0)})
local liveHeal=created[#created-2]
local liveHealPrompt=getPrompt(liveHeal)
check(liveHeal.Name=="ITEM_1_HEAL","TEAM original HEAL target exists")
humanoid.Health=humanoid.MaxHealth
liveHealPrompt.trigger(human)
check(liveHeal.CanQuery and liveHealPrompt.Enabled~=false,
 "full TEAM HP cannot consume field HEAL")
check(humanoid.Health==humanoid.MaxHealth,"full TEAM HP remains unchanged")
humanoid.Health=65
liveHealPrompt.trigger(human)
check(humanoid.Health==100,"damaged TEAM player obtains original 35HP")
check(not liveHeal.CanQuery and liveHealPrompt.Enabled==false,
 "eligible TEAM pickup consumes precisely one shared item")
runTo(now+35)
check(liveHeal.CanQuery and liveHealPrompt.Enabled==true,
 "consumed TEAM HEAL respawns after original 35 seconds")
healedMatch.itemStop()
local brHealMatch=makeSession("BATTLE_ROYALE")
FieldItems.start(brHealMatch,{
 Vector3.new(0,0,0),Vector3.new(4,0,0),Vector3.new(8,0,0)})
local brHeal=created[#created-2]
local brHealPrompt=getPrompt(brHeal)
check(brHeal.Name=="ITEM_1_HEAL","BR original HEAL target exists")
humanoid.Health=100
brHealPrompt.trigger(human)
check(brHeal.CanQuery and brHealPrompt.Enabled~=false,
 "full BR HP cannot consume shared field HEAL")
humanoid.Health=99
brHealPrompt.trigger(human)
check(humanoid.Health==100 and not brHeal.CanQuery,
 "damaged BR player can immediately claim previously skipped HEAL")
check(brHealPrompt.Enabled==false,
 "BR shared item still has one-claim server-authoritative semantics")
brHealMatch.itemStop()
runTo(now+40)
check(not brHeal.CanQuery and brHealPrompt.Enabled==false,
 "retired BR must not respawn old consumed field item")
print("GQ_HEAL_ORIGINAL_FULL_ITEM_GUARD_VM_PASS",assertions,
 "TEAM and BR original ITEM, 0HP waste, consumptions, original LOS and cargo")
'''
def git_blob_hash(data: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def build(author_harness:Path,guard:Path,item:Path,out:Path):
    raw=author_harness.read_bytes()
    assert git_blob_hash(raw)==ORIGINAL_HARNESS_BLOB, "author's VM harness changed; re-review"
    assert guard.exists() and item.exists()
    source=item.read_text(encoding="utf-8")
    assert source.count("if not healUseful(kind,hum.Health,hum.MaxHealth) then return end")==1
    spec=importlib.util.spec_from_file_location("original_item_harness",author_harness)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.SUITE.count(INSERT_AFTER)==1, "author original VM test structure changed"
    module.SUITE=module.SUITE.replace(INSERT_AFTER,INSERT_AFTER+EXTRA,1)
    module.ITEM=item
    module.GUARD=guard
    out.parent.mkdir(parents=True,exist_ok=True)
    module.build(out)
    combined=out.read_text(encoding="utf-8")
    for required in ("local FieldItems=Items","SharedGuard=Guard",
                     "GQ_HEAL_ORIGINAL_FULL_ITEM_GUARD_VM_PASS","function Items.start"):
        assert required in combined
    print("GQ_ORIGINAL_AUTHOR_FULL_ITEM_GUARD_VM_GENERATED",len(combined))

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    for field in ("author-harness","guard","item","out"):
        ap.add_argument("--"+field,required=True,type=Path)
    ns=ap.parse_args()
    build(ns.author_harness,ns.guard,ns.item,ns.out)
