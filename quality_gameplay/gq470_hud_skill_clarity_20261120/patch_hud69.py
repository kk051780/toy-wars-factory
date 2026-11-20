#!/usr/bin/env python3
"""FB-004/015: remove internal skill IDs from the existing REAL69 HUD drawer.

No Tool names are changed; the server's skill lookup, damage authority and
inventory remain exactly as before. This is a candidate until #220 adoption.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
                       "gq8_rc85_rc86_real68_nonloss_20261120"))
from verify_nonloss import project_scan

PARENT = "6c2338b44db1c772bab0d688b2aece2e3aa8aae2"
ROUTE = "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
MARK = "GQ470_FB004_SKILL_PUBLIC_LABEL_HUD_REAL69_20261120"
PRIOR = "GQ8_RC85_RC86_FB019_LOCAL_ATTACK_SWING_REAL69_20261120"
HOOK = "local function openDrawer(which)"
OLD = 'if t then table.insert(options,{id=slot,name=slot.." "..t.Name:sub(19),tool=t}) end'
NEW = 'if t then table.insert(options,{id=slot,name=publicSkillLabel(t,slot),tool=t}) end'
LABEL = '''-- GQ470_FB004_SKILL_PUBLIC_LABEL_HUD_REAL69_20261120
-- Presentation only: never alter Tool.Name. Server-owned Tool IDs remain stable.
local function publicSkillLabel(tool:Tool,slot:string):string
 local prefix="技"..slot.." "
 for _,key in ipairs({"SkillDisplayName","DisplayName","EGGRUMBLE_DisplayName"}) do
  local labelText=tool:GetAttribute(key)
  if typeof(labelText)=="string" and #labelText>0 and #labelText<=48
    and not string.find(labelText,"EGGRUMBLE_",1,true)
    and not string.find(labelText,"SKILL_",1,true) then
   return prefix..labelText
  end
 end
 local tooltip=tool.ToolTip
 if tooltip and tooltip~="" and #tooltip<=48
   and not string.find(tooltip,"EGGRUMBLE_",1,true)
   and not string.find(tooltip,"SKILL_",1,true) then
  return prefix..tooltip
 end
 return prefix.."能力"
end

'''

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def need(ok: bool, code: str) -> None:
    if not ok:
        raise ValueError("RED_GQ470_HUD_LABEL_" + code)

def patch(source: str) -> str:
    need(source.count(PRIOR)==1, "FB019_PARENT_MISSING")
    need(MARK not in source, "DUPLICATE")
    need(source.count(HOOK)==1 and source.count(OLD)==1,
         "EXACT_SINGLE_SKILL_DRAWER")
    need(source.count('local function slotTool(slot)')==1,
         "SERVER_TOOL_LOOKUP_DRIFT")
    need(source.count('actions.ATTACK.Activated:Connect(function()')==1,
         "PREEXISTING_ATTACK_BIND_DRIFT")
    out=source.replace(HOOK,LABEL+HOOK).replace(OLD,NEW)
    need(out.count(MARK)==1 and out.count(NEW)==1 and OLD not in out,
         "PATCH_UNIQUE")
    need("tool.Name=" not in LABEL and "FireServer(" not in LABEL
         and "SetCoreGuiEnabled(" not in LABEL, "NO_TOOL_OR_AUTHORITY_CHANGE")
    return out

def selftest() -> None:
    baseline=("-- "+PRIOR+"\n"+HOOK+"\n"
              "local function slotTool(slot)\n"
              "actions.ATTACK.Activated:Connect(function()\n"
              +OLD+"\n")
    good=patch(baseline)
    need("return prefix..tooltip" in good and "publicSkillLabel(t,slot)" in good,
         "POSITIVE")
    for altered in (baseline.replace(PRIOR,"WRONG"),
                    baseline.replace(OLD,""),
                    baseline.replace("slotTool(slot)","slotTool(other)"),
                    good):
        try:
            patch(altered)
        except ValueError:
            pass
        else:
            raise AssertionError("MUTANT_ACCEPTED")
    print("GQ470_HUD_LABEL_SOURCE_4_MUTANTS_PASS")

def apply(root: Path) -> None:
    before=project_scan(root,PROJECT)
    need(len(before)==69 and ROUTE in before,"REAL69_SOURCE_COUNT")
    need(before[ROUTE]["class"]=="LocalScript","EXISTING_CLIENT_OWNER")
    receiptpath=root/RECEIPT
    receipt=json.loads(receiptpath.read_text(encoding="utf-8"))
    need(receipt.get("build_head")==PARENT
         and receipt.get("selected_source_count")==69
         and len(receipt.get("source_hashes",{}))==69,
         "CURRENT_EXACT_OFFICIAL_PARENT")
    need(all(receipt["source_hashes"].get(route)==meta["sha256"]
             for route,meta in before.items()),"RECEIPT_69_HASHES")
    need("gq470_p0_combat_neutral_visibility" in receipt,"P0_915_REQUIRED")
    target=root/before[ROUTE]["path"]
    old=target.read_bytes()
    new=patch(old.decode("utf-8")).encode("utf-8")
    off=root/"off69_hud_label"
    need(not off.exists(),"OFF_COLLISION")
    shutil.copytree(root/"sources",off/"sources")
    for name in (PROJECT,RECEIPT,"EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copy2(root/name,off/name)
    target.write_bytes(new)
    after=project_scan(root,PROJECT)
    need(len(after)==69 and set(before)==set(after),"ROUTES_PRESERVED")
    need({route for route in before if before[route]["sha256"]!=after[route]["sha256"]}
         =={ROUTE},"ONLY_HUD_ROUTE_CHANGED")
    need(all(before[route]["class"]==after[route]["class"]
             and before[route]["path"]==after[route]["path"]
             for route in before),"PATH_CLASS_PRESERVED")
    need((off/before[ROUTE]["path"]).read_bytes()==old,"INVERSE_EXACT")
    receipt["source_hashes"][ROUTE]=sha(new)
    receipt["build_head"]="PREP_HUD_LABEL_FROM_"+PARENT
    receipt["gq470_fb004_hud_skill_label"]={
        "feature_id":MARK,
        "formal_parent":PARENT,
        "modified_existing_route":ROUTE,
        "old_sha256":sha(old),
        "new_sha256":sha(new),
        "other_68_scripts_byte_exact":True,
        "tool_names_changed":False,
        "gameplay_server_authority_changed":False,
        "default_roblox_backpack_label_fixed":False,
        "scope":"Only the custom SKILL drawer human-readable labels",
        "rollback":"off69_hud_label",
        "studio":"NOT_TESTED",
        "android":"NOT_TESTED",
        "owner_accepted":False
    }
    receiptpath.write_text(json.dumps(receipt,ensure_ascii=False,
                                      sort_keys=True,indent=2)+"\n",
                           encoding="utf-8")
    print("GQ470_HUD_CUSTOM_DRAWER_LABEL_ONE_SOURCE_READY_NOT_STUDIO")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--base",type=Path)
    parser.add_argument("--self-test",action="store_true")
    args=parser.parse_args()
    if args.self_test:
        selftest()
    else:
        need(args.base is not None,"MISSING_BASE")
        apply(args.base)
