#!/usr/bin/env python3
"""GQ470 FB015: strictly visual REAL69 siege gate phase meter.

A-only selected one-source PREP; never writes formal RC. This modifies the
existing server-owned display consumer, not any HP, authority or attack function.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
ROUTE="ServerScriptService/EGGRUMBLE_CastleSiegeBridge"
OLD_SHA="14f0f291ae9e8d14d525be0c1626e964aff52398b002c2ef1051c5bd1e4f72c5"
FEATURE="GQ470_FB015_CASTLE_GATE_HP_MATTE_REAL69_20261121"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
OFF="OFF69_GATEHP_MATTE"

def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def demand(ok: bool, code: str):
    if not ok:
        raise ValueError("RED_GQ470_GATEHP_" + code)

def selected(root: Path) -> dict[str, Path]:
    data=json.loads((root/PROJECT).read_text(encoding="utf-8"))
    paths={}
    def walk(node, route=""):
        if not isinstance(node, dict): return
        if "$path" in node:
            p=(root/node["$path"]).resolve()
            demand(p.is_relative_to(root.resolve()) and p.is_file(), "SELECTED_PATH")
            demand(route not in paths, "DUPLICATE_ROUTE")
            paths[route]=p
        for key, value in node.items():
            if not key.startswith("$"):
                walk(value, route+"/"+key if route else key)
    walk(data["tree"])
    return paths

def replace1(text: str, old: str, new: str, gate: str) -> str:
    demand(text.count(old)==1, "ANCHOR_"+gate)
    return text.replace(old,new,1)

def patch(source: str) -> str:
    demand(FEATURE not in source, "DUPLICATE_APPLY")
    start="local function render(session:any,target:string,s:any)\n"
    end="function M.attach(session:any,Rules:any):any\n"
    demand(source.count(start)==1 and source.count(end)==1, "RENDER_OWNER")
    a=source.index(start); b=source.index(end)
    demand(0<a<b, "RENDER_ORDER")
    prefix,render,suffix=source[:a],source[a:b],source[b:]
    for marker in ("Rules.damageCastle(", "Policy.gateHit(", "Policy.corePermit(",
                   "Policy.commitCorePermit(", "Policy.recordOriginalCastleHp(",
                   "GQ804_NOT_ACTIVE_ENEMY_OR_OWNER"):
        demand(marker in suffix, "GAMEPLAY_OWNER_"+marker)
    demand('gui.AlwaysOnTop=false;gui.MaxDistance=70' in render, "OCCLUSION_FENCE")
    demand('label.BackgroundTransparency=.25' in render, "MATTE_PANEL")
    demand('label.Font=Enum.Font.GothamBold;label.TextScaled=true' in render, "TEXT_POLICY")
    render=replace1(render,
       'gui.Size=UDim2.fromOffset(190,48);gui.StudsOffset=Vector3.new(0,7,0)',
       'gui.Size=UDim2.fromOffset(164,44);gui.StudsOffset=Vector3.new(0,6.7,0)',
       "COMPACT_SIZE")
    render=replace1(render,
       'gui.AlwaysOnTop=false;gui.MaxDistance=70;gui.Parent=door',
       'gui.AlwaysOnTop=false;gui.MaxDistance=56;gui.Parent=door',
       "MOBILE_OCCLUDED_DISTANCE")
    render=replace1(render,
       'label.Size=UDim2.fromScale(1,1);label.BackgroundTransparency=.25',
       'label.Size=UDim2.new(1,-12,0,26);label.Position=UDim2.fromOffset(6,3)\n'
       '  label.BackgroundTransparency=.25',
       "TEXT_PANEL")
    render=replace1(render,
       'label.Font=Enum.Font.GothamBold;label.TextScaled=true',
       'label.Font=Enum.Font.GothamBold;label.TextScaled=false\n'
       '  label.TextSize=14;label.TextTruncate=Enum.TextTruncate.AtEnd',
       "FIXED_TEXT")
    render=replace1(render,
       'label.TextColor3=Color3.fromRGB(245,234,205);label.Parent=gui',
       '''label.TextColor3=Color3.fromRGB(245,234,205);label.Parent=gui
  -- GQ470_FB015_CASTLE_GATE_HP_MATTE_REAL69_20261121
  -- Two UI frames only, allocated once per existing gate label; no 3D parts.
  local track=Instance.new("Frame");track.Name="GateHPTrack"
  track.Position=UDim2.fromOffset(8,33)
  track.Size=UDim2.new(1,-16,0,5)
  track.BorderSizePixel=0;track.BackgroundTransparency=.15
  track.BackgroundColor3=Color3.fromRGB(58,66,77);track.Parent=gui
  local fill=Instance.new("Frame");fill.Name="GateHPFill"
  fill.Size=UDim2.fromScale(1,1)
  fill.BorderSizePixel=0;fill.BackgroundColor3=Color3.fromRGB(132,168,178)
  fill.Parent=track''',
       "BOUNDED_BAR")
    render=replace1(render,
       ' door.Color=if s.stage=="GATE" then Color3.fromRGB(111,78,54)',
       ''' -- Bar derives only from existing server-owned siege state.
 local track=gui:FindFirstChild("GateHPTrack")
 local fill=track and track:FindFirstChild("GateHPFill")
 if fill and fill:IsA("Frame") then
  local maxHp=if s.stage=="GATE" then 180 else 1000
  local hp=if s.stage=="GATE" then s.gateHP
   elseif s.stage=="FALLEN" then 0 else s.castleHP
  local ratio=if type(hp)=="number" and hp==hp then
   math.clamp(hp/maxHp,0,1) else 0
  fill.Size=UDim2.fromScale(ratio,1)
  fill.BackgroundColor3=if s.stage=="FALLEN" then Color3.fromRGB(91,94,99)
   elseif s.stage=="FINAL" then Color3.fromRGB(192,105,80)
   elseif s.stage=="INNER" then Color3.fromRGB(178,145,83)
   else Color3.fromRGB(142,175,191)
 end
 door.Color=if s.stage=="GATE" then Color3.fromRGB(111,78,54)''',
       "READABLE_PHASE_METER")
    out=prefix+render+suffix
    demand(out[out.index(end):]==suffix, "GAMEPLAY_SUFFIX_NOT_EXACT")
    demand(out[:out.index(start)]==prefix, "GAMEPLAY_PREFIX_NOT_EXACT")
    demand(out.count("Instance.new(\"BillboardGui\")")==source.count("Instance.new(\"BillboardGui\")"),"NO_EXTRA_BILLBOARDS")
    demand(out.count('Instance.new("Frame")')==source.count('Instance.new("Frame")')+2,"UI_FRAME_BUDGET")
    for token in ("RemoteEvent", "DataStoreService", "TakeDamage", "FireServer", "InvokeServer"):
        demand(render.count(token)==0, "AUTHORITY_"+token)
    return out

def source_negatives(source: str) -> int:
    altered=patch(source)
    mutants=[
       altered,
       source.replace('gui.Size=UDim2.fromOffset(190,48)','gui.Size=UDim2.fromOffset(900,500)',1),
       source.replace('gui.AlwaysOnTop=false;gui.MaxDistance=70','gui.AlwaysOnTop=true;gui.MaxDistance=70',1),
       source.replace('label.Font=Enum.Font.GothamBold;label.TextScaled=true',
                      'label.Font=Enum.Font.GothamBold;label.TextScaled=false',1),
       source.replace('label.TextColor3=Color3.fromRGB(245,234,205);label.Parent=gui',
                      'label.TextColor3=Color3.fromRGB(245,234,205);label.Parent=nil',1),
       source.replace('local function render(session:any,target:string,s:any)','local function bogusRender(',1),
       source.replace('Policy.commitCorePermit(', 'Policy.commitWithoutPermit(',1),
       source.replace('Rules.damageCastle(', 'Rules.fakeDamage(',1),
       source.replace('gui.AlwaysOnTop=false;gui.MaxDistance=70;gui.Parent=door',
                      'gui.AlwaysOnTop=false;gui.MaxDistance=71;gui.Parent=door',1),
    ]
    for i,mutant in enumerate(mutants):
        demand(mutant!=source,"MUTANT_NOT_CHANGED_"+str(i))
        try: patch(mutant)
        except ValueError: continue
        raise AssertionError("RED_MUTANT_ACCEPTED_"+str(i))
    return len(mutants)

def apply(root: Path):
    paths=selected(root)
    receipt=json.loads((root/RECEIPT).read_text(encoding="utf-8"))
    demand(receipt.get("build_head")==BASE and receipt.get("official_branch")==
           "rc/p0d-s1-kids-rc01" and receipt.get("canonical_build") is True,
           "CANONICAL_HEAD")
    demand(receipt.get("selected_source_count")==len(paths)==69,"REAL69_COUNT")
    demand(set(paths)==set(receipt["source_hashes"])==set(receipt["source_classes"]),
           "RECEIPT_ROUTES")
    demand(receipt["source_classes"].get(ROUTE)=="ModuleScript", "SOURCE_CLASS")
    demand(receipt["source_hashes"].get(ROUTE)==OLD_SHA,"SOURCE_LOCK")
    for route,path in paths.items():
        demand(sha(path.read_bytes())==receipt["source_hashes"][route],"SOURCE_HASH_"+route)
    original=paths[ROUTE].read_bytes()
    demand(sha(original)==OLD_SHA,"ACTUAL_SOURCE_LOCK")
    source=original.decode("utf-8")
    count=source_negatives(source)
    candidate=patch(source).encode("utf-8")
    off=root/OFF
    demand(not off.exists(),"ALREADY_PATCHED")
    off.mkdir()
    shutil.copytree(root/"sources",off/"sources")
    for name in (PROJECT,RECEIPT,"EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copyfile(root/name,off/name)
    paths[ROUTE].write_bytes(candidate)
    demand({k for k,p in paths.items() if p.read_bytes()!=selected(off)[k].read_bytes()}=={ROUTE},
           "OTHER68_CHANGED")
    demand((root/PROJECT).read_bytes()==(off/PROJECT).read_bytes(),
           "ROJO_PROJECT_DRIFT")
    receipt["source_hashes"][ROUTE]=sha(candidate)
    receipt["gq470_castle_gatehp_matte"]={
        "feature_id":FEATURE,"selected_source":ROUTE,
        "original_sha256":OLD_SHA,"candidate_sha256":sha(candidate),
        "selected_source_changed":1,"other_selected_sources_byte_exact":68,
        "gate_billboard_old_new":[190,48,164,44],
        "max_view_distance_old_new":[70,56],
        "new_ui_frames_per_existing_gate":2,
        "new_world_parts":0,"authority_changed":False,"gameplay_suffix_byte_exact":True,
        "negative_mutations_rejected":count,"rollback":OFF,
        "studio_engine":"NOT_TESTED","android15":"NOT_TESTED",
        "art_owner":"NOT_TESTED","publish_authorized":False,
        "official_adoption":False}
    (root/RECEIPT).write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n",
                                  encoding="utf-8")
    print("GQ470_GATEHP_REAL69_SOURCE_PATCH_PASS",sha(candidate),"NEGATIVES",count)

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--self-test",action="store_true")
    args=p.parse_args()
    if args.self_test:
        data=json.loads((args.base/RECEIPT).read_text())
        original=selected(args.base)[ROUTE].read_bytes()
        demand(data.get("build_head")==BASE and sha(original)==OLD_SHA,"SELFTEST_SOURCE_LOCK")
        print("GQ470_GATEHP_NEGATIVES_PASS",source_negatives(original.decode("utf-8")))
    else: apply(args.base)
