#!/usr/bin/env python3
"""Safe two-author source-selective integration into ONE existing Combat module.

Reuses #510 original mage author patch without editing its files and the sole
#516 status callback patch. Both apply only to #482 pinned original Combat.
This is an isolated non-production 27-source candidate; no RC writer action.
"""
import argparse
import hashlib
import importlib.util
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
LANE=Path(__file__).resolve().parents[1]
ORIGIN=ROOT/"handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116/EGGRUMBLE_SevenRoleCombat.luau"
ORIG_GIT_BLOB="66e666418b7c23d41f87faa5d61eb6e2770a463e"
IMPORT_BASE='local AttackGeometry=require(script.Parent:WaitForChild("EGGRUMBLE_AttackGeometry"))'
STATUS_IMPORT='local StatusTickFence=require(script.Parent:WaitForChild("EGGRUMBLE_StatusTickFence"))'
STATUS_START="local function secondaryEffect("
STATUS_END="\nlocal function execute("
HEAL_START="local function healAllies("
HEAL_END="\n-- Status effects are real server damage / movement changes"

def git_blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def unique_segment(body:str,start:str,end:str)->str:
    assert body.count(start)==1 and body.count(end)==1,(start,end)
    first=body.index(start)
    last=body.index(end,first)
    return body[first:last]

def load_mage_patch(path:Path):
    assert path.is_file()
    spec=importlib.util.spec_from_file_location("_gq510_author_patch",path)
    assert spec is not None and spec.loader is not None
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.SOURCE_BLOB==ORIG_GIT_BLOB,"mage owner blob changed"
    return module.patch

def compose(mage_builder:Path)->str:
    raw=ORIGIN.read_bytes()
    assert git_blob(raw)==ORIG_GIT_BLOB,"#482 source drift"
    origin=raw.decode("utf-8")
    status=(LANE/"EGGRUMBLE_SevenRoleCombat.patched.luau").read_text()
    mage=load_mage_patch(mage_builder)(origin)
    assert mage!=origin and STATUS_IMPORT not in mage
    assert origin.count(IMPORT_BASE)==1 and status.count(STATUS_IMPORT)==1
    orig_block=unique_segment(origin,STATUS_START,STATUS_END)
    status_block=unique_segment(status,STATUS_START,STATUS_END)
    assert orig_block!=status_block
    # Validate the status-only author's entire source delta: no hidden edits.
    expected_status=origin.replace(IMPORT_BASE,IMPORT_BASE+"\n"+STATUS_IMPORT)
    expected_status=expected_status.replace(orig_block,status_block)
    assert expected_status==status,"#516 status source drift outside owned anchors"
    # Validate #510 patch remains outside the sole status-owned function.
    assert unique_segment(mage,STATUS_START,STATUS_END)==orig_block
    assert unique_segment(mage,HEAL_START,HEAL_END)!=unique_segment(origin,HEAL_START,HEAL_END)
    assert unique_segment(status,HEAL_START,HEAL_END)==unique_segment(origin,HEAL_START,HEAL_END)
    out=mage.replace(orig_block,status_block)
    assert out!=mage and out.count(IMPORT_BASE)==1 and STATUS_IMPORT not in out
    out=out.replace(IMPORT_BASE,IMPORT_BASE+"\n"+STATUS_IMPORT)
    assert unique_segment(out,HEAL_START,HEAL_END)==unique_segment(mage,HEAL_START,HEAL_END)
    assert unique_segment(out,STATUS_START,STATUS_END)==status_block
    assert out.count(STATUS_IMPORT)==1 and out.count("StatusTickFence.canTick(")==1
    assert out.count('h.Health=math.min(h.MaxHealth,h.Health+25)')==1
    assert out.count('botHum.Health=math.min(botHum.MaxHealth,botHum.Health+25)')==1
    assert out.count('h:TakeDamage(tick)')==1
    assert out.count('function HeroCombat.equip')==origin.count('function HeroCombat.equip')
    assert out.count('local function healAllies(')==1 and out.count('local function secondaryEffect(')==1
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--mage-builder",required=True,type=Path)
    parser.add_argument("--out",required=True,type=Path)
    args=parser.parse_args()
    candidate=compose(args.mage_builder.resolve(strict=True))
    target=args.out.resolve()
    assert target.parent.is_dir(),"precreated artifact directory only"
    assert target!=ORIGIN.resolve()
    target.write_text(candidate,encoding="utf-8")
    print("GQ_510_516_7ROLE_COMBAT_EXACT_UNION_PASS",len(candidate),
      hashlib.sha256(candidate.encode()).hexdigest())

if __name__=="__main__":
    main()
