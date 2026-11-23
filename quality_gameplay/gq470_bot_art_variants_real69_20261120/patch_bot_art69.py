#!/usr/bin/env python3
"""ART-JOBS source-only bot hero visual variety for genuine REAL69.

This operates on the pinned official PRIVATE Studio build. It edits only the
already selected HeroSilhouetteArt Script; it never creates a second runtime.
Prep/CI passing is not a Studio/Android/human art acceptance.
"""
from __future__ import annotations
import argparse, hashlib, json, shutil
from pathlib import Path

BASE = "c226c63eeb235503f9292503b61f2173550337ec"
TARGET = "ServerScriptService/EGGRUMBLE_HeroSilhouetteArt"
BASE_HASH = "7ca5be97c2c76cb0b7d4c228168a6f14fa6ecf213de31eb4222086d358462da4"
PROJECT = "EGGRUMBLE_REAL69.project.json"
RECEIPT = "REAL69_LEGACY_INTAKE_RECEIPT.json"
MARK = "GQ470_ART_BOT_THREE_ARCHETYPES_REAL69_20261120"
START = "local function decorateAI(model:Model)\n"
END = "local function watchRole(player:Player)\n"

REPLACEMENT = """-- GQ470_ART_BOT_THREE_ARCHETYPES_REAL69_20261120
-- Existing BotActors AI hero body art only. 7-piece cap per bot, no extra AI,
-- collision, combat authority, remote, HUD or new render loop.
local MAX_BOT_ARMOR_PIECES=7
local function botArmorVariant(id:any):number
 local value=tostring(id)
 local signature=0
 -- Position-weighted IDs collapse to one archetype if the changing digit
 -- occupies a character index divisible by 3. A rolling hash keeps adjacent
 -- numeric BotIds spread across all three appearances, with stable identity.
 for i=1,#value do signature=(signature*31+string.byte(value,i))%3 end
 return signature
end

local function decorateAI(model:Model)
 if marked[model] or model:GetAttribute("EGGRUMBLE_BotId")==nil then return end
 local torso=model:FindFirstChild("HumanoidRootPart")
 if not torso or not torso:IsA("BasePart") then return end
 marked[model]=true
 -- Avoid retaining destroyed AI models across repeated matches/respawns.
 model.Destroying:Connect(function() marked[model]=nil end)
 local red=torso.Color.R>torso.Color.B
 local primary=if red then Color3.fromRGB(124,66,62) else Color3.fromRGB(58,91,137)
 local silver=Color3.fromRGB(207,186,140)
 local shadow=Color3.fromRGB(57,64,80)
 local accent=if red then Color3.fromRGB(234,174,115) else Color3.fromRGB(132,211,232)
 local variant=botArmorVariant(model:GetAttribute("EGGRUMBLE_BotId"))
 local visual=Instance.new("Folder")
 visual.Name="EGGRUMBLE_BotVisuals"
 visual:SetAttribute("EGGRUMBLE_VisualArchetype",if variant==0 then "BULWARK" elseif variant==1 then "SCOUT" else "ENGINEER")
 visual.Parent=model
 local count=0
 local function g(name:string,shape:string,offset:CFrame,size:Vector3,color:Color3,material:Enum.Material)
  if count>=MAX_BOT_ARMOR_PIECES then return end
  count+=1
  -- piece() is the existing noncolliding, nonqueryable, massless welded helper.
  piece(visual,torso,name,shape,size,offset,color,material,false)
 end
 if variant==0 then
  -- Front-line bulwark: wide iron shoulders, jaw guard and split cuirass.
  g("BulwarkChest","Wedge",CFrame.new(0,.3,-.94)*CFrame.Angles(0,math.pi,0),
   Vector3.new(2.25,1.75,.58),primary,Enum.Material.Metal)
  for _,side in ipairs({-1,1}) do
   g("BulwarkPauldron"..side,"Wedge",
    CFrame.new(side*1.54,1.03,0)*CFrame.Angles(0,side*math.pi/2,0),
    Vector3.new(1.30,1.24,1.6),silver,Enum.Material.Metal)
   g("BulwarkTasset"..side,"Wedge",CFrame.new(side*.75,-1.38,.55),
    Vector3.new(.97,1.48,.45),primary,Enum.Material.Slate)
  end
  g("BulwarkHelm","Wedge",CFrame.new(0,2.80,-.2),
   Vector3.new(.76,1.18,1.13),silver,Enum.Material.Metal)
  g("BulwarkBackShield","Block",CFrame.new(0,.18,.99),
   Vector3.new(1.91,2.05,.28),shadow,Enum.Material.Metal)
 elseif variant==1 then
  -- Fast scout: a sloping hood and paired back blades, not a color-only clone.
  g("ScoutHood","Wedge",CFrame.new(0,2.33,-.14)*CFrame.Angles(0,math.pi,0),
   Vector3.new(1.90,1.38,1.42),shadow,Enum.Material.Fabric)
  g("ScoutMask","Block",CFrame.new(0,1.75,-1.0),
   Vector3.new(1.44,.36,.34),primary,Enum.Material.Fabric)
  for _,side in ipairs({-1,1}) do
   g("ScoutMantle"..side,"Wedge",
    CFrame.new(side*1.20,.78,.34)*CFrame.Angles(0,side*math.pi/2,0),
    Vector3.new(.96,.80,1.5),primary,Enum.Material.Fabric)
   g("ScoutBlade"..side,"Wedge",
    CFrame.new(side*.54,.22,1.05)*CFrame.Angles(math.rad(-17),0,math.rad(side*19)),
    Vector3.new(.23,2.04,.26),accent,Enum.Material.Metal)
  end
  g("ScoutCoat","Wedge",CFrame.new(0,-1.72,.94),
   Vector3.new(1.81,2.22,.35),shadow,Enum.Material.Fabric)
 else
  -- Field engineer: recognizable squared pack, sensor mast and facial visor.
  g("EngineerBackpack","Block",CFrame.new(0,.08,1.15),
   Vector3.new(1.98,2.16,.69),shadow,Enum.Material.Metal)
  g("EngineerReactor","Cylinder",
   CFrame.new(0,.11,1.55)*CFrame.Angles(0,0,math.pi/2),
   Vector3.new(.17,1.15,1.15),accent,Enum.Material.Glass)
  for _,side in ipairs({-1,1}) do
   g("EngineerFrame"..side,"Block",CFrame.new(side*1.38,.65,.09),
    Vector3.new(.57,1.50,1.12),primary,Enum.Material.Metal)
  end
  g("EngineerAntenna","Cylinder",CFrame.new(.71,2.69,.84),
   Vector3.new(.15,1.42,.15),silver,Enum.Material.Metal)
  g("EngineerVisor","Block",CFrame.new(0,2.19,-1.03),
   Vector3.new(1.40,.39,.28),accent,Enum.Material.Glass)
  g("EngineerApron","Wedge",CFrame.new(0,-1.58,-.75),
   Vector3.new(1.40,1.85,.32),primary,Enum.Material.Fabric)
 end
end

"""

