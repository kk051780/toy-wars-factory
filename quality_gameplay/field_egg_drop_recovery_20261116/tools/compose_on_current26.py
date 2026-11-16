#!/usr/bin/env python3
"""Append ONE field/egg recovery policy onto original #484 26-source composite.
Preserves original composer, bot AI, 7 roles, ART and SCORE by SHA. PRIVATE only.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
POLICY=ROOT/"EGGRUMBLE_FieldEggDropBounds.luau"
HOST="EGGRUMBLE_LobbyCastleModesPreview"
REQUIRE='local Rules=require(script.Parent:WaitForChild("EGGRUMBLE_CastleMatchRules"))\n'
ORIGINAL='local landing=Vector3.new(at.X,session.groundY or at.Y,at.Z+17)'
INSERT='local DropBounds=require(script.Parent:WaitForChild("EGGRUMBLE_FieldEggDropBounds"))\n'
REPLACEMENT='''local home=session.castleLocations[ownerId]
   local safe=DropBounds.recover(mode,root.X,root.Z,at.X,at.Z,
    home and home.X or nil,home and home.Z or nil)
   local landing=Vector3.new(safe.x,session.groundY or at.Y,safe.z+17)'''

def h(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def iter_paths(tree,folder):
    for name,child in tree.items():
        if name.startswith("$"):continue
        if "$path" in child:
            yield name,(folder/child["$path"]).resolve(strict=True)
        else:
            yield from iter_paths(child,folder)

def compose(base26:Path,out:Path):
    base26=base26.resolve(strict=True)
    out=out.resolve()
    assert out!=base26 and out.parent!=base26.parent, "must use separate new output folder"
    project=json.loads(base26.read_text(encoding="utf-8"))
    tree=project["tree"]
    server=tree["ServerScriptService"]
    original=dict(iter_paths(tree,base26.parent))
    assert len(original)==26 and len(server)-1==23
    assert HOST in original and "EGGRUMBLE_FieldEggDropBounds" not in original
    assert original[HOST].name=="EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    before={n:h(p) for n,p in original.items()}
    text=original[HOST].read_text(encoding="utf-8")
    assert text.count(REQUIRE)==1 and text.count(ORIGINAL)==1, "review original #484 host layout"
    assert text.count("CastleAccessRamp")>0, "must preserve original #484 castle ramp"
    assert "EGGRUMBLE_BotActors" in original and "EGGRUMBLE_FlagshipFieldArt" in original
    assert "EGGRUMBLE_ScoreBalance" in original and "EGGRUMBLE_ArtDistanceLOD" in original
    updated=text.replace(REQUIRE,REQUIRE+INSERT,1).replace(ORIGINAL,REPLACEMENT,1)
    assert updated!=text
    out.mkdir(parents=True,exist_ok=True)
    host_path=out/(HOST+".server.luau")
    host_path.write_text(updated,encoding="utf-8")
    server[HOST]={"$path":os.path.relpath(host_path,out).replace(os.sep,"/")}
    server["EGGRUMBLE_FieldEggDropBounds"]={"$path":os.path.relpath(POLICY,out).replace(os.sep,"/")}
    project["name"]="EGGRUMBLE_GQ_FIELD_EGG_RECOVERY_AUTHOR27_PRIVATE_SOURCE_NO_RC"
    dest=out/"EGGRUMBLE_GQ_FIELD_EGG_SAFE27.project.json"
    dest.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    after=dict(iter_paths(project["tree"],out))
    assert len(after)==27 and len(set(after))==27
    assert set(after)==set(original)|{"EGGRUMBLE_FieldEggDropBounds"}
    for name,source in original.items():
        assert h(source)==before[name],f"mutated original composer output: {name}"
        if name!=HOST:
            assert after[name]==source and h(after[name])==before[name],f"original drift: {name}"
    assert after[HOST]==host_path and after["EGGRUMBLE_FieldEggDropBounds"]==POLICY
    receipt={
        "status":"PRIVATE27_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "original_count":26,"candidate_count":27,
        "base_26_project":str(base26),"original_sha256":before,
        "candidate_sha256":{name:h(path) for name,path in sorted(after.items())},
        "preserved_original_26":25,"host_overlay_only":HOST,
        "new_policy_only":"EGGRUMBLE_FieldEggDropBounds",
        "studio":"NOT_RUN","android":"NOT_RUN","owner_accepted":False}
    (out/"SOURCE27_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print("GQ_FIELD_EGG_ORIGINAL26_TO_PRIVATE27_PASS kept=25/26 one-host-overlay one-pure-policy")
    return dest

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base26",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    args=ap.parse_args()
    compose(args.base26,args.out)
