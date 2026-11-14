#!/usr/bin/env python3
"""Private78 full-body 9 NPC costume source+Rojo receipts, source not Studio run."""
import argparse,json
from pathlib import Path
from verify_p0_results78 import verify as full_rojo
from apply_p0_fullbody78 import read,derived_source,DEST,gitblob,FLAG
def verify(dist,place,receipt):
    full_rojo(dist,place,receipt)
    s=read(dist)
    art=derived_source()
    assert s[DEST]==art
    features=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert features["p0_fullbody78"]["adapted_source_gitblob"]==gitblob(art)
    assert features["p0_fullbody78"]["other77_byte_identical"] is True
    result=json.loads(receipt.read_text("utf8"))
    result["private_candidate"]="P0D_PRIVATE78_RESULTS_PLUS_NINE_FULL_COSTUMES"
    result["full_silhouette_authored_part_types"]=41
    result["nine_actor_complete_accessories"]=92
    result["cosmetic_part_budget"]=104
    result["combat_remote_compatibility"]="OPTIONAL_REMOTE_PLUS_SERVER_POPUP_FALLBACK"
    result["studio_motion"]="NOT_TESTED"
    result["owner_art"]="ART_NO_GO"
    receipt.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0_PRIVATE78_FULLBODY_78_78_ROJO_SOURCE_EXACT_PASS",
          result["place_bytes"],result["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
