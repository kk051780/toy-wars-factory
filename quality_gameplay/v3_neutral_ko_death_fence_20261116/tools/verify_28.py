#!/usr/bin/env python3
"""Independent exact-source / class verification of the private 28-script XML Place."""
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from pathlib import Path

def flatten(tree):
    out={}
    def visit(node,key=()):
        for name,child in node.items():
            if name.startswith("$"):continue
            if "$path" in child:
                assert name not in out,("duplicate source name",name)
                out[name] = (key+(name,),child["$path"])
            else:visit(child,key+(name,))
    visit(tree)
    return out

def instances(root):
    found={}
    for node in root.iter("Item"):
        name=node.findtext("Properties/string[@name='Name']")
        if name is None: name=node.findtext("Properties/ProtectedString[@name='Name']")
        if name is None:continue
        src=node.findtext("Properties/ProtectedString[@name='Source']")
        if src is None:src=node.findtext("Properties/string[@name='Source']")
        if src is None:continue
        assert name not in found,("duplicate script instance",name)
        found[name]=(node.get("class"),src.replace("\r\n","\n"))
    return found

def main(project_path,place_path):
    project_path=project_path.resolve(strict=True)
    place_path=place_path.resolve(strict=True)
    project=json.loads(project_path.read_text(encoding="utf-8"))
    mapped=flatten(project["tree"])
    assert len(mapped)==28,len(mapped)
    place=instances(ET.parse(place_path).getroot())
    assert set(mapped)==set(place),(sorted(set(mapped)-set(place)),sorted(set(place)-set(mapped)))
    sha256={}
    count={"ModuleScript":0,"Script":0,"LocalScript":0}
    for name,(key,relative) in mapped.items():
        data=(project_path.parent/relative).resolve(strict=True).read_text(encoding="utf-8").replace("\r\n","\n")
        actual_class,actual=place[name]
        expect_class="LocalScript" if key[0]=="StarterPlayer" else ("Script" if name.endswith("Preview") else "ModuleScript")
        assert actual_class==expect_class,(name,actual_class,expect_class)
        assert data==actual,("byte-different Luau Source",name)
        sha256[name]=hashlib.sha256(data.encode("utf-8")).hexdigest()
        count[expect_class]+=1
    assert count["ModuleScript"]>=20
    receipt=json.loads((project_path.parent/"SOURCE28_RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["original_27_mapped"]==27 and receipt["unchanged_26_sources"]==26
    assert sha256["EGGRUMBLE_NeutralKoDeathFence"]==receipt["fence_sha256"]
    assert sha256["EGGRUMBLE_SwarmCombat"]==receipt["combined_swarm_sha256"]
    place_hash=hashlib.sha256(place_path.read_bytes()).hexdigest()
    out={"private_source_exact":True,"mapped_count":28,"embedded_count":len(place),
         "class_counts":count,"place_bytes":place_path.stat().st_size,
         "place_sha256":place_hash,"official_rc_adopted":False,
         "source_sha256":sha256}
    (project_path.parent/"PLACE28_RECEIPT.json").write_text(json.dumps(out,indent=2)+"\n")
    print("NEUTRAL_GQ494_PLUS_508_NATIVE_ROJO28_EXACT_PASS",len(mapped),place_path.stat().st_size,place_hash)
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--project",type=Path,required=True)
    p.add_argument("--place",type=Path,required=True)
    a=p.parse_args()
    main(a.project,a.place)