def require(ok: bool, reason: str) -> None:
    if not ok:
        raise ValueError("RED_BOT_ARMOR_" + reason)

def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def selected(root: Path) -> dict[str, Path]:
    project=json.loads((root/PROJECT).read_text(encoding="utf-8"))
    found={}
    def visit(node,route=""):
        if not isinstance(node,dict): return
        if "$path" in node: found[route]=root/node["$path"]
        for key,value in node.items():
            if not key.startswith("$"): visit(value,route+"/"+key if route else key)
    visit(project["tree"])
    return found

def transform(source: str) -> str:
    require(MARK not in source, "DUPLICATE")
    require(source.count(START)==1 and source.count(END)==1, "ANCHOR")
    require(source.index(START)<source.index(END), "ORDER")
    require("local PART_BUDGET_PER_SUBJECT = 13" in source, "SEVEN_ROLE_BUDGET")
    require("local function sculpt(parent:Instance,anchor:BasePart,role:string,static:boolean)" in source,
            "ROLE_SCULPT_PRESERVATION")
    require('p.CanCollide=false' in source and 'p.CanQuery=false' in source,
            "DECOR_NONPHYSICAL")
    left=source[:source.index(START)]
    right=source[source.index(END):]
    output=left+REPLACEMENT+right
    require(output.count(MARK)==1 and output.count("local function decorateAI(model:Model)")==1,
            "SINGLE_ART_OWNER")
    require(output.count("local function watchRole(player:Player)")==1,
            "PLAYER_ROLE_PRESERVATION")
    return output

