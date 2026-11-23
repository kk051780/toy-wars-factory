#!/usr/bin/env python3
"""GQ8 P0: repair pickup verb mismatch in original ONE V3 InteractionGuard.

Original 9 item prompts use display ActionText="拾って使う"; new RC86 six
weapon prompts use "拾って強化"; both call the SAME existing server guard with
verb="拾う". Prior configuredReach accepted exact ActionText=="拾う" only,
so ALL 15 gameplay pickups were denied despite green Native/Rojo Source QA.
This patch preserves the Japanese UI and restricts aliases to "拾う".
"""
from __future__ import annotations
import argparse,hashlib,json
from pathlib import Path

ROUTE="ServerScriptService/EGGRUMBLE_InteractionGuard"
FIX_ID="GQ8_RC86_ITEM_PROMPT_VERB_ALIAS_GATE_P0_20261119"
ORIGINAL='''  if child:IsA("ProximityPrompt") and child.Enabled and child.ActionText==verb then'''
FIX='''  -- GQ8 RC86 pickup repair: the visible Japanese label is not the guard verb.
  -- Alias ONLY existing server-authorized "拾う" for the two genuine UI labels.
  local isPrompt=child:IsA("ProximityPrompt")
  local pickupAlias=isPrompt and verb=="拾う"
   and (child.ActionText=="拾って使う" or child.ActionText=="拾って強化")
  if isPrompt and child.Enabled and (child.ActionText==verb or pickupAlias) then'''

def patch(body:str)->str:
    if body.count(ORIGINAL)!=1 or FIX_ID in body:
        raise ValueError("RED_ITEM_GUARD_ORIGINAL_PROMPT_CONTRACT_DRIFT")
    for token in (
        'local function configuredReach(part:BasePart,verb:string):number?',
        'local function positionValid(actor:Player,part:BasePart,verb:string):boolean',
        'local function positionValid(actor:Player,part:BasePart,verb:string):boolean',
        '["拾う"]=0.38',
        'if selected then return nil end',
        'if hit and hit.Instance~=part then return false end',
    ):
        if token not in body:
            raise ValueError("RED_ITEM_GUARD_MISSING_"+token[:28])
    # The old duplicate-token check is harmless; preserve configuredReach strictness.
    fixed=body.replace(ORIGINAL,FIX,1)
    fixed=fixed.replace(
        '  -- GQ8 RC86 pickup repair: the visible Japanese label is not the guard verb.',
        '  -- '+FIX_ID+': visible label is not the server guard verb.',1)
    if fixed.count("pickupAlias=isPrompt and verb==\"拾う\"")!=1:
        raise ValueError("RED_ITEM_GUARD_PICKUP_ALIAS_MISSING")
    if fixed.count('or child.ActionText=="拾って強化"')!=1:
        raise ValueError("RED_ITEM_GUARD_STAGE_WEAPON_LABEL_NOT_HANDLED")
    if fixed.replace(
         '  -- '+FIX_ID+': visible label is not the server guard verb.',
         '  -- GQ8 RC86 pickup repair: the visible Japanese label is not the guard verb.',1
       ).replace(FIX,ORIGINAL,1)!=body:
        # Handle inserted sentinel normalisation below instead.
        normalized=fixed.replace(
            '  -- '+FIX_ID+': visible label is not the server guard verb.',
            '  -- GQ8 RC86 pickup repair: the visible Japanese label is not the guard verb.',1)
        if normalized.replace(FIX,ORIGINAL,1)!=body:
            raise ValueError("RED_ITEM_GUARD_UNRELATED_ORIGINAL_CHANGE")
    for token in ("RemoteEvent","ProcessReceipt","DataStoreService",":TakeDamage("):
        if fixed.count(token)!=body.count(token):
            raise ValueError("RED_ITEM_GUARD_ADDED_GAME_AUTHORITY")
    return fixed

