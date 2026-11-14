#!/usr/bin/env python3
"""FB-008 source-locked RC80 cumulative intake of original PR382 Horde crowd patch.

Use after FB017 final RC80 assembly. 80 scripts stay 80, the one Horde
module changes and 79 original sources remain exact. No Game authority added.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
from apply_fb017_no_guides import read,blob
from apply_fb008_density import apply_horde,ORIGINAL_BLOB,H

HERE=Path(__file__).resolve().parent
AUTHORED=HERE/"apply_fb008_density.py"
AUTHOR_BLOB="cb35806584ec7a7683fefbe5081906f3a9d695ad"
PATCHED_BLOB="8b4bf0d3e77f52f93d94e8e5da451227f9316d6b"
FEATURE="FB008_17_MINIONS_FAIR_HITS_RC80_V1"
BASE_FEATURE="FB017_NO_PERSISTENT_BATTLE_GUIDES"

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"OFF_MUST_NOT_WRITE"
        print("FB008_OFF_ZERO_WRITE_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir() and not out.exists()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    assert blob(AUTHORED.read_bytes())==AUTHOR_BLOB,"AUTHORED_PR382_BLOB_DRIFT"
    before=read(base)
    assert len(before)==80 and H in before and "server/Game.server.luau" in before
    oldpins={p:blob(data) for p,data in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==oldpins,"BASE_SOURCE_LOCK_DRIFT"
    assert fl["feature_flags"].get(BASE_FEATURE) is True,"REQUIRE_RC80_FB017"
    assert FEATURE not in fl["feature_flags"],"DUPLICATE_FB008"
    assert blob(before[H])==ORIGINAL_BLOB,"HORDE_SOURCES_CHANGED"
    patched=apply_horde(before[H])
    assert blob(patched)==PATCHED_BLOB,"AUTHOR_OUTPUT_BLOB_DRIFT"
    after=dict(before);after[H]=patched
    assert len(after)==80 and sum(after[p]!=before[p] for p in before)==1
    pins={p:blob(data) for p,data in sorted(after.items())}
    report={
        "feedback_id":"FB-008",
        "feature_id":FEATURE,"author_pr":382,
        "pinned_author_blob":AUTHOR_BLOB,
        "prior_horde_blob":ORIGINAL_BLOB,"new_horde_blob":PATCHED_BLOB,
        "changed_source":H,"other79_byte_exact":True,
        "single_game_remote_store_hp_egg_authority_unchanged":True,
        "horde_minion_count":16,"horde_elite_count":1,
        "regular_hit_cap_per_tick_total":4,
        "regular_hit_cap_per_player_per_tick":2,
        "crowd_separation_studs":5,
        "new_script_count":0,
        "rollback":"omit FB008 adapter: original RC80 byte-identical",
        "studio_gameplay":"NOT_TESTED",
        "owner_acceptance":"NOT_TESTED"
    }
    sl["blobs"]=pins;sl["fb008_crowd"]=report
    fl["source_gitblobs"]=pins;fl["feature_flags"][FEATURE]=True
    fl["fb008_crowd"]=report
    temp=Path(tempfile.mkdtemp(prefix=".fb008_",dir=str(out.parent)))
    try:
        staged=temp/"dist"
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/H).write_bytes(patched)
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(temp,ignore_errors=True)
    print("FB008_CUMULATIVE_RC80_79_OTHER_SOURCES_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