def selftest():
    old=("local PART_BUDGET_PER_SUBJECT = 13\n"
         "p.CanCollide=false;p.CanQuery=false\n"
         "local function sculpt(parent:Instance,anchor:BasePart,role:string,static:boolean)\nend\n"
         +START+" end\n"+END+" end\n")
    new=transform(old)
    require("BulwarkChest" in new and "ScoutBlade" in new and "EngineerBackpack" in new,
            "THREE_ARCHETYPES")
    require("model.Destroying:Connect" in new and "MAX_BOT_ARMOR_PIECES=7" in new,
            "CLEANUP_BUDGET")
    require("signature=(signature*31+string.byte(value,i))%3" in new,
            "VARIANT_HASH_REACHABLE")
    def current_variant(value: str) -> int:
        sig = 0
        for character in value:
            sig = (sig * 31 + ord(character)) % 3
        return sig
    def previous_variant(value: str) -> int:
        sig = 0
        for i, character in enumerate(value, 1):
            sig = (sig + ord(character) * i) % 3
        return sig
    # Six-character BotIds demonstrate the real original regression:
    # changing only the last digit at position six used to alter nothing.
    ids = ["BOTID" + str(i) for i in (1, 2, 3)]
    require(len({previous_variant(v) for v in ids}) == 1,
            "REPRO_LEGACY_SAME_APPEARANCE")
    require(len({current_variant(v) for v in ids}) == 3,
            "THREE_IDENTITY_SILHOUETTES")
    for prefix in ("AI_BOT_", "TEAM_BOT00", "B_2026_"):
        require(len({current_variant(prefix + str(i)) for i in (1, 2, 3)}) == 3,
                "NUMERIC_SUFFIX_DIVERSITY")
    for mutant in (new,old.replace(START,""),old.replace(END,""),
                   old.replace("p.CanQuery=false","p.CanQuery=true")):
        try: transform(mutant)
        except ValueError: pass
        else: raise AssertionError("RED_BOT_ARMOR_NEGATIVE_NOT_BLOCKED")
    print("GQ470_ART_BOT_3_ARCHETYPES_4_NEGATIVES_PASS")

def apply(root: Path, current_head: str|None=None):
    paths=selected(root)
    receipt_path=root/RECEIPT
    receipt=json.loads(receipt_path.read_text(encoding="utf-8"))
    require(len(paths)==69 and TARGET in paths, "REAL69_69_ROUTES")
    require(receipt.get("build_head")==(current_head or BASE) and len(receipt.get("source_hashes",{}))==69,
            "PINNED_HEAD")
    old={key:checksum(value.read_bytes()) for key,value in paths.items()}
    require(old==receipt["source_hashes"],"69_HASH_RECONCILIATION")
    require(old[TARGET]==BASE_HASH, "BOT_ART_PARENT_HASH")
    require(not (root/"off69_bot_art").exists(),"ROLLBACK_COLLISION")
    save=root/"off69_bot_art"
    shutil.copytree(root/"sources",save/"sources")
    for name in (PROJECT,RECEIPT,"EGGRUMBLE_REAL69_PRIVATE.rbxlx"):
        shutil.copy2(root/name,save/name)
    original=paths[TARGET].read_bytes()
    transformed=transform(original.decode("utf-8")).encode("utf-8")
    paths[TARGET].write_bytes(transformed)
    current={key:checksum(value.read_bytes()) for key,value in paths.items()}
    require(len(current)==69 and set(current)==set(old),"ROUTES")
    require({key for key in old if old[key]!=current[key]}=={TARGET},"ONLY_ART_SCRIPT")
    require((save/paths[TARGET].relative_to(root)).read_bytes()==original,"EXACT_ROLLBACK")
    receipt["source_hashes"][TARGET]=checksum(transformed)
    receipt["build_head"]=current_head or ("PREP_BOT_ART_FROM_"+BASE)
    receipt["gq470_bot_art_variants"]={
      "feature_id":MARK,"formal_parent":BASE,"route":TARGET,
      "original_source_sha256":BASE_HASH,
      "changed_source_sha256":checksum(transformed),
      "other_selected_routes_byte_exact":68,"source_count":69,
      "max_parts_per_bot":7,"visual_archetypes":["BULWARK","SCOUT","ENGINEER"],
      "new_scripts":0,"new_combat_authority":False,"collision_changed":False,
      "rollback":"off69_bot_art","studio":"NOT_TESTED","android":"NOT_TESTED",
      "human_art":"NOT_TESTED","owner_accepted":False}
    receipt_path.write_text(json.dumps(receipt,ensure_ascii=False,indent=2,sort_keys=True)+"\n",
                            encoding="utf-8")
    print("GQ470_ART_BOT_ONE_SOURCE_68_EXACT_OFF69_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--self-test",action="store_true")
    parser.add_argument("--base",type=Path)
    parser.add_argument("--head",type=str,default=None)
    opts=parser.parse_args()
    if opts.self_test:selftest()
    else:
        require(opts.base is not None,"MISSING_BASE")
        apply(opts.base,opts.head)
