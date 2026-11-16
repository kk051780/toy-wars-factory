#!/usr/bin/env python3
"""Pin and compose existing #529 4-author SINGLE Combat + #530 dead-caster guard.

The #529 author composer is reused unmodified; do not invent a second Game,
Combat, Remote, AI, damage authority, or rewrite its source. Private Place only.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ORIGINAL_529_HEAD = "99ae00fbec2b5057c54e938d741ea99b0caad924"
ORIGINAL_529_FOUR_SHA256 = "c4b464560ba6c6878b5e15af891f595f6f85130cf720c59948980f05d6565470"
UPSTREAM = Path("quality_gameplay/v3_human_stealth_pvp_20261116/compose_four_author.py")
ENTRY = (
    " local char,root,h=characterOf(p)\n"
    " if not char or not root or not h then return end\n"
    " local now=os.clock()"
)
REPLACEMENT = (
    " local char,root,h=characterOf(p)\n"
    " if not char or not root or not h then return end\n"
    " -- GQ_DEAD_CASTER_FENCE: reject death/downed before skill cost, heal or damage.\n"
    " if h.Health<=0 or char:GetAttribute(\"EGGRUMBLE_Downed\")==true then return end\n"
    " local now=os.clock()"
)

def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def four_author_module():
    spec=importlib.util.spec_from_file_location("pinned_gq529_four_author", UPSTREAM.resolve(strict=True))
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def apply_to_combined(original: str) -> str:
    if sha256(original)!=ORIGINAL_529_FOUR_SHA256:
        raise ValueError("RED_529_FOUR_AUTHOR_SOURCE_LOCK_DRIFT")
    if original.count(ENTRY)!=1:
        raise ValueError("RED_ORIGINAL_EXECUTE_ENTRY_NOT_UNIQUE")
    start=original.index("local function execute(session:any,p:Player,role:string,slot:string)")
    anchor=original.index(ENTRY)
    guard=original.index("perPlayer[key]=now",start)
    limit=original.index("function HeroCombat.roleOrder()",start)
    if not(start < anchor < guard < limit):
        raise ValueError("RED_UNEXPECTED_EXECUTE_SCOPE")
    result=original.replace(ENTRY,REPLACEMENT,1)
    if result.replace(REPLACEMENT,ENTRY,1)!=original:
        raise ValueError("RED_FIVE_AUTHOR_REVERSAL")
    for phrase in (
        "humanCombatTargetable(",
        "StatusTickFence.canTick(",
        "local function safeMove(session:any,char:Model,root:BasePart,amount:number):boolean",
        "botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)",
        "function HeroCombat.equip(",
        "function HeroCombat.clear(",
    ):
        if result.count(phrase)!=original.count(phrase):
            raise ValueError("RED_FOUR_AUTHOR_REGRESSION: "+phrase)
    if result.count("GQ_DEAD_CASTER_FENCE:")!=1:
        raise ValueError("RED_DUPLICATE_FENCE")
    return result

def compose(output: Path, project: Path, receipt: Path) -> None:
    four=four_author_module()
    old, upstream_heads=four.build_union()
    new=apply_to_combined(old)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(new,encoding="utf-8")
    five_heads={
        **upstream_heads,
        "five_author_combat_sha256":sha256(new),
        "prior_529_head":ORIGINAL_529_HEAD,
        "dead_cast_530":"SOURCE_ONLY_SOFT_CLAIM_NOT_GRANTED",
        "dead_cast_530_source_only":True,
        "dead_cast_530_rollback":"remove only two inserted lines or disable entire optional overlay",
        "original_482_game_sources_unchanged":20,
        "official_rc_adopted":False,
    }
    four.compose_private(output,project,receipt,five_heads)
    data=json.loads(receipt.read_text(encoding="utf-8"))
    data["status"]="FIVE_AUTHOR_PRIVATE22_SOURCE_ONLY_NOT_FORMAL_RC"
    data["combination"]="original482+mage510+dot516+warp524+human529+deadguard530"
    data["combat_source_overlays"]=1
    data["source_author_review_required"]=True
    data["claim_granted"]=False
    data["project_mode"]="NOT_REAL_STUDIO_TEST"
    receipt.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    pj=json.loads(project.read_text(encoding="utf-8"))
    pj["name"]="GQ_5_AUTHOR_WITH_DEAD_CASTER_PRIVATE22_NOT_OFFICIAL_RC"
    project.write_text(json.dumps(pj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    assert data["private_source_count"]==22
    assert data["original_modules_byte_identical"]==20
    assert data["combat_four_author_sha256"]==ORIGINAL_529_FOUR_SHA256
    print("FIVE_AUTHOR_COMBAT_REUSE_AND_REVERSE_PASS",sha256(new))
    print("FIVE_AUTHOR_PRIVATE22_SOURCE_MAP_PASS",len(data["source_sha256"]))

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--combat",required=True,type=Path)
    p.add_argument("--project",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    p.add_argument("--verify-place",type=Path)
    a=p.parse_args()
    if a.verify_place:
        four_author_module().verify_place(a.project,a.verify_place,a.receipt)
    else:
        compose(a.combat,a.project,a.receipt)

if __name__=="__main__":
    main()
