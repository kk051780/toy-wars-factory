#!/usr/bin/env python3
"""Independent source-only #983 ART17 Swarm overlap proof, never formal admission."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from zipfile import ZipFile
from patch_swarm_subject69 import TARGET,PROJECT,RECEIPT,PLACE,NEW,OLD,patch,selected

ART17_SHA="443914a672f4f535fe4c6313b0dec524892a0afeb4684a8d935e4eebb1458305"
ART17_SIZE=822713
ART17_SWARM_SHA="09e72ccce28fb669725a71b40e26fac276900a0ffa737f24a193f778b0378925"
PREFIX="on/B220_ART16_P0_SELECTED17_NOT_FORMAL/selected_sources/"

def sha(b):return hashlib.sha256(b).hexdigest()
def need(ok,message):
    if not ok:raise ValueError("RED_ART17_SWARM_SUBJECT_"+message)

def prepare(formal:Path,artifact:Path,destination:Path):
    need(not destination.exists(),"REUSED_OUTPUT")
    orig=selected(formal)
    need(len(orig)==69,"FORMAL_69_MISSING")
    before={k:v.read_bytes() for k,v in orig.items()}
    with ZipFile(artifact) as z:
        names=[n for n in z.namelist() if n.startswith(PREFIX) and n.endswith(".luau")]
        need(len(names)==17,"SELECTED17")
        art_receipt=json.loads(z.read("on/"+RECEIPT))
        art_place=z.read("on/"+PLACE)
        need(len(art_place)==ART17_SIZE and sha(art_place)==ART17_SHA,
             "AUTHENTIC_ART17_PRIVATE_PLACE")
        need(z.read("on/"+PROJECT)==(formal/PROJECT).read_bytes(),"PROJECT_NONLOSS")
        changed={}
        for name in names:
            route=name.removeprefix(PREFIX).removesuffix(".luau")
            need(route in before and route not in changed,"ROUTE_COLLISION")
            changed[route]=z.read(name)
        need(TARGET in changed and sha(changed[TARGET])==ART17_SWARM_SHA,
             "REAL_ART17_SWARM_SOURCE_SHA")
        need(set(art_receipt["source_hashes"])==set(orig),"RECEIPT_ROUTES")
        for key,previous in before.items():
            src=changed.get(key,previous)
            need(sha(src)==art_receipt["source_hashes"][key],"ART17_SOURCE_IDENTITY_"+key)
        need(len([x for x in changed if changed[x]!=before[x]])==17,"SEVENTEEN_CHANGED")
        shutil.copytree(formal,destination)
        s=selected(destination)
        for key,payload in changed.items():s[key].write_bytes(payload)
    (destination/"ART17_PARENT_SWARM_EXACT.luau").write_bytes(changed[TARGET])
    revised=patch(changed[TARGET].decode("utf-8")).encode("utf-8")
    need(revised.decode("utf-8").replace(NEW,OLD).encode("utf-8")==changed[TARGET],
         "ONE_LINE_INVERSE")
    need(b"GQ470_FB015_NEUTRAL_HORDE_8_SPECIES_MATTE_FACETS_REAL69_20261121" in revised,
         "EIGHT_SPECIES_ART_MISSING")
    s[TARGET].write_bytes(revised)
    after={k:v.read_bytes() for k,v in selected(destination).items()}
    need(len(after)==69 and {k for k in before if before[k]!=after[k]}==set(changed),
         "EXACT_ART17_SET_17_NOT_18")
    r=json.loads((destination/RECEIPT).read_text(encoding="utf-8"))
    r["source_hashes"]={k:sha(v) for k,v in after.items()}
    r["build_head"]="A_ONLY_ART17_PLUS_SWARM_SUBJECT_NOT_FORMAL"
    meta={"formal_rc_integrated":False,"art17_parent_place_sha256":ART17_SHA,
          "art17_swarm_before_sha256":ART17_SWARM_SHA,
          "art17_subject_swarm_after_sha256":sha(revised),
          "source_select_count":69,"art17_changed_source_count":17,
          "preserved_original_source_count":52,"added_script_count":0,
          "gameplay_authority_changes":0,"studio":"NOT_TESTED",
          "art_screenshots":"0/32","android15":"NOT_TESTED",
          "owner_accepted":False}
    r["gq470_art17_subject_compat"]=meta
    (destination/RECEIPT).write_text(json.dumps(r,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    (destination/"GQ470_ART17_SUBJECT_COMPAT_SOURCE_ONLY.json").write_text(
      json.dumps(meta,sort_keys=True,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print("GQ470_ART17_17_SOURCE_NONLOSS_SUBJECT_PASS",json.dumps(meta,sort_keys=True))

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--formal",type=Path,required=True)
    p.add_argument("--art17-zip",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    prepare(args.formal,args.art17_zip,args.output)
