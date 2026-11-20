#!/usr/bin/env python3
"""One selected REAL69 SkillFX source: anti-occlusion sculpted translucent slash.
A-source only, not Studio/ART/FUN PASS. Originals remain in OFF69 rollback.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
from pathlib import Path

BASE="e80973c354f14a0d0088577f3cc1a875454f0f8f"
FEATURE="GQ470_FB015_SKILLFX_SHARD_FLASH_REAL69_20261121"
ROUTE="ServerScriptService/EGGRUMBLE_SkillFX"
SHA_BEFORE="d1656b4e0becc944b2ad15b3b6e8b053d3ec2f0bdd24bcfcf22fef4704c6bcb3"
PROJECT="EGGRUMBLE_REAL69.project.json"
RECEIPT="REAL69_LEGACY_INTAKE_RECEIPT.json"
PLACE="EGGRUMBLE_REAL69_PRIVATE.rbxlx"
OFF="OFF69_SKILLFX_SHARD_FLASH"
OLD=''' local head=effectPart(parent,"FX_"..role.."_"..slot.."_FLASH",center,Vector3.new(2,2,2),primary,life)
 if head then
  head.Shape=Enum.PartType.Ball
  animate(head,Vector3.new(radius*1.45*scale,2.4,radius*1.45*scale),life)
  particleBurst(head,secondary,if slot=="C" then 12 else 5)
 end
'''
NEW=''' -- GQ470_FB015_SKILLFX_SHARD_FLASH_REAL69_20261121
 -- Low-glare sculpted slash, not a large opaque spherical curtain.
 -- One original Part, same lifetime/lease/quota and same hit particles.
 local head=effectPart(parent,"FX_"..role.."_"..slot.."_FLASH",center,Vector3.new(2,2,2),primary,life)
 if head then
  local visualWidth=math.clamp(radius,2,12)
  head.Shape=Enum.PartType.Block
  head.Material=Enum.Material.SmoothPlastic
  head.Transparency=.55
  head.CFrame=CFrame.lookAt(center+Vector3.new(0,1.75,0),center+f*3)
   *CFrame.Angles(0,0,math.rad(24))
  animate(head,Vector3.new(.24,2.8,visualWidth*.85*scale),life,
   CFrame.lookAt(center+f*2+Vector3.new(0,1.75,0),center+f*8)
   *CFrame.Angles(0,0,math.rad(24)))
  particleBurst(head,secondary,if slot=="C" then 12 else 5)
 end
'''

def require(ok:bool,kind:str)->None:
    if not ok: raise ValueError("RED_SKILLFX_"+kind)

def sha(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def selected(root:Path)->dict[str,Path]:
    root=root.resolve()
    tree=json.loads((root/PROJECT).read_text())["tree"]
    mapping={}
    def walk(node:object,route:str="")->None:
        if not isinstance(node,dict): return
        if "$path" in node:
            rel=node["$path"]
            require(isinstance(rel,str),"PATH_FORMAT")
            src=(root/rel).resolve()
            require(src.is_relative_to(root) and src.is_file(),"PATH_ESCAPE")
            require(route not in mapping,"ROUTE_DUPLICATE")
            mapping[route]=src
        for key,value in node.items():
            if not key.startswith("$"):
                walk(value,(route+"/" if route else "")+key)
    walk(tree)
    return mapping

def inspect_visual(fragment:str)->None:
    require(fragment.count('local head=effectPart(')==1,"ONE_FLASH")
    require('head.Shape=Enum.PartType.Block' in fragment
            and 'head.Material=Enum.Material.SmoothPlastic' in fragment,
            "MATERIAL_AND_SILHOUETTE")
    require('head.Transparency=.55' in fragment
            and 'local visualWidth=math.clamp(radius,2,12)' in fragment,
            "MOBILE_OCCLUSION_LIMIT")
    require('Vector3.new(.24,2.8,visualWidth*.85*scale)' in fragment
            and 'CFrame.lookAt(center+f*2+' in fragment,
            "SLASH_SHAPE_AND_MOTION")
    require(fragment.count('particleBurst(head,secondary,if slot=="C" then 12 else 5)')==1,
            "PRESERVE_CONFIRM_FEEL")
    require(fragment.count("Instance.new(")==0
            and "RemoteEvent" not in fragment and "TakeDamage" not in fragment,
            "NO_NEW_INSTANCES_OR_AUTHORITY")
    require("Enum.Material.Neon" not in fragment and "Enum.PartType.Ball" not in fragment,
            "NO_SPHERE_NEON_HEAD")
    require("head.CanCollide" not in fragment and "head.Parent" not in fragment,
            "INHERIT_EXISTING_SAFE_FACTORY")

def transform(source:str)->str:
    require(FEATURE not in source,"DOUBLE_APPLY")
    require(source.count(OLD)==1,"PINNED_ORIGINAL_HEAD_BLOCK")
    require('local fairQuota=ModeFairQuota.new(72,12)' in source
            and 'local MAX_NEW_PER_PULSE=6' in source
            and 'if active>ACTIVE_LIMIT-MAX_NEW_PER_PULSE' in source,
            "TWO_MODE_FX_QUOTA")
    require('if role=="WARRIOR" then' in source
            and 'elseif role=="ZOMBIE" then' in source
            and 'function SkillFX.active():number return active end' in source,
            "SEVEN_ROLE_OWNER")
    inspect_visual(NEW)
    before,after=source.split(OLD,1)
    patched=before+NEW+after
    require(patched.replace(NEW,OLD,1)==source,"STRICT_ONE_HUNK")
    require(patched.count(FEATURE)==1,"ONLY_OWN_MARKER")
    require(patched.count('function SkillFX.emit(')==1,"ONE_EMITTER")
    return patched

def self_test()->None:
    original=('local fairQuota=ModeFairQuota.new(72,12)\n'
              'local MAX_NEW_PER_PULSE=6\n'
              'if active>ACTIVE_LIMIT-MAX_NEW_PER_PULSE\n'
              'if role=="WARRIOR" then\n'
              'elseif role=="ZOMBIE" then\n'
              'function SkillFX.active():number return active end\n'+OLD)
    after=transform(original)
    require(after.replace(NEW,OLD,1)==original,"SOURCE_REVERSE")
    for i,bad in enumerate((
        NEW.replace('head.Transparency=.55','head.Transparency=.12'),
        NEW.replace('Enum.Material.SmoothPlastic','Enum.Material.Neon'),
        NEW.replace('Enum.PartType.Block','Enum.PartType.Ball'),
        NEW.replace('math.clamp(radius,2,12)','radius*2'),
        NEW.replace('Vector3.new(.24,2.8,visualWidth*.85*scale)',
                    'Vector3.new(8,20,visualWidth*2)'),
        NEW.replace('particleBurst(head,secondary,if slot=="C" then 12 else 5)',
                    'particleBurst(head,secondary,if slot=="C" then 48 else 30)'),
        NEW.replace('local head=effectPart(', 'local head=Instance.new("Part")\n local x=effectPart('),
        NEW.replace('head.Material=Enum.Material.SmoothPlastic',
                    'head.Material=Enum.Material.SmoothPlastic\n  head.Parent=workspace'),
    )):
        try: inspect_visual(bad)
        except ValueError: continue
        raise AssertionError("RED_VISUAL_MUTANT_ACCEPTED_"+str(i))
    for i,bad in enumerate((after,original.replace(OLD,""),
                            original.replace('ModeFairQuota.new(72,12)',
                                             'ModeFairQuota.new(144,12)'),
                            original.replace('function SkillFX.active()',
                                             'function SkillFX.unknown()'))):
        try: transform(bad)
        except ValueError: continue
        raise AssertionError("RED_SOURCE_MUTANT_ACCEPTED_"+str(i))
    print("GQ470_SKILLFX_12_NEGATIVE_MUTATIONS_PASS")

def apply(root:Path)->None:
    root=root.resolve()
    sources=selected(root)
    require(len(sources)==69 and ROUTE in sources,"REAL69_69_ROUTE")
    hashes={k:sha(v.read_bytes()) for k,v in sources.items()}
    receipt_file=root/RECEIPT
    receipt=json.loads(receipt_file.read_text())
    require(receipt.get("canonical_build") is True
            and receipt.get("build_head")==BASE
            and receipt.get("selected_source_count")==69
            and receipt.get("source_hashes")==hashes,
            "OFFICIAL_SOURCE_HASHES")
    original=sources[ROUTE].read_bytes()
    require(sha(original)==SHA_BEFORE,"PINNED_ORIGINAL_SKILLFX_SHA")
    candidate=transform(original.decode("utf-8")).encode("utf-8")
    require(candidate!=original,"REAL_SOURCE_DELTA")
    off=root/OFF
    require(not off.exists() and (root/PLACE).is_file()
            and (root/"sources").is_dir(),"CLEAN_SOURCE_ARTIFACT")
    off.mkdir()
    shutil.copytree(root/"sources",off/"sources")
    for name in (PROJECT,RECEIPT,PLACE): shutil.copy2(root/name,off/name)
    sources[ROUTE].write_bytes(candidate)
    new_hashes={k:sha(v.read_bytes()) for k,v in selected(root).items()}
    require(len(new_hashes)==69 and
            {k for k in hashes if hashes[k]!=new_hashes[k]}=={ROUTE},
            "ONLY_ONE_SOURCE_CHANGED_68_BYTE_EXACT")
    require(selected(off)[ROUTE].read_bytes()==original,"OFF_EXACT")
    require((off/PROJECT).read_bytes()==(root/PROJECT).read_bytes(),"PROJECT_UNCHANGED")
    details={
        "feature_id":FEATURE,"formal_base":BASE,"source_route":ROUTE,
        "source_sha_before":SHA_BEFORE,"source_sha_after":sha(candidate),
        "selected_sources_changed":1,"other_selected_sources_byte_exact":68,
        "flash_parts_per_skill_before_after":[1,1],
        "new_scripts":0,"new_remotes":0,"combat_authority_changed":False,
        "two_mode_quota_72_preserved":True,"particles_preserved":True,
        "rollback":OFF,"studio_solo":"NOT_TESTED","studio_2client":"NOT_TESTED",
        "android15":"NOT_TESTED","art_photos_received":0,"art_photos_required":32,
        "human_art":"NOT_TESTED","kid_fun":"NOT_TESTED","owner_accepted":False,
        "art":"ART_NO_GO","product":"PRODUCT_NO_GO",
        "official_rc_adopted":False
    }
    receipt["source_hashes"]=new_hashes
    receipt["gq470_skillfx_shard_flash"]=details
    receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    (root/"SKILLFX_SHARD_SOURCE_REPORT.json").write_text(
        json.dumps(details,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    print("GQ470_SKILLFX_ONE_LUA_SOURCE_PREP",sha(candidate))

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--self-test",action="store_true")
    a.add_argument("--base",type=Path)
    options=a.parse_args()
    if options.self_test: self_test()
    else:
        require(options.base is not None,"BASE_ARTIFACT_REQUIRED")
        apply(options.base)
