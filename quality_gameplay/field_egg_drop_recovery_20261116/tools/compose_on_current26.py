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

def compose(base26:Path,out:Path,expect_count:int=26):
    base26=base26.resolve(strict=True)
    out=out.resolve()
    assert out!=base26 and out!=base26.parent, "must use separate new output folder"
    project=json.loads(base26.read_text(encoding="utf-8"))
    tree=project["tree"]
    server=tree["ServerScriptService"]
    original=dict(iter_paths(tree,base26.parent))
    assert expect_count in (26,28)
    assert len(original)==expect_count and len(server)-1==expect_count-3
    assert HOST in original and "EGGRUMBLE_FieldEggDropBounds" not in original
    assert original[HOST].name=="EGGRUMBLE_LobbyCastleModesPreview.server.luau"
    before={n:h(p) for n,p in original.items()}
    text=original[HOST].read_text(encoding="utf-8")
    assert text.count(REQUIRE)==1 and text.count(ORIGINAL)==1, "review original #484 host layout"
    assert text.count("CastleAccessRamp")>0, "must preserve original #484 castle ramp"
    assert "EGGRUMBLE_BotActors" in original and "EGGRUMBLE_FlagshipFieldArt" in original
    assert "EGGRUMBLE_ScoreBalance" in original and "EGGRUMBLE_ArtDistanceLOD" in original
    if expect_count==28:
        # Federated 28 belongs to ORIGINAL #509 egg terminal fence, #489 ITEM,
        #494/#501 neutral policies. Reject a misidentified generic 28 project.
        for required in ("EGGRUMBLE_NeutralEncounterFairness","EGGRUMBLE_NeutralSpawnPacing"):
            assert required in original, ("missing owner policy",required)
        assert 'if m.phase~="ACTIVE" or m.winner~=nil then return 0,{} end' in original["EGGRUMBLE_CastleMatchRules"].read_text(), "NOT the authenticated #509 late-death original author Rules"
    updated=text.replace(REQUIRE,REQUIRE+INSERT,1).replace(ORIGINAL,REPLACEMENT,1)
    assert updated!=text
    out.mkdir(parents=True,exist_ok=True)
    # #484 paths are relative to its own 26-project. The moved 27-project
    # MUST retain the exact same physical source bytes when rooted in out.
    def rebase(node):
        for name,child in node.items():
            if name.startswith("$"): continue
            if "$path" in child:
                source=(base26.parent/child["$path"]).resolve(strict=True)
                child["$path"]=os.path.relpath(source,out).replace(os.sep,"/")
            else:
                rebase(child)
    rebase(tree)
    host_path=out/(HOST+".server.luau")
    host_path.write_text(updated,encoding="utf-8")
    server[HOST]={"$path":os.path.relpath(host_path,out).replace(os.sep,"/")}
    server["EGGRUMBLE_FieldEggDropBounds"]={"$path":os.path.relpath(POLICY,out).replace(os.sep,"/")}
    project["name"]=f"EGGRUMBLE_GQ_FIELD_EGG_RECOVERY_FEDERATED{expect_count+1}_PRIVATE_SOURCE_NO_RC"
    dest=out/f"EGGRUMBLE_GQ_FIELD_EGG_SAFE{expect_count+1}.project.json"
    dest.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    after=dict(iter_paths(project["tree"],out))
    assert len(after)==expect_count+1 and len(set(after))==expect_count+1
    assert set(after)==set(original)|{"EGGRUMBLE_FieldEggDropBounds"}
    for name,source in original.items():
        assert h(source)==before[name],f"mutated original composer output: {name}"
        if name!=HOST:
            assert after[name]==source and h(after[name])==before[name],f"original drift: {name}"
    assert after[HOST]==host_path and after["EGGRUMBLE_FieldEggDropBounds"]==POLICY
    receipt={
        "status":f"PRIVATE{expect_count+1}_SOURCE_ONLY_NOT_OFFICIAL_RC",
        "original_count":expect_count,"candidate_count":expect_count+1,
        "base_26_project":str(base26),"original_sha256":before,
        "candidate_sha256":{name:h(path) for name,path in sorted(after.items())},
        "preserved_base_sources":expect_count-1,"host_overlay_only":HOST,
        "new_policy_only":"EGGRUMBLE_FieldEggDropBounds",
        "studio":"NOT_RUN","android":"NOT_RUN","owner_accepted":False}
    (out/f"SOURCE{expect_count+1}_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(f"GQ_FIELD_EGG_ORIGINAL{expect_count}_TO_PRIVATE{expect_count+1}_PASS kept={expect_count-1}/{expect_count} one-host-overlay one-pure-policy")
    return dest

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--base26",type=Path,required=True)
    ap.add_argument("--out",type=Path,required=True)
    ap.add_argument("--expect-count",type=int,choices=(26,28),default=26)
    args=ap.parse_args()
    compose(args.base26,args.out,args.expect_count)
