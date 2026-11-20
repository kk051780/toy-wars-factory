#!/usr/bin/env python3
"""REAL69 visual motion source-select: real one-route A PREP, never formal RC."""
from __future__ import annotations
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

DIR=Path(__file__).resolve().parent
PATCH=DIR/"ROLE_MOTION_REAL69.patch"
ROUTE="StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills"
REL="sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_ProceduralSkills.client.luau"
PROJECT="EGGRUMBLE_REAL69.project.json"
BASE="95e5dba544a759547ea41e8ecec1984317fc61b35281f4533b2323df1951491f"
NEW="1856594a79d2e7ab7d4f6ac386c9379a45a8647a4168f65354246e888428bffb"
RC="e80973c354f14a0d0088577f3cc1a875454f0f8f"
FEATURE="GQ470_FB015_ROLE_MOTION_READABLE_REAL69_20261121"

def sha(data): return hashlib.sha256(data).hexdigest()
def check(test,name):
    if not test: raise AssertionError("ROLE_MOTION_RED_"+name)

def selected(root):
    tree=json.loads((root/PROJECT).read_text())["tree"]; found={}
    def walk(node,parents):
        for name,item in node.items():
            if name.startswith("$") or not isinstance(item,dict): continue
            key="/".join(parents+[name])
            if "$path" in item: found[key]=root/item["$path"]
            else: walk(item,parents+[name])
    walk(tree,[])
    check(len(found)==69 and found.get(ROUTE)==root/REL,"SELECTED_69_ROUTE")
    check(all(p.is_file() for p in found.values()),"ALL69_EXIST")
    return found

def validate(source):
    check(source.startswith("--!strict\n"),"LUAU_STRICT")
    check("if not RunService:IsStudio() then return end" in source,"STUDIO_ONLY")
    check("EGGRUMBLE_SkillCastSignature" in source,"SERVER_CAST")
    check("local MAX_ANIMATED_AVATARS=16" in source and "local MAX_VIEW_DISTANCE=130" in source,"MOBILE_BOUNDS")
    check("local DURATION={A=.26,B=.48,C=.82}" in source,"SERVER_PACING")
    check(source.count("RunService.PreSimulation:Connect(")==1 and "RenderStepped:Connect(" not in source,"ONE_LOOP")
    check("local pulse,snap=motionProfile(t,slot)" in source and "local function smoothstep(t:number)" in source,"TIMING")
    check('local strikeEnd=(slot=="A") and .36 or .42' in source,"A_STRIKE_PHASE")
    check('local holdEnd=(slot=="A") and .62 or .54' in source,"A_25FPS_HOLD")
    check("characterListener:Disconnect()" in source,"LISTENER_CLEANUP")
    check("resetPose(record)\n   active[uid]=nil\n  end" in source,"OFFSCREEN_UNPOSE")
    for job in ("WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE"):
        check('role=="'+job+'"' in source,"JOB_"+job)
    for denied in ("Instance.new(",":FireServer(",":TakeDamage(","DataStoreService","task.spawn(","task.wait("):
        check(denied not in source,"NO_AUTHORITY_"+denied)

def test_mutations(source):
    for token in ("characterListener:Disconnect()","local pulse,snap=motionProfile(t,slot)",
                  "if not RunService:IsStudio() then return end","RunService.PreSimulation:Connect("):
        check(token in source,"NEGATIVE_PRECONDITION")
        try: validate(source.replace(token,"",1))
        except AssertionError: continue
        raise AssertionError("ROLE_MOTION_MUTANT_NOT_REJECTED_"+token)

def compose(base,out):
    check(not out.exists(),"NO_OVERWRITE")
    old=selected(base)
    receipt=json.loads((base/"REAL69_LEGACY_INTAKE_RECEIPT.json").read_text())
    check(receipt["selected_source_count"]==69 and len(receipt["source_hashes"])==69,"RECEIPT")
    check(receipt["source_hashes"][ROUTE]==BASE,"REAL69_ORIGINAL_IDENTITY")
    for route,path in old.items():
        check(sha(path.read_bytes())==receipt["source_hashes"][route],"BASE_HASH_"+route)
    shutil.copytree(base,out)
    off=out/"OFF69_SOURCE_EXACT";off.mkdir()
    shutil.copytree(base/"sources",off/"sources")
    shutil.copy2(base/PROJECT,off/PROJECT)
    subprocess.run(["patch","-p1","--batch","--fuzz=0","-i",str(PATCH)],
                   cwd=out,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    on=selected(out);rolled=selected(off)
    check({k for k in old if on[k].read_bytes()!=rolled[k].read_bytes()}=={ROUTE},"ONLY_ONE_SELECTED")
    for k in old:
        check(old[k].read_bytes()==rolled[k].read_bytes(),"OFF69_EXACT_"+k)
        if k!=ROUTE: check(old[k].read_bytes()==on[k].read_bytes(),"68_UNCHANGED_"+k)
    code=on[ROUTE].read_text()
    check(sha(code.encode())==NEW,"NEW_SOURCE_SHA")
    validate(code);test_mutations(code)
    report={"schema":FEATURE,"official_head":RC,"official_source_artifact_id":14610422120,
      "original_source_route":ROUTE,"class":"LocalScript","base_sha256":BASE,
      "candidate_sha256":NEW,"on_sources":69,"off_sources":69,"unchanged":68,
      "changed_routes":[ROUTE],"negative_tests":4,"added_parts":0,
      "added_remotes":0,"added_render_loops":0,"native_luau":"PENDING_CI",
      "rojo_on_off":"PENDING_CI","studio":"NOT_TESTED","android15":"NOT_TESTED",
      "human_before_after_screenshots":"0/32","art_gate":"NO_GO",
      "fun_gate":"NO_GO","owner_accepted":False,"formal_rc_adopted":False}
    # Candidate receipt mirrors only the one changed real selected source.
    # Immutable base receipt lives in OFF69_SOURCE_EXACT for bytewise rollback.
    shutil.copy2(base/"REAL69_LEGACY_INTAKE_RECEIPT.json",off/"REAL69_LEGACY_INTAKE_RECEIPT.json")
    receipt["source_hashes"][ROUTE]=NEW
    receipt["gq470_role_motion"]={"feature":FEATURE,"original_sha256":BASE,"candidate_sha256":NEW,
      "official_base":RC,"changed_one":ROUTE,"original_68_unchanged":True,
      "gameplay_authority_modified":False,"studio":"NOT_TESTED","art_go":False}
    (out/"REAL69_LEGACY_INTAKE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n")
    (out/"ART_CHECK_REPORT_ROLE_MOTION.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    handoff=out/"B220_ONE_SOURCE_NOT_FORMAL"
    (handoff/"selected_sources").mkdir(parents=True)
    shutil.copy2(on[ROUTE],handoff/"selected_sources/EGGRUMBLE_ProceduralSkills.client.luau")
    (handoff/"SOURCE_SELECT_MANIFEST.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
    print("GQ470_ROLE_MOTION_REAL69_ONE_SOURCE_68_UNCHANGED_OFF69_NEG4_PASS_NOT_STUDIO")
    return report

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    a=p.parse_args();compose(a.base.resolve(),a.out.resolve())
if __name__=="__main__":main()
