#!/usr/bin/env python3
"""P0D FB005 source-pinned #402 bot unstuck + async lease backport to PRIVATE78.

Source-authored #402 patch_bot second half is parsed as literal exact text
substitutions from its immutable Git blob. The first half (spectators/LOS)
has already been independently authored into our full-game #401 parent.
The 77 other Luau sources, especially Game authority, remain byte identical.
"""
from __future__ import annotations
import argparse,ast,json,os,shutil,tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob,BASE_RC

ROOT=Path(__file__).resolve().parent
AUTHOR=ROOT/"features/p0_bot_path78/qa_firstplay_p0_AUTHOR402.py"
AUTHOR_BLOB="0b7d982a5be7e23a9196324c6011325915d2c1b2"
BOT="server/SoloTeamBots.luau"
GAME="server/Game.server.luau"
FIX="FB005_BOT_PATH_UNSTUCK_LEASE_SOURCERY_QA_V1"
ORIGINAL_BOT_BLOB="84f59050da4f4fcdf6630d8f08e65af72af8fa1a"

def authored_pairs()->list[tuple[str,str]]:
    raw=AUTHOR.read_bytes()
    assert gitblob(raw)==AUTHOR_BLOB,"P0_BOT_PATH_AUTHOR_SOURCE_DRIFT"
    tree=ast.parse(raw.decode("utf8"))
    funcs=[f for f in tree.body if isinstance(f,ast.FunctionDef) and f.name=="patch_bot"]
    assert len(funcs)==1,"P0_BOT_PATH_AUTHOR_FUNCTION_DRIFT"
    pairs=[]
    begun=False
    for node in funcs[0].body:
        if not isinstance(node,ast.Assign) or len(node.targets)!=1:continue
        if not isinstance(node.targets[0],ast.Name) or node.targets[0].id!="text":continue
        value=node.value
        if not isinstance(value,ast.Call) or not isinstance(value.func,ast.Name) or value.func.id!="one":continue
        assert len(value.args)==3 and isinstance(value.args[0],ast.Name) and value.args[0].id=="text"
        old=ast.literal_eval(value.args[1])
        new=ast.literal_eval(value.args[2])
        assert isinstance(old,str) and isinstance(new,str)
        if old=="local TICK_MIN=.35":begun=True
        if begun:pairs.append((old,new))
    assert len(pairs)==16,("P0_BOT_PATH_AUTHOR_REWRITE_COUNT_DRIFT",len(pairs))
    assert pairs[0][0]=="local TICK_MIN=.35"
    assert pairs[-1][0].startswith("    if bot.lastGoal==nil")
    assert "bot.detourGoal=position+detour" in pairs[-1][1]
    assert "MAX_PENDING_PATH_TASKS" in "\n".join(new for _,new in pairs)
    assert "releasePathLease(bot)" in "\n".join(new for _,new in pairs)
    return pairs

