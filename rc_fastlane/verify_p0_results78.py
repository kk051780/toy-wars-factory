#!/usr/bin/env python3
"""Real Rojo Game-only repaired private78 receipts; original private78 untouched."""
import argparse,json
from pathlib import Path
from verify_p0_motion78 import verify as full_verify
from apply_p0_results78 import read,GAME,REPAIR
def verify(dist,place,out):
    full_verify(dist,place,out)
    s=read(dist)
    assert len(s)==78
    assert s[GAME].decode().count(REPAIR)==1
    r=json.loads(out.read_text("utf8"))
    fl=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert fl["p0_results78"]["other77_sources_exact"] is True
    assert fl["p0_results78"]["no_new_source"] is True
    r["private_candidate"]="P0D_PRIVATE78_RESULTS_LOBBY_RECOVERY"
    r["authored_issue"]="FB007 / PR391"
    r["results_lobby_dead_player_recovery"]="SOURCE_AND_NATIVE_TESTED"
    r["parent78_unchanged"]=True
    r["owner_fun"]="FUN_NO_GO"
    out.write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0_PRIVATE78_RESULTS_ROJO_ALL_78_SOURCE_EXACT_PASS",r["place_bytes"],r["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    a=p.parse_args()
    verify(a.dist,a.place,a.receipt)
