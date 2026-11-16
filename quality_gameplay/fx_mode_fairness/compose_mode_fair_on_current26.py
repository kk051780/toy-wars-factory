#!/usr/bin/env python3
"""Source-selective 26->27 current V3 extension. REUSES #484 composer output.

No source generation, mutation, duplicate Game/ART/SCORE or active RC change.
"""
import argparse, hashlib, json, os, re
from pathlib import Path

def mapped(project):
    base=project.parent
    tree=json.loads(project.read_text(encoding="utf8"))["tree"]
    result={}
    def walk(obj):
        for key,value in obj.items():
            if key.startswith("$") or not isinstance(value,dict):continue
            if "$path" in value:
                if key in result:raise AssertionError("duplicate script name: "+key)
                assert set(value)=={"$path"},key
                result[key]=(base/value["$path"]).resolve(strict=True)
            else:walk(value)
    walk(tree)
    return tree,result

def sha(f):
    return hashlib.sha256(f.read_bytes()).hexdigest()

def main():
    a=argparse.ArgumentParser()
    for key in ("base_project","base_receipt","original_skillfx","overlay_skillfx","policy","out"):
        a.add_argument("--"+key.replace("_","-"),type=Path,required=True)
    args=a.parse_args()
    proj=args.base_project.resolve(strict=True)
    prev_receipt=json.loads(args.base_receipt.read_text(encoding="utf8"))
    tree, before=mapped(proj)
    assert len(before)==26 and len(prev_receipt["source_sha256"])==26
    assert set(before)==set(prev_receipt["source_sha256"])
    assert before["EGGRUMBLE_SkillFX"].read_bytes()==args.original_skillfx.read_bytes(),"author SkillFX drift"
    for k,source in before.items():
        assert sha(source)==prev_receipt["source_sha256"][k],("stale base26",k)
    assert "EGGRUMBLE_FXModeFairQuota" not in before
    assert len([k for k in before if k.endswith("LobbyCastleModesPreview")])==1
    assert "EGGRUMBLE_ArtDistanceLOD" in before and "EGGRUMBLE_ScoreBalance" in before
    overlay=args.overlay_skillfx.resolve(strict=True)
    policy=args.policy.resolve(strict=True)
    s=overlay.read_text(encoding="utf8")
    assert s.count("fairQuota:acquire(parent.Name)")==1
    assert s.count("fairQuota:release(lease)")==1
    assert s.count("fairQuota:canStart(parent.Name,MAX_NEW_PER_PULSE)")==1
    assert 'script.Parent:WaitForChild("EGGRUMBLE_FXModeFairQuota")' in s
    out=args.out.resolve()
    assert out.parent.is_dir() and out!=proj
    ss=tree["ServerScriptService"]
    assert "EGGRUMBLE_FXModeFairQuota" not in ss
    ss["EGGRUMBLE_SkillFX"]={"$path":os.path.relpath(overlay,out.parent).replace(os.sep,"/")}
    ss["EGGRUMBLE_FXModeFairQuota"]={"$path":os.path.relpath(policy,out.parent).replace(os.sep,"/")}
    assert len(ss)-1==24,("server drift",len(ss))
    assert len(tree["StarterPlayer"]["StarterPlayerScripts"])-1==3
    tree["$className"]="DataModel"
    data=json.loads(proj.read_text(encoding="utf8"))
    data["name"]="EGGRUMBLE_GQ_MODE_FAIR_AUTHOR_ART_SCORE_CURRENT27_PRIVATE"
    data["tree"]=tree
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    afterTree, after=mapped(out)
    assert len(after)==27
    assert set(after)==set(before)|{"EGGRUMBLE_FXModeFairQuota"}
    for name,p in before.items():
        if name!="EGGRUMBLE_SkillFX":assert after[name].read_bytes()==p.read_bytes(),("other-owner mutated",name)
    assert after["EGGRUMBLE_SkillFX"]==overlay and after["EGGRUMBLE_FXModeFairQuota"]==policy
    manifest={k:sha(v) for k,v in sorted(after.items())}
    receipt={"status":"PRIVATE_27_SOURCE_EXACT_ONLY_NO_OFFICIAL_RC",
      "composer":"#484 ORIGINAL COMPOSER REUSED UNMODIFIED",
      "original_26_sha256":prev_receipt["source_sha256"],
      "source_27_sha256":manifest,
      "unique_overlay":"EGGRUMBLE_SkillFX","new_helper":"EGGRUMBLE_FXModeFairQuota",
      "kept_25_of_26_source_bytes_exact":True,
      "private_source_total":27,"server_modules":24,"client_scripts":3,
      "studio":"NOT_TESTED","android":"NOT_TESTED","owner_accepted":False,
      "official_rc_adopted":False}
    (out.parent/"SOURCE_FAIR_27_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("GQ_FX_MODE_ORIGINAL_COMPOSER_26_TO_27_SOURCE_EXACT_PASS")
if __name__=="__main__":main()