def patch_bot(src:str)->str:
    for marker in (
        'P0D_LateJoinSpectator','if eligible~=1 then Bot.stop();return end',
        'if eligible~=1 then return false end',
        'and team and (team=="RED" or team=="BLUE")',
        'params.FilterDescendantsInstances={attackerCharacter}',
        'local function pathTo(bot,goal,now)',
        'local function move(bot,goal,now)',
    ):
        assert marker in src,("P0_BOT_PATH_PRIOR_GUARDS_MISSING",marker)
    assert FIX not in src and "MAX_PENDING_PATH_TASKS" not in src,"P0_BOT_PATH_ALREADY_ADOPTED"
    assert src.count("function Bot.start(")==src.count("function Bot.tick(")==1
    assert src.count("local function move(")==1
    original=src
    for i,(old,new) in enumerate(authored_pairs()):
        assert src.count(old)==1,("P0_BOT_PATH_AUTHOR_SOURCE_CONFLICT",i,old[:120],src.count(old))
        src=src.replace(old,new,1)
    for marker in (
        'MAX_PENDING_PATH_TASKS=10','pendingPathTasks=0',
        'releasePathLease(bot)','now<bot.detourUntil and gap>2.5',
        'flatDistance<=4.5 then','flatDistance<=bot.lastProgressDistance-2.5',
        'bot.hum:MoveTo(bot.detourGoal)',
        'if eligible~=1 then return false end',
        'if eligible~=1 then Bot.stop();return end',
        'and team and (team=="RED" or team=="BLUE")',
    ):
        assert marker in src,("P0_BOT_PATH_OUTPUT_DRIFT",marker)
    assert "MAX_PENDING_PATH_TASKS" not in original
    assert src.count("function Bot.start(")==src.count("function Bot.tick(")==1
    assert src.count("local function move(")==1
    assert src.count("local function pathTo(")==1
    assert "P0D_LateJoinSpectator" in src
    return src

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_PRIVATE78_BOT_PATH_OFF_ZERO_WRITE");return False
    base=base.absolute();out=out.absolute()
    assert base.is_dir() and not base.is_symlink(),"BOT_PATH_MISSING_FULL78_PARENT"
    assert out.parent.is_dir() and not out.exists() and not out.is_symlink()
    assert base!=out and not base.is_relative_to(out) and not out.is_relative_to(base)
    before=read(base)
    assert len(before)==78 and BOT in before and GAME in before
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(v) for p,v in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==78
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["p0_private77"]["official_base"]==BASE_RC
    assert fl["p0_spectator_h2_78"]["other76_byte_exact"]
    assert fl["p0_round_epoch_role78"]["other77_sources_byte_exact"]
    assert fl["p0_recovery_v2_78"]["other77_scripts_byte_exact"]
    assert "p0_bot_path78" not in fl and "p0_bot_path78" not in sl
    after={**before,BOT:patch_bot(before[BOT].decode("utf8")).encode("utf8")}
    assert {p for p in before if before[p]!=after[p]}=={BOT}
    assert after[GAME]==before[GAME],"BOT_PATH_MUST_NOT_CHANGE_GAME"
    pins78={p:gitblob(v) for p,v in sorted(after.items())}
    receipt={
        "id":FIX,"authored_pr":402,"source_author_blob":AUTHOR_BLOB,
        "parent_original_author_bot":ORIGINAL_BOT_BLOB,
        "source_author_pairs":16,
        "only_existing_bot_changed":True,"other77_sources_byte_exact":True,
        "Game_egg_HP_score_Remote_unchanged":True,
        "new_scripts":0,"new_feature_ids":0,"count":78,
        "movement_recovery":"5s_stalled_then_alternate_lateral_MoveTo_up_to_2.6s_no_teleport",
        "pathfinding":"logical_leases_generation_guard_raw_pending_ComputeAsync_max10",
        "native_QA":"AUTHOR402_ACTOR19_MOVE35_PATH18_TESTS_REQUIRED",
        "studio_engine":"NOT_TESTED","android":"NOT_TESTED",
        "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO","official_adopted":False,
        "rollback":"omit private78 bot path overlay and retain existing 78 all-features parent",
    }
    sl["blobs"]=pins78;fl["source_gitblobs"]=pins78
    sl["p0_bot_path78"]=receipt;fl["p0_bot_path78"]=receipt
    staging=Path(tempfile.mkdtemp(prefix=".p0d_path78_",dir=out.parent))
    temp=staging/"candidate"
    try:
        shutil.copytree(base,temp,symlinks=False)
        (temp/"src"/BOT).write_bytes(after[BOT])
        (temp/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (temp/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(temp)==after
        assert json.loads((temp/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins78
        assert json.loads((temp/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins78
        assert not out.exists()
        os.replace(temp,out)
    finally:
        shutil.rmtree(staging,ignore_errors=True)
    assert read(base)==before,"P0_BOT_PATH_PARENT78_MUTATED"
    print("P0_PRIVATE78_BOT_PATH_AUTHOR402_ONLY_BOT_SOURCE_LOCK_PASS")
    return True

if __name__=="__main__":
    a=argparse.ArgumentParser()
    a.add_argument("--base",type=Path,required=True)
    a.add_argument("--out",type=Path,required=True)
    a.add_argument("--enabled",required=True,choices=("true","false"))
    opts=a.parse_args()
    apply(opts.base,opts.out,opts.enabled=="true")
