#!/usr/bin/env python3
"""REAL69 8-NPC source-only ART420 report. Does NOT score beauty or FPS."""
from __future__ import annotations
import argparse, hashlib, json, xml.etree.ElementTree as ET
from pathlib import Path

SCENES = ("lobby","field_wide","castle","sea","forest","neutral","beast","combat")
DEVICES = ("pc","android")
VERSIONS = ("before","after")
SHA_ORIGINAL = "fc63171149a86f6b39779ba6ebe7e18fcb7099fbde98ad2ec33a7cb92b3a9934"
SOURCE_ORIGINAL = "c8a78277b74669caebfb7ac6e1dc18f065c537f2da00cf22d8fd7fbca0bf5a00"
SOURCE_CANDIDATE = "2e4b398927873a51203115feda60027c0720b847f3f5f2dd1f5189c1a161a8d6"
NAME = "EGGRUMBLE_LegacyTwinBiomes"

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def require(condition: bool,key: str) -> None:
    if not condition:
        raise ValueError("RED_GQ470_ART_REPORT_" + key)

def script_map(data: bytes) -> tuple[ET.Element,dict]:
    root=ET.fromstring(data)
    scripts={}
    for item in root.iter("Item"):
        if item.get("class") not in ("Script","LocalScript","ModuleScript"):continue
        prop=item.find("Properties")
        require(prop is not None,"PROPS")
        name=prop.find('string[@name="Name"]')
        src=prop.find('string[@name="Source"]')
        require(name is not None and name.text and src is not None,"SCRIPT_PAYLOAD")
        require(name.text not in scripts,"DUPLICATE_SCRIPT")
        scripts[name.text]={"class":item.get("class"),"source":src.text or "", "node":src}
    require(len(scripts)==69,"SCRIPT_69")
    return root,scripts

def audit(old: bytes,new: bytes,evidence: dict,head: str) -> dict:
    require(len(head)==40 and all(c in "0123456789abcdef" for c in head),
            "PINNED_HEAD")
    old_xml,old_scripts=script_map(old)
    new_xml,new_scripts=script_map(new)
    require(len(list(old_xml.iter("Item")))==len(list(new_xml.iter("Item")))==75,
            "ITEM_CLASS_TOPOLOGY")
    require(set(old_scripts)==set(new_scripts) and NAME in old_scripts,
            "SOURCE_IDENTITY")
    changed={name for name in old_scripts
             if old_scripts[name]["source"]!=new_scripts[name]["source"]}
    require(changed=={NAME}, "OTHER_68_UNMODIFIED")
    require(old_scripts[NAME]["class"]==new_scripts[NAME]["class"]=="Script",
            "SCRIPT_CLASS")
    old_src=old_scripts[NAME]["source"]; new_src=new_scripts[NAME]["source"]
    require(sha(old_src.encode())==SOURCE_ORIGINAL and
            sha(new_src.encode())==SOURCE_CANDIDATE, "SOURCE_SHA")
    require(sha(old)==SHA_ORIGINAL and len(old)==798390, "ORIGINAL_PLACE_SHA")
    require(new_src.count("GQ470_FB015_TWIN_CREATURE_SILHOUETTES_REAL69_20261121")==1,
            "ACTUAL_ART_MARKER")
    require(all('ArtSilhouette"' in new_src for _ in range(1)) and
            new_src.count('stem.CFrame=stem.CFrame*CFrame.Angles')==1 and
            new_src.count('horn.CFrame=horn.CFrame*CFrame.Angles')==1,
            "SILHOUETTE_CONTENT")
    new_scripts[NAME]["node"].text=old_scripts[NAME]["node"].text
    require(ET.tostring(old_xml)==ET.tostring(new_xml), "ANY_NON_SOURCE_XML_DRIFT")
    shots=evidence.get("shots",[])
    triple={(x.get("scene"),x.get("device"),x.get("version")) for x in shots}
    expected={(s,d,v) for s in SCENES for d in DEVICES for v in VERSIONS}
    require(len(shots)==len(triple)==32 and triple==expected, "ART_32_SCENE_SCHEMA")
    return {
      "schema":"P0D_GQ470_REAL69_TWIN_NPC_ART_SOURCE_REPORT_V1",
      "candidate_head":head, "official_baseline_head":"e80973c354f14a0d0088577f3cc1a875454f0f8f",
      "game_profile":"REAL69_PRIVATE_COMPANION_NOT_ACTIVE_RICH51",
      "actual_candidate_place_bytes":len(new), "actual_candidate_place_sha256":sha(new),
      "original_place_bytes":len(old), "original_place_sha256":sha(old),
      "source_gate":{"status":"PASS_SOURCE_ONLY","on_scripts":69,
                     "source_count_changed":1,"unchanged_other_sources":68,
                     "place_items_before_after":[75,75],
                     "place_structural_xml_equal_except_selected_source":True,
                     "actual_neutral_npc_variants":4,"actual_spawn_per_biome_shore":2,
                     "new_static_parts_in_source":0,
                     "source_no_new_damaging_authority":True,
                     "warning":"Static source checks do not prove in-engine NPC count, visibility or quality"},
      "visual_evidence_gate":{"status":"MISSING","screenshots_required":32,
                              "screenshots_received":0, "scenes":list(SCENES),
                              "before_after_camera_matched":"NOT_TESTED"},
      "human_art":{"status":"NOT_TESTED","pc_target_5":4.5,
                   "android_target_5":4.0,"scores_received":0},
      "mobile_runtime":{"status":"NOT_TESTED","low_end_android_15min":False,
                        "median_fps_target":30,"p10_fps_target":25,
                        "heat_deterioration_fraction_target_max":0.20,
                        "measured_fps":None,"device_model":None},
      "kid_first3min_fun":{"status":"NOT_TESTED","rating_5":None},
      "studio_solo":"NOT_TESTED","studio_two_client":"NOT_TESTED",
      "owner_accepted":False,"art_gate":"ART_NO_GO","mobile_gate":"MOBILE_NO_GO",
      "fun_gate":"FUN_NO_GO","product_gate":"PRODUCT_NO_GO",
      "required_next":"Same-camera Roblox Studio old/new 32 PNG + real Android 15min FPS + human ART + OWNER accept"
    }

def test_mutations(old: bytes,new:bytes,evidence:dict,head:str) -> None:
    orig=audit(old,new,evidence,head)
    require(orig["source_gate"]["unchanged_other_sources"]==68,"BASE_POSITIVE")
    bad=dict(evidence);bad["shots"]=evidence["shots"][:-1]
    bads=((old,old,evidence,head),(old,new,bad,head),
          (old,new,evidence,"bad"),(new,new,evidence,head))
    for before,after,ev,s in bads:
        try:audit(before,after,ev,s)
        except ValueError:continue
        raise AssertionError("ART_REPORT_MUTANT_NOT_REJECTED")
    print("GQ470_REAL69_ART420_REPORT_FOUR_MUTANT_NEGATIVES_PASS")

def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--old-place",type=Path,required=True)
    p.add_argument("--new-place",type=Path,required=True)
    p.add_argument("--evidence-template",type=Path,required=True)
    p.add_argument("--candidate-head",required=True)
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    old=args.old_place.read_bytes();new=args.new_place.read_bytes()
    evidence=json.loads(args.evidence_template.read_text())
    report=audit(old,new,evidence,args.candidate_head)
    test_mutations(old,new,evidence,args.candidate_head)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("GQ470_REAL69_TWIN_NPC_SOURCE_ART_REPORT_PASS_ART_NO_GO_0_OF_32")

if __name__=="__main__":
    main()
