#!/usr/bin/env python3
"""Actual Rojo 78/78, unique Game, original full-body + latest solo native receipts."""
from __future__ import annotations
import argparse,json
from pathlib import Path
from verify_p0_fullbody78 import verify as validate_rojo78
from apply_p0_solo78 import GAME,HUD,ID
from apply_p0_motion78 import read
def verify(dist,place,out):
    validate_rojo78(dist,place,out)
    scripts=read(dist)
    assert len(scripts)==78
    assert '#Players:GetPlayers()>1 and chosenMode==ModeVote.SCORE' in scripts[GAME].decode("utf8")
    assert 'soloFiveEggUnavailable' in scripts[GAME].decode("utf8")
    assert 'soloFiveEggUnavailable' in scripts[HUD].decode("utf8")
    features=json.loads((dist/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert features["p0_solo78"]["id"]==ID
    assert features["p0_solo78"]["new_feature_count"]==0
    assert features["p0_solo78"]["other76_sources_byte_identical"]
    data=json.loads(out.read_text("utf8"))
    data["private_candidate"]="P0D_PRIVATE78_FULL_COSTUME_LOBBY_SOLO_BOTLESS_FIX"
    data["source_count"]=78
    data["solo_one_human_five_egg"]="CLASSIC_FIVE_BOTS_SOURCE_AND_NATIVE_VERIFIED"
    data["two_plus_humans_mode_vote"]="PRESERVED_SOURCE_AND_NATIVE_VERIFIED"
    data["formal_rc_adoption"]=0
    data["studio_solo"]="NOT_TESTED"
    data["owner_art"]="ART_NO_GO"
    data["owner_fun"]="FUN_NO_GO"
    out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0_PRIVATE78_SOLO_RESULTS_FULLBODY_ROJO_ALL_78_EXACT_PASS",
          data["place_bytes"],data["place_sha256"])
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dist",required=True,type=Path)
    p.add_argument("--place",required=True,type=Path)
    p.add_argument("--receipt",required=True,type=Path)
    args=p.parse_args()
    verify(args.dist,args.place,args.receipt)
