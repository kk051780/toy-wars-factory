#!/usr/bin/env python3
"""EGGRUMBLE REAL69 A-only GuildShop art: reversible visual source patch.

Uses *the actual fixed official 69-source artifact*, never guesses an active
Script source from historical 31/48/65 candidate branches.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
ORIGINAL_ARTIFACT = 14610422120
ORIGINAL_SOURCE_SHA = "139fb22fd8051635dc2f5a892777983c37dbe16cf741eb82cd213a829993ba6d"
ROUTE = "ServerScriptService/GQ805_LobbyGuildShop"
FILE = "sources/ServerScriptService/GQ805_LobbyGuildShop.server.luau"
FEATURE = "GQ470_FB015_GUILD_GUARDIAN_SCULPT_REAL69_20261121"

OLD_ROOF = '''piece(world,"GuildRoof",Vector3.new(0,11,2),Vector3.new(29,2,17),Color3.fromRGB(67,89,138),false,Enum.Material.Slate)'''
NEW_ROOF = '''-- GQ470_FB015_GUILD_GUARDIAN_SCULPT_REAL69_20261121
-- Shop roof: two static faceted slate pitches replace one flat bar; no
-- collision/query or gameplay ownership, +1 Part once per private Studio.
for half=-1,1,2 do
 local pitch=Instance.new("WedgePart")
 pitch.Name=if half<0 then "GuildRoofWestPitch" else "GuildRoofEastPitch"
 pitch.Size=Vector3.new(17,3,14.5)
 pitch.Anchored=true;pitch.CanCollide=false;pitch.CanTouch=false
 pitch.CanQuery=false;pitch.CastShadow=true
 pitch.Material=Enum.Material.Slate
 pitch.Color=if half<0 then Color3.fromRGB(75,94,119)
  else Color3.fromRGB(88,105,128)
 local yaw=if half<0 then math.rad(-90) else math.rad(90)
 pitch.CFrame=CFrame.new(center+Vector3.new(half*7.25,11,2))*CFrame.Angles(0,yaw,0)
 pitch.Parent=world
 made+=1
end'''

OLD_PREVIEW = '''  local torso=piece(figurine,"GuardianBody",Vector3.new(x,1.35,z),Vector3.new(1.35,2.1,.95),r[3],false)
  local head=piece(figurine,"GuardianHead",Vector3.new(x,2.9,z),Vector3.new(1,1,1),Color3.fromRGB(247,217,166),false)
  head.Shape=r[4]
  local weapon=piece(figurine,"SignatureGear",Vector3.new(x+1,1.7,z),Vector3.new(.35,if variant==1 then 1.8 else 2.4,.5),Color3.fromRGB(243,222,160),false,Enum.Material.Metal)
  if i==4 then weapon.Shape=Enum.PartType.Ball end
  if i==6 then head.Shape=Enum.PartType.Ball end'''
NEW_PREVIEW = '''  -- Keep EXACT four noncolliding parts per figurine (14 guardians / 56 parts).
  -- Two variants read as scout/guardian through lean, bulk and gear posture.
  local compact=variant==1
  local bulk=if compact then 1.15 else 1.62
  local tall=if compact then 2.05 else 2.34
  local torso=piece(figurine,"GuardianBody",Vector3.new(x,1.35,z),
   Vector3.new(bulk,tall,if compact then .85 else 1.13),r[3],false,
   if i==1 or i==5 then Enum.Material.Slate else Enum.Material.SmoothPlastic)
  torso.Shape=if i==2 or i==4 then Enum.PartType.Cylinder else Enum.PartType.Block
  torso.CFrame=torso.CFrame*CFrame.Angles(0,math.rad((i-4)*6),
   math.rad(if compact then -7 else 5))
  local head=piece(figurine,"GuardianHead",Vector3.new(x,2.9,z),
   Vector3.new(if i==1 or i==5 then 1.18 else .94,1.05,.96),
   Color3.fromRGB(236,205,164),false)
  head.Shape=if i==2 or i==4 or i==6 then Enum.PartType.Ball else r[4]
  head.CFrame=head.CFrame*CFrame.Angles(0,math.rad((i-4)*9),0)
  local weapon=piece(figurine,"SignatureGear",Vector3.new(x+1,1.7,z),
   Vector3.new(if i==4 then .65 else .30,if compact then 1.9 else 2.5,
    if i==1 or i==3 then .36 else .48),
   Color3.fromRGB(181,187,169),false,Enum.Material.Metal)
  weapon.Shape=if i==2 or i==6 or i==7 then Enum.PartType.Cylinder
   elseif i==4 then Enum.PartType.Ball else Enum.PartType.Block
  weapon.CFrame=weapon.CFrame*CFrame.Angles(0,math.rad((i-4)*7),
   math.rad(if compact then -18 else 14))
  weapon.CastShadow=true'''

OLD_ENTRY='''piece(world,"GuildEntry",Vector3.new(0,2,-10),Vector3.new(8,4,1),Color3.fromRGB(236,195,87),false,Enum.Material.Neon)'''
# Guild entry is stored as "local door" and must remain the ProximityPrompt owner.
OLD_DOOR = '''local door=piece(world,"GuildEntry",Vector3.new(0,2,-10),Vector3.new(8,4,1),Color3.fromRGB(236,195,87),false,Enum.Material.Neon)'''
NEW_DOOR = '''local door=piece(world,"GuildEntry",Vector3.new(0,2,-10),Vector3.new(8,4,1),Color3.fromRGB(189,166,108),false,Enum.Material.SmoothPlastic)'''

def insist(value: bool, code: str) -> None:
    if not value:
        raise ValueError("RED_GQ470_GUILD_" + code)

def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def patch(original: str) -> str:
    insist(FEATURE not in original, "ALREADY_PATCHED")
    for name, anchor in (("ROOF", OLD_ROOF), ("GUARDIAN", OLD_PREVIEW), ("DOOR", OLD_DOOR)):
        insist(original.count(anchor) == 1, "EXACT_" + name + "_ANCHOR")
    for guard in ("RunService:IsStudio()", 'world.Name="GQ805_LobbyGuildShop"',
                  'world:SetAttribute("EGGRUMBLE_NoPurchaseAuthority",true)',
                  'prompt.Name="GQ805_ShopReadOnlyPrompt"',
                  "prompt.RequiresLineOfSight=true", "for i,r in ipairs(roles) do",
                  "for variant=1,2 do", 'plaque(stand,r[2]..'):
        insist(guard in original, "GUARD_MISSING_" + guard)
    updated=original.replace(OLD_ROOF, NEW_ROOF, 1)
    updated=updated.replace(OLD_PREVIEW, NEW_PREVIEW, 1)
    updated=updated.replace(OLD_DOOR, NEW_DOOR, 1)
    insist(updated.count(FEATURE) == 1, "FEATURE_MARKER_ONCE")
    insist(updated.count('piece(figurine,"GuardianBody"') == 1 and
           updated.count('piece(figurine,"GuardianHead"') == 1 and
           updated.count('piece(figurine,"SignatureGear"') == 1,
           "FOUR_PARTS_PER_FIGURINE")
    insist(updated.count('local door=piece(world,"GuildEntry"') == 1 and
           updated.count("prompt.Parent=door") == 1, "PROMPT_OWNER_EXACT")
    insist(unpatch(updated) == original, "OFF_INVERSE")
    return updated

def unpatch(updated: str) -> str:
    for name, anchor in (("ROOF", NEW_ROOF), ("GUARDIAN", NEW_PREVIEW), ("DOOR", NEW_DOOR)):
        insist(updated.count(anchor) == 1, "OFF_" + name + "_ANCHOR")
    return updated.replace(NEW_ROOF, OLD_ROOF, 1).replace(
        NEW_PREVIEW, OLD_PREVIEW, 1).replace(NEW_DOOR, OLD_DOOR, 1)

def selected_routes(project: dict) -> dict[str,str]:
    found: dict[str,str] = {}
    def walk(node: dict, prefix: str = "") -> None:
        if "$path" in node:
            insist(prefix not in found, "DUP_ROUTE")
            found[prefix]=node["$path"]
            return
        for name, val in node.items():
            if not name.startswith("$") and isinstance(val,dict):
                walk(val, prefix+"/"+name if prefix else name)
    walk(project["tree"])
    return found

def build(archive_file: Path, output_dir: Path) -> dict:
    insist(not output_dir.exists(), "DEST_EXISTS")
    with zipfile.ZipFile(archive_file) as z:
        names=z.namelist()
        insist(len(names)==len(set(names)),"DUPLICATE_ZIP_ENTRY")
        insist(all(not name.startswith("/") and
                   ".." not in PurePosixPath(name).parts for name in names),
               "ZIP_PATH_TRAVERSAL")
        project_bytes=z.read("EGGRUMBLE_REAL69.project.json")
        receipt_bytes=z.read("REAL69_LEGACY_INTAKE_RECEIPT.json")
        project=json.loads(project_bytes)
        receipt=json.loads(receipt_bytes)
        paths=selected_routes(project)
        insist(receipt.get("build_head")==BASE and receipt.get("canonical_build") is True,
               "PINNED_FORMAL_HEAD")
        insist(receipt.get("official_branch")=="rc/p0d-s1-kids-rc01" and
               receipt.get("source_profile")=="REAL69",
               "CANONICAL_BRANCH_AND_PROFILE")
        insist(len(paths)==69 and receipt.get("selected_source_count")==69,
               "SOURCE_COUNT_69")
        insist(set(paths)==set(receipt.get("source_hashes",{})), "RECEIPT_ROUTES")
        insist(set(paths)==set(receipt.get("source_classes",{})), "RECEIPT_CLASSES_69")
        insist(paths.get(ROUTE)==FILE, "GUILD_ROUTE_PATH")
        insist(receipt["source_classes"].get(ROUTE)=="Script", "GUILD_RECEIPT_SCRIPT_CLASS")
        selected_guild=project["tree"].get("ServerScriptService",{}).get("GQ805_LobbyGuildShop",{})
        insist(selected_guild.get("$className","Script")=="Script","GUILD_PROJECT_SCRIPT_CLASS")
        sources={}
        for route,path in paths.items():
            insist(path.startswith("sources/") and path in names, "PATH_" + route)
            raw=z.read(path)
            insist(digest(raw)==receipt["source_hashes"][route], "HASH_" + route)
            sources[route]=raw
        original=sources[ROUTE]
        insist(digest(original)==ORIGINAL_SOURCE_SHA,"SOURCE_ORIGINAL_PINNED_SHA")
        candidate=patch(original.decode("utf-8")).encode("utf-8")
        insist(unpatch(candidate.decode("utf-8")).encode("utf-8")==original,
               "EXACT_OFF69")
        output_dir.mkdir(parents=True)
        for route,path in paths.items():
            to=output_dir/path
            insist(to.resolve().is_relative_to(output_dir.resolve()), "PATH_ESCAPE")
            to.parent.mkdir(parents=True,exist_ok=True)
            to.write_bytes(candidate if route==ROUTE else sources[route])
        (output_dir/"EGGRUMBLE_REAL69.project.json").write_bytes(project_bytes)
        (output_dir/"OFF69_ORIGINAL_GUILD.server.luau").write_bytes(original)
        (output_dir/"OFF69_ORIGINAL_RECEIPT.json").write_bytes(receipt_bytes)
        updated=copy.deepcopy(receipt)
        updated["source_hashes"][ROUTE]=digest(candidate)
        updated["candidate_gq470_guild_sculpt"]={
            "feature_id": FEATURE, "source_target": ROUTE, "original_artifact": ORIGINAL_ARTIFACT,
            "formal_head_unmodified": BASE, "other_selected_sources_byte_exact": 68,
            "original_source_sha256": digest(original), "candidate_source_sha256": digest(candidate),
            "roof_parts_before_after": [1,2], "guardian_models": 14,
            "decorative_parts_per_guardian_before_after":[4,4],
            "new_instance_parts_total":1, "gameplay_authority_changes":0,
            "new_remote_or_store":0, "studio":"NOT_TESTED","android":"NOT_TESTED",
            "art_gate":"ART_NO_GO","fun_gate":"FUN_NO_GO","owner_accepted":False,
            "official_rc_adopted":False}
        (output_dir/"REAL69_LEGACY_INTAKE_RECEIPT.json").write_text(
            json.dumps(updated,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
        qa={"schema":"GQ470_GUILD_SCULPT_REAL69_SOURCE_QA_V1","feature_id":FEATURE,
            "formal_base_head":BASE,"candidate_route":ROUTE,"selected_script_count":69,
            "other_selected_byte_exact":68,"source_sha_before":digest(original),
            "source_sha_after":digest(candidate),"source_before_bytes":len(original),
            "source_after_bytes":len(candidate),"rollback_byte_exact":True,
            "extra_decorative_parts":1,"new_scripts":0,"new_runloops":0,
            "purchase_authority_changed":False,
            "official_rc_adopted":False,"studio":"NOT_TESTED","android":"NOT_TESTED",
            "art_gate":"ART_NO_GO","fun_gate":"FUN_NO_GO","owner_accepted":False}
        (output_dir/"GQ470_GUILD_SOURCE_QA.json").write_text(json.dumps(qa,ensure_ascii=False,indent=2,sort_keys=True)+"\n")
        return qa

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--artifact",type=Path,required=True)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.artifact,args.out),ensure_ascii=False,indent=2))