def self_test()->None:
    base="\n".join([
     'local function configuredReach(part:BasePart,verb:string):number?',
     'local function positionValid(actor:Player,part:BasePart,verb:string):boolean',
     '["拾う"]=0.38',
     'if selected then return nil end',
     'if hit and hit.Instance~=part then return false end',
     ORIGINAL,'return selected','end'
    ])
    result=patch(base)
    assert 'verb=="拾う"' in result
    assert 'child.ActionText=="拾って使う"' in result
    assert 'child.ActionText=="拾って強化"' in result
    for mutation in (result,base.replace('["拾う"]=0.38','["拾う"]=0.0'),
                     base.replace('child.ActionText==verb','child.ActionText=="任意"')):
        try:patch(mutation)
        except ValueError:pass
        else:raise AssertionError("RED_PICKUP_VERB_MUTANT_NOT_DETECTED")
    print("GQ8_REAL65_PICKUP_LABEL_VERB_ALIAS_NEGATIVE_PASS")

def run(project_path:Path,receipt_path:Path)->None:
    project=json.loads(project_path.read_text(encoding="utf8"))
    receipt=json.loads(receipt_path.read_text(encoding="utf8"))
    rows={r["route"]:r for r in receipt["sources"]}
    if (project["name"]!="EGGRUMBLE_REAL65_PRIVATE_STUDIO" or len(rows)!=65
      or receipt.get("rc85_rc86_stage_weapon_delta",{}).get("added_script_owners")!=0
      or not receipt.get("legacy_rc86_wind")
      or receipt.get("pickup_prompt_alias")):
        raise ValueError("RED_PICKUP_VERB_WRONG_REAL65_BASE")
    if ROUTE not in rows or rows[ROUTE]["class"]!="ModuleScript":
        raise ValueError("RED_PICKUP_GUARD_NOT_SINGLE_MODULE")
    node=project["tree"]
    for part in ROUTE.split("/"):node=node[part]
    source=project_path.parent/node["$path"]
    original=source.read_bytes()
    current=hashlib.sha256(original).hexdigest()
    if current!=rows[ROUTE]["sha256"] or len(original)!=rows[ROUTE]["bytes"]:
        raise ValueError("RED_PICKUP_GUARD_SOURCE_HASH_DRIFT")
    new=patch(original.decode("utf8")).encode("utf8")
    source.write_bytes(new)
    rows[ROUTE]["sha256"]=hashlib.sha256(new).hexdigest()
    rows[ROUTE]["bytes"]=len(new)
    if ROUTE in receipt["patched_existing_routes"]:
        raise ValueError("RED_PICKUP_GUARD_ALREADY_MODIFIED_BY_ANOTHER_LANE")
    receipt["patched_existing_routes"].append(ROUTE)
    receipt["original_real63_byte_unchanged"]-=1
    receipt["pickup_prompt_alias"]={
      "feature_id":FIX_ID,
      "bug":"Existing 9 item prompts ActionText=拾って使う and newly integrated 6 weapon prompts 拾って強化 both called guard verb=拾う, so configuredReach falsely returned nil.",
      "changed_existing":ROUTE,"unchanged_other_scripts":64,
      "selected_script_count":65,"additional_game_owners":0,
      "accepted_ui_aliases":["拾って使う","拾って強化"],
      "server_verb":"拾う","duplicate_prompt_rejection":"PRESERVED",
      "solid_wall_raycast":"PRESERVED",
      "per_player_rate_limit":"PRESERVED",
      "studio":"NOT_TESTED","android":"NOT_TESTED","fun":"NO_GO",
      "rollback":"Undo this one InteractionGuard source overlay, restore original REAL65 + exact OFF63"
    }
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",encoding="utf8")
    for row in receipt["sources"]:
        n=project["tree"]
        for part in row["route"].split("/"):n=n[part]
        raw=(project_path.parent/n["$path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=row["sha256"] or len(raw)!=row["bytes"]:
            raise ValueError("RED_PICKUP_VERB_FINAL_65_SOURCE_RECEIPT_"+row["route"])
    print("GQ8_REAL65_15_PICKUP_PROMPT_VERB_SOURCE_FIX_PASS_NO_SECOND_ITEM_OWNER")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--self-test",action="store_true")
    p.add_argument("--project",type=Path)
    p.add_argument("--receipt",type=Path)
    args=p.parse_args()
    if args.self_test:self_test()
    else:
        if not args.project or not args.receipt:p.error("--project and --receipt required")
        run(args.project,args.receipt)
