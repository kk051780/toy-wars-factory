#!/usr/bin/env python3
"""Source-selective overlay on ORIGINAL #484 26-source composer; not an alternate engine."""
import argparse
import hashlib
import json
import os
from pathlib import Path

def hash_file(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def mapped(project):
    tree=json.loads(project.read_text(encoding="utf8"))["tree"]
    result={}
    def walk(node):
        for name,item in node.items():
            if name.startswith("$") or not isinstance(item,dict):continue
            if "$path" in item:
                assert set(item)=={"$path"},name
                assert name not in result,"duplicate script"
                result[name]=(project.parent/item["$path"]).resolve(strict=True)
            else:walk(item)
    walk(tree)
    return tree,result

def main():
    a=argparse.ArgumentParser()
    for name in ("base_project","base_receipt","original_combat","overlay_combat","policy","out"):
        a.add_argument("--"+name.replace("_","-"),required=True,type=Path)
    args=a.parse_args()
    base=args.base_project.resolve(strict=True)
    receipt=json.loads(args.base_receipt.read_text(encoding="utf8"))
    tree,old=mapped(base)
    assert len(old)==26 and len(receipt["source_sha256"])==26
    assert set(old)==set(receipt["source_sha256"])
    for key,p in old.items():
        assert hash_file(p)==receipt["source_sha256"][key],("baseline source mismatch",key)
    assert old["EGGRUMBLE_SevenRoleCombat"].read_bytes()==args.original_combat.read_bytes(),"author game changed"
    overlay=args.overlay_combat.resolve(strict=True)
    helper=args.policy.resolve(strict=True)
    script=overlay.read_text(encoding="utf8")
    assert script.count("StatusTickFence.canTick(")==1
    assert script.count('require(script.Parent:WaitForChild("EGGRUMBLE_StatusTickFence"))')==1
    assert "EGGRUMBLE_StatusTickFence" not in old
    out=args.out.resolve()
    assert out.parent.is_dir() and out!=base
    server=tree["ServerScriptService"]
    assert server.get("$className")=="ServerScriptService"
    server["EGGRUMBLE_SevenRoleCombat"]={"$path":os.path.relpath(overlay,out.parent).replace(os.sep,"/")}
    server["EGGRUMBLE_StatusTickFence"]={"$path":os.path.relpath(helper,out.parent).replace(os.sep,"/")}
    obj=json.loads(base.read_text(encoding="utf8"))
    obj["name"]="EGGRUMBLE_GQ_STATUS_FENCE_ORIG_ART_SCORE_CURRENT27_PRIVATE"
    obj["tree"]=tree
    out.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    _,new=mapped(out)
    assert len(new)==27 and set(new)==set(old)|{"EGGRUMBLE_StatusTickFence"}
    for key,p in old.items():
        if key!="EGGRUMBLE_SevenRoleCombat":
            assert new[key].read_bytes()==p.read_bytes(),("foreign owner source drift",key)
    assert new["EGGRUMBLE_SevenRoleCombat"]==overlay
    assert new["EGGRUMBLE_StatusTickFence"]==helper
    result={
       "status":"PRIVATE_CURRENT27_SOURCE_ONLY_NOT_OFFICIAL_RC",
       "scope":"GQ_V3_BURN_PREDATOR_TARGET_LIFETIME_FENCE",
       "baseline":"#484 original 26-source composer reused without source edits",
       "original_26_sha256":receipt["source_sha256"],
       "source_27_sha256":{name:hash_file(p) for name,p in sorted(new.items())},
       "preserved_25_of_original_26":True,
       "modified_existing_script":"EGGRUMBLE_SevenRoleCombat",
       "new_helper":"EGGRUMBLE_StatusTickFence",
       "script_count":27,"studio":"NOT_TESTED","android":"NOT_TESTED",
       "official_rc_integrated":False,"owner_accepted":False}
    (out.parent/"SOURCE_STATUS27_RECEIPT.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
    print("GQ_STATUS_26_TO_CURRENT27_SOURCE_EXACT_PASS")
if __name__=="__main__":main()
