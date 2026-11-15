#!/usr/bin/env python3
"""FB008 / #470 cumulative repair: original #382 16+1 fair-hit Horde,
plus #382-author-bounded six-pack initial formation, on FB003 fixed real RC82.
Reversible, default OFF, and only original MusouHorde source changes.
"""
from __future__ import annotations
import argparse,hashlib,json,os,shutil,tempfile
from pathlib import Path
from apply_fb003_prompt_fix import read,blob
from apply_fb008_density import apply_horde,H,ORIGINAL_BLOB

ROOT=Path(__file__).resolve().parent
AUTHOR=ROOT/"apply_fb008_density.py"
AUTHOR_BLOB="cb35806584ec7a7683fefbe5081906f3a9d695ad"
AUTHOR_OUTPUT_BLOB="8b4bf0d3e77f52f93d94e8e5da451227f9316d6b"
FEATURE="FB008_ORIGINAL17_SIXPACK_REAL82_V1"
PARENT="FB003_OWNER_PROMPT_ACCESS_AND_H2_DISAMBIGUATION_V1"
OLD_POS=(
"    -- Center routes within the original 250x142 arena, NOT remote fantasy scenery.\n"
"    for i=1,MAX_ACTIVE do\n"
"        local elite=(i==MAX_ACTIVE)\n"
"        local x=if elite then 0 else ((i-1)%4-1.5)*16\n"
"        local z=if elite then 0 else (if i<=4 then -18 elseif i<=8 then 18 elseif i<=12 then -6 else 6)\n"
)
NEW_POS=(
"    -- Group six light enemies into a readable first-sweep formation; other ten and elite stay.\n"
"    -- Reuse original #382 17-mob movement/fair-hit logic; do not increase attack authority.\n"
"    local openingPack = {\n"
"        Vector2.new(-24,-18),Vector2.new(-19,-18),Vector2.new(-14,-18),\n"
"        Vector2.new(-24,-12),Vector2.new(-19,-12),Vector2.new(-14,-12),\n"
"    }\n"
"    for i=1,MAX_ACTIVE do\n"
"        local elite=(i==MAX_ACTIVE)\n"
"        local packed=openingPack[i]\n"
"        local x=if elite then 0 elseif packed then packed.X else ((i-1)%4-1.5)*16\n"
"        local z=if elite then 0 elseif packed then packed.Y else (if i<=4 then -18 elseif i<=8 then 18 elseif i<=12 then -6 else 6)\n"
)

def patch(source:bytes)->bytes:
    assert blob(AUTHOR.read_bytes())==AUTHOR_BLOB,"PR382_ORIGINAL_AUTHOR_DRIFT"
    assert blob(source)==ORIGINAL_BLOB,"ORIGINAL_RC82_HORDE_DRIFT"
    authored=apply_horde(source)
    assert blob(authored)==AUTHOR_OUTPUT_BLOB,"PR382_PATCH_OUTPUT_DRIFT"
    text=authored.decode("utf8")
    assert text.count(OLD_POS)==1,"PR382_FORMATION_ANCHOR_CHANGED"
    text=text.replace(OLD_POS,NEW_POS,1)
    assert text.count(NEW_POS)==1
    # Author's combat damage and 6-target cap unchanged.
    assert "local MINIONS = 16" in text and "local MAX_ACTIVE = 17" in text
    assert "local MINION_HP = 24" in text
    assert "touched<6" in text
    assert "(impactsByPlayer[nearest] or 0)<2" in text
    assert "minionImpacts<4" in text
    assert "local openingPack" in text
    assert "Horde:hit(" in text and text.count("function Horde:tick(")==1
    restored=text.replace(NEW_POS,OLD_POS,1).encode("utf8")
    assert restored==authored,"NON_FORMATION_CHANGE_AFTER_PR382"
    assert len({(x,y) for x,y in [(-24,-18),(-19,-18),(-14,-18),(-24,-12),(-19,-12),(-14,-12)]})==6
    return text.encode("utf8")

def apply(base:Path,out:Path,enabled:bool)->bool:
    assert not out.exists(),"OUTPUT_ALREADY_EXISTS"
    if not enabled:
        print("P0D_FB008_SIXPACK_DISABLED_ZERO_WRITE")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and out.parent.is_dir()
    assert not out.is_relative_to(base) and not base.is_relative_to(out)
    before=read(base)
    assert len(before)==82 and H in before and blob(before[H])==ORIGINAL_BLOB
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    oldpins={p:blob(data) for p,data in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==82
    assert sl["blobs"]==fl["source_gitblobs"]==oldpins
    assert fl["feature_flags"].get(PARENT) is True,"FB003_PARENT_ABSENT"
    assert FEATURE not in fl["feature_flags"],"DUPLICATE_FB008"
    new_horde=patch(before[H])
    after=dict(before);after[H]=new_horde
    assert {p for p in before if after[p]!=before[p]}=={H}
    assert len(after)==82
    pins={p:blob(data) for p,data in sorted(after.items())}
    meta={
        "feedback_id":"FB008","feature_id":FEATURE,"parent":PARENT,
        "source_author_pr":382,"source_author_blob":AUTHOR_BLOB,
        "base_horde_blob":ORIGINAL_BLOB,"author_original_horde_output":AUTHOR_OUTPUT_BLOB,
        "new_horde_blob":pins[H],"only_modified_source":H,
        "other81_byte_exact":True,"normal_minions":16,"elite_count":1,
        "max_sweep_targets":6,"minion_hit_cap_tick":4,
        "minion_hit_cap_per_player_tick":2,"opening_pack_count":6,
        "all_game_egg_hp_remote_store_sources_unmodified":True,
        "studio_real_6_ko":"NOT_TESTED","android":"NOT_TESTED",
        "owner_accepted":False,"quality":"PRODUCT_NO_GO",
        "rollback":"omit only FB008 overlay; previous FB003 fixed 82 exactly"
    }
    sl["blobs"]=pins
    fl["source_gitblobs"]=pins
    sl["fb008_sixpack"]=fl["fb008_sixpack"]=meta
    fl["feature_flags"][FEATURE]=True
    tmp=Path(tempfile.mkdtemp(prefix=".p0d_fb008_",dir=str(out.parent)))
    staged=tmp/"candidate"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/H).write_bytes(new_horde)
        for name,data in (("SOURCE_LOCK.json",sl),("RC_FEATURE_LOCK.json",fl)):
            (staged/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after and read(base)==before,"STAGE_SOURCE_DRIFT"
        os.replace(staged,out)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
    print("P0D_FB008_RC82_SIXPACK_SOURCE_81_EXACT_PASS",pins[H])
    return True

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--base",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--enabled",choices=("true","false"),required=True)
    args=a.parse_args()
    apply(args.base,args.out,args.enabled=="true")
