#!/usr/bin/env python3
"""Source-select exactly one #815 Swarm overlay + unchanged #801 Curse Policy.
All 42 other Real43 Roblox sources remain byte-exact. Never write official RC.
"""
from __future__ import annotations
import argparse,copy,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"gq800_neutral8_single_swarm_20261118"))
from compose_real43 import flatten

SWARM=("ServerScriptService","EGGRUMBLE_SwarmCombat")
CURSE=("ServerScriptService","EGGRUMBLE_CurseConversionPolicy")
ORIGINAL_SWARM_BLOB="0f4774c543d60b91c261cc6e871d77aa937149cb"
ORIGINAL_CURSE_BLOB="0bd81a807ff6a935642a660b9fe9e0fd05ef484c"

def blob(data:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()

def prepare(real43:Path,selected_swarm:Path,original_curse:Path,out:Path):
    old,files=flatten(real43)
    assert len(files)==43 and SWARM in files and CURSE not in files,"RED_WRONG_REAL43"
    assert blob(files[SWARM].read_bytes())==ORIGINAL_SWARM_BLOB,"RED_SIBLING_SOURCE_MOVED"
    assert blob(original_curse.read_bytes())==ORIGINAL_CURSE_BLOB,"RED_NOT_IMMUTABLE_801_POLICY"
    source=selected_swarm.read_bytes()
    assert source.count(b"local Swarm={}") == 1
    assert source.count(b"CursePolicy.seal(state,os.clock(),{") == 1
    assert source.count(b"h:TakeDamage(damage)") == 1
    assert source.count(b"eh:TakeDamage(8)") == 1
    assert b"existingSummoned=3" in source
    assert b"if not charmed[m]" in source
    assert out.parent != real43.parent and not out.exists(),"RED_OUTPUT_NOT_ISOLATED"
    out.parent.mkdir(parents=True,exist_ok=True)
    result=copy.deepcopy(old)
    result["name"]="GQ800_REAL44_CURSE_SOURCE_PREVIEW_NOT_OFFICIAL"
    selected=out.parent/"EGGRUMBLE_SwarmCombat_Curse44.luau"
    selected.write_bytes(source)
    policy=out.parent/"EGGRUMBLE_CurseConversionPolicy.luau"
    policy.write_bytes(original_curse.read_bytes())
    result["tree"]["ServerScriptService"]["EGGRUMBLE_SwarmCombat"]["$path"]=selected.name
    result["tree"]["ServerScriptService"]["EGGRUMBLE_CurseConversionPolicy"]={"$path":policy.name}
    out.write_text(json.dumps(result,ensure_ascii=False,sort_keys=True,indent=2)+"\n")
    _,now=flatten(out)
    assert len(now)==44 and set(now)==set(files)|{CURSE}
    assert {r for r in files if now[r].read_bytes()!=files[r].read_bytes()}=={SWARM},"RED_OTHER_OWNER_MUTATED"
    assert now[CURSE].read_bytes()==original_curse.read_bytes()
    assert now[SWARM].suffix==".luau" and now[CURSE].suffix==".luau"
    receipt={"schema":"GQ800_REAL44_CURSE_LIVE_SOURCE_V1","on_sources":44,"off_sources":43,
      "unchanged_original":42,"changed_original":["/".join(SWARM)],
      "added_original_policy_blob":ORIGINAL_CURSE_BLOB,
      "original_swarm_blob":ORIGINAL_SWARM_BLOB,"selected_swarm_blob":blob(source),
      "single_swarm":True,"new_remote_store_game_owner":False,
      "conservative_charmed_per_zombie":1,"duration_seconds":14,
      "previous_582_summons_reserved":3,"source_ready":True,
      "official_rc_adopted":False,"studio_2client":"NOT_TESTED","android":"NOT_TESTED",
      "rollback":"Re-select unchanged Real43 selected source and remove Curse module"}
    (out.parent/"REAL44_RECEIPT.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    print("REAL44_SOURCE_EXACT_ONE_SWARM_ONE_CURSE_MODULE_PASS")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    for x in ("real43","selected_swarm","original_curse","out"):p.add_argument("--"+x,required=True,type=Path)
    a=p.parse_args()
    prepare(a.real43,a.selected_swarm,a.original_curse,a.out)
