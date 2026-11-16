#!/usr/bin/env python3
"""Combine two independently AUTHOR-composed 28-source projects into a real 30-source Place.
No new GAME, ITEM, neutral boss, score, lobby or counter implementation.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

COMBO={"EGGRUMBLE_RoundAttributeFence","EGGRUMBLE_RoundAttributeFenceServer"}
BOSS={"EGGRUMBLE_BossCreditPolicy","EGGRUMBLE_BossCreditRoundFence"}
ITEM="EGGRUMBLE_FieldItemPickups"
FIXED_ITEM_SHA="55f7cce975c05a263047192043d20b8b6c1de869d5c44c8c5b76d7d70dfe582c"

def sha(p:Path)->str:return hashlib.sha256(p.read_bytes()).hexdigest()

def mapped(p:Path):
    src=json.loads(p.read_text(encoding="utf-8"))
    out={}
    def walk(node,chain=()):
        if not isinstance(node,dict):return
        if "$path" in node:
            assert set(node)=={"$path"},"duplicate authority specification"
            path=(p.parent/node["$path"]).resolve(strict=True)
            name=chain[-1]
            assert name not in out,("duplicate script name",name)
            cls=("Script" if path.name.endswith(".server.luau") else
                 "LocalScript" if path.name.endswith(".client.luau") else "ModuleScript")
            out[name]=(chain,path,cls)
        else:
            for key,value in node.items():
                if not key.startswith("$"):walk(value,chain+(key,))
    walk(src["tree"])
    return src,out

def compose(combo:Path,boss:Path,out:Path,receipt:Path):
    original,cmap=mapped(combo)
    _,bmap=mapped(boss)
    assert len(cmap)==28 and len(bmap)==28
    assert COMBO.issubset(cmap) and BOSS.isdisjoint(cmap)
    assert BOSS.issubset(bmap) and COMBO.isdisjoint(bmap)
    assert set(cmap)-COMBO==set(bmap)-BOSS
    common=set(cmap)-COMBO
    assert len(common)==26 and ITEM in common
    for name in common:
        assert cmap[name][0]==bmap[name][0],("author path conflict",name)
        assert cmap[name][1]==bmap[name][1],("composer src path conflict",name)
        assert sha(cmap[name][1])==sha(bmap[name][1]),("author source conflict",name)
    assert sha(cmap[ITEM][1])==FIXED_ITEM_SHA
    for name in COMBO:
        assert cmap[name][0][0]=="ServerScriptService"
    for name in BOSS:
        assert bmap[name][0][0]=="ServerScriptService"
    assert out.parent==combo.parent==boss.parent
    manifest=original
    for name in sorted(BOSS):
        _,path,_=bmap[name]
        manifest["tree"]["ServerScriptService"][name]={"$path":os.path.relpath(path,out.parent).replace(os.sep,"/")}
    manifest["name"]="GQ_517_ITEM_512_COMBO_514_BOSS_PRIVATE30_NOT_RC"
    out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    _,allmap=mapped(out)
    assert len(allmap)==30 and set(allmap)==set(cmap)|BOSS
    for name in cmap:assert allmap[name]==cmap[name]
    for name in BOSS:assert allmap[name]==bmap[name]
    record={"status":"PRIVATE_CROSS_AUTHOR_30_SOURCE_ONLY_NOT_OFFICIAL_RC",
      "source_count":30,"base26_source_count":26,"addon_combo2":2,"addon_boss2":2,
      "shared_author_scripts_identical":26,"changed_original_author_code":0,
      "author_code_source":"#482/#484/#485/#487/#489 original + generated HEAL hunk #517; #512 combo, #514 boss exact",
      "source_sha256":{name:sha(z[1]) for name,z in sorted(allmap.items())},
      "sources":{name:{"service":"/".join(z[0][:-1]),"class":z[2],"sha256":sha(z[1])}
                 for name,z in sorted(allmap.items())},
      "official_rc_adopted":False,"source_claim":"SOFT_NOT_GRANTED",
      "studio":"NOT_TESTED","android":"NOT_TESTED","owner":"NO_GO",
      "production_guard_mismatch":"GQ512 combo server Studio-only; GQ514 boss server live-enabled; original V3 GAME remains Studio-guarded"}
    receipt.write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_517_512_514_COMPOSER_AUTHOR30_REUSE_PASS",len(common),len(allmap))

def verify(project:Path,place:Path,receipt:Path,compiler:Path):
    _,expected=mapped(project)
    assert len(expected)==30
    observed={}
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        cls=item.attrib.get("class")
        if cls not in ("Script","ModuleScript","LocalScript"):continue
        props=item.find("Properties")
        if props is None:continue
        name=props.findtext("string[@name='Name']")
        if not name:continue
        assert name not in observed,("duplicate embedded script",name)
        source=props.findtext("ProtectedString[@name='Source']")
        if source is None:source=props.findtext("string[@name='Source']")
        observed[name]=(cls,(source or "").replace("\r\n","\n"))
    assert set(observed)==set(expected),("Place source map missing/extra",set(expected)-set(observed),set(observed)-set(expected))
    for name,(_,path,cls) in expected.items():
        assert observed[name]==(cls,path.read_text(encoding="utf-8").replace("\r\n","\n")),("Place source/class conflict",name)
        subprocess.run([str(compiler),"--text",str(path)],stdout=subprocess.DEVNULL,check=True)
    r=json.loads(receipt.read_text(encoding="utf-8"))
    assert r["source_count"]==30 and r["shared_author_scripts_identical"]==26
    assert r["source_sha256"]=={k:sha(x[1]) for k,x in expected.items()}
    r["place_bytes"]=place.stat().st_size
    r["place_sha256"]=sha(place)
    r["source_exact"]="30/30"
    r["native_compiled"]="30/30"
    receipt.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("GQ_517_512_514_PRIVATE30_NATIVE_ROJO_SOURCE_CLASS_EXACT_PASS",r["place_bytes"],r["place_sha256"])

def make_policy_vm(combo:Path,boss:Path,out:Path):
    cs=combo.read_text(encoding="utf-8")
    bs=boss.read_text(encoding="utf-8")
    assert cs.rstrip().endswith("return Fence")
    assert bs.rstrip().endswith("return Policy")
    cs=cs.rstrip()[:-len("return Fence")]+"local ComboFence=Fence"
    bs=bs.rstrip()[:-len("return Policy")]+"local BossPolicy=Policy"
    tests=r'''
local n=0
local function check(prev,next,combo,boss)
 assert(ComboFence.shouldClear(prev,next)==combo,
  "COMBO transition "..tostring(prev).." -> "..tostring(next))
 assert(BossPolicy.shouldReset(prev,next)==boss,
  "BOSS transition "..tostring(prev).." -> "..tostring(next))
 n+=1
end
check(nil,nil,false,false)
check(nil,"TEAM",false,true)
check("TEAM",nil,true,true)
check("BATTLE_ROYALE",nil,true,true)
check("TEAM","BATTLE_ROYALE",false,true)
check("BATTLE_ROYALE","TEAM",false,true)
check("TEAM","TEAM",false,false)
check("BATTLE_ROYALE","BATTLE_ROYALE",false,false)
check("BOGUS",nil,false,false)
check(nil,"BOGUS",false,false)
check("BOGUS","TEAM",false,false)
local write={}
local p={}
function p:SetAttribute(k,v)write[k]=v end
ComboFence.clear(p)
assert(write["EGGRUMBLE_Combo"]==0 and write["EGGRUMBLE_BestCombo"]==0)
assert(write["EGGRUMBLE_BossDefeats"]==nil,"COMBO code overwrote boss writer")
print("GQ_517_512_514_REAL_AUTHOR_POLICY_BOUNDARY_PASS",n,"transitions + noninterference")
'''
    # Preserve original module functions; only rewrite the module export declaration
    # to local same-environment aliases in an ephemeral VM harness.
    out.write_text(cs+"\n"+bs+"\n"+tests,encoding="utf-8")
    print("GQ_512_514_UNMODIFIED_AUTHOR_POLICIES_NATIVE_VM_EXTRACTED",len(out.read_bytes()))

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=("compose","verify","policy"))
    for v in ("combo","boss","out","receipt","project","place","compiler"):
        parser.add_argument("--"+v,type=Path)
    o=parser.parse_args()
    if o.mode=="compose":
        assert o.combo and o.boss and o.out and o.receipt
        compose(o.combo,o.boss,o.out,o.receipt)
    elif o.mode=="verify":
        assert o.project and o.place and o.receipt and o.compiler
        verify(o.project,o.place,o.receipt,o.compiler)
    else:
        assert o.combo and o.boss and o.out
        make_policy_vm(o.combo,o.boss,o.out)
if __name__=="__main__":main()
