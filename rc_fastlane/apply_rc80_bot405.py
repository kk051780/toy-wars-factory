#!/usr/bin/env python3
"""Author-pinned #405 safety-only Bot lifecycle patch over exact RC80 source.
No new scripts, Game/Remote/score/HP/Store authority, or gameplay features.
OFF does zero writes; ON creates a new separate source-locked Studio candidate.
"""
from __future__ import annotations
import argparse, copy, json, os, shutil, tempfile
from pathlib import Path
from apply_fb017_no_guides import read, blob

BOT="server/SoloTeamBots.luau"
GAME="server/Game.server.luau"
AUTHOR405="0b95421a390759dea32f279e3a299edcd6b9361f"
KEY="AI_PATH_CALLBACK_CLEANUP_AUTHOR405"
PATCHES=[
("""        if current then
            if ok and path and path.Status==Enum.PathStatus.Success then
                bot.path=path:GetWaypoints()
                bot.pathIndex=math.min(2,#bot.path)
            else
                bot.path={}
                bot.pathIndex=1
            end
        end
        -- Old asynchronous planners must not release a newer planner's lock.""",
"""        local applied,applyErr=pcall(function()
            if current then
                if ok and path and path.Status==Enum.PathStatus.Success then
                    bot.path=path:GetWaypoints()
                    bot.pathIndex=math.min(2,#bot.path)
                else
                    bot.path={}
                    bot.pathIndex=1
                end
            end
        end)
        if not applied then
            warn("P0D_BOT_PATH_RESULT_FAILED",applyErr)
            if current then bot.path={};bot.pathIndex=1 end
        end
        -- Old asynchronous planners must not release a newer planner's lock."""),
("""        releasePathLease(bot)
        clearCarry(bot)
        if bot.model then bot.model:Destroy() end""",
"""        releasePathLease(bot)
        local cleared,clearErr=pcall(clearCarry,bot)
        if not cleared then warn("P0D_BOT_EGG_DROP_FAILED",clearErr) end
        bot.carry=nil
        local destroyed,destroyErr=pcall(function()
            if bot.model then bot.model:Destroy() end
        end)
        if not destroyed then warn("P0D_BOT_MODEL_TEARDOWN_FAILED",destroyErr) end"""),
("""    if folder then folder:Destroy();folder=nil end
    map=nil;callbacks=nil""",
"""    if folder then
        local oldFolder=folder
        folder=nil
        local ok,err=pcall(function() oldFolder:Destroy() end)
        if not ok then warn("P0D_BOT_FOLDER_TEARDOWN_FAILED",err) end
    end
    map=nil;callbacks=nil"""),
("""    for key,value in pairs(fresh) do bot[key]=value end
    bot.pathGeneration=nextGeneration""",
"""    for key,value in pairs(fresh) do bot[key]=value end
    -- Lua pairs cannot overwrite previous-life fields with nil.
    bot.lastProgressDistance=nil
    bot.lastProgressAt=0
    bot.unstuckAttempts=0
    bot.detourGoal=nil
    bot.detourUntil=0
    bot.pathLease=nil
    bot.pathGeneration=nextGeneration"""),
("if flatDistance<=4.5 then", "if (position-goal).Magnitude<=4.5 then"),
]

def patch_source(src:str)->str:
    assert 'MAX_PENDING_PATH_TASKS=10' in src
    assert 'releasePathLease(bot)' in src
    assert 'P0D_LateJoinSpectator' in src
    assert src.count('local function pathTo(')==1
    assert src.count('local function respawn(bot)')==1
    assert src.count('function Bot.stop()')==1
    assert src.count('function Bot.start(')==1
    assert KEY not in src
    out=src
    for index,(old,new) in enumerate(PATCHES):
        assert out.count(old)==1,("AUTHOR405_EXPECTED_PARENT_DRIFT",index,out.count(old))
        assert new not in out,("AUTHOR405_DUPLICATE",index)
        out=out.replace(old,new,1)
    assert out!=src and out.count('P0D_BOT_PATH_RESULT_FAILED')==1
    assert out.count('P0D_BOT_EGG_DROP_FAILED')==1
    assert out.count('P0D_BOT_FOLDER_TEARDOWN_FAILED')==1
    assert 'if (position-goal).Magnitude<=4.5 then' in out
    assert src.count("DataStoreService")==out.count("DataStoreService")
    return out

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        assert not out.exists(),"OFF_ZERO_WRITE"
        print("P0D_BOT405_OFF_ZERO_WRITE_PASS")
        return False
    base=base.resolve();out=out.absolute()
    assert base.is_dir() and not base.is_symlink() and out.parent.is_dir()
    assert not out.exists() and not out.is_symlink()
    assert base!=out and not base.is_relative_to(out) and not out.is_relative_to(base)
    before=read(base)
    assert len(before)==80 and BOT in before and GAME in before
    old_pins={p:blob(v) for p,v in sorted(before.items())}
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    assert sl["total_scripts"]==fl["total_sources"]==80
    assert sl["blobs"]==fl["source_gitblobs"]==old_pins
    assert fl["feature_flags"]["FB016_FOLIAGE_PASSAGE_20261114"] is True
    assert fl["feature_flags"]["FB017_NO_PERSISTENT_BATTLE_GUIDES"] is True
    assert KEY not in sl and KEY not in fl
    patched=patch_source(before[BOT].decode("utf8")).encode("utf8")
    after={**before,BOT:patched}
    assert {k for k in before if before[k]!=after[k]}=={BOT}
    assert after[GAME]==before[GAME]
    pins={p:blob(v) for p,v in sorted(after.items())}
    receipt={
        "id":KEY,"source_author_pr":405,"author_commit":AUTHOR405,
        "prior_bot_gitblob":old_pins[BOT],"updated_bot_gitblob":pins[BOT],
        "replacement_count":len(PATCHES),"same_script_count":80,
        "only_existing_bot_changed":True,"other79_sources_byte_exact":True,
        "game_remote_egg_score_hp_store_unchanged":True,
        "native_tests":"ACTOR26_PATH25_MOVE38_REQUIRED",
        "studio":"NOT_TESTED","android":"NOT_TESTED","owner_acceptance":"NOT_TESTED",
        "official_rc_adopted":False,
        "rollback":"omit isolated AUTHOR405 patch; retain RC80",
    }
    sl["blobs"]=pins;sl[KEY]=receipt
    fl["source_gitblobs"]=pins;fl[KEY]=receipt
    staging=Path(tempfile.mkdtemp(prefix=".bot405_",dir=out.parent))
    staged=staging/"dist"
    try:
        shutil.copytree(base,staged,symlinks=False)
        (staged/"src"/BOT).write_bytes(patched)
        (staged/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (staged/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(staged)==after
        assert read(base)==before
        os.replace(staged,out)
    finally:
        shutil.rmtree(staging,ignore_errors=True)
    print("P0D_RC80_BOT405_ONLY_BOT_CHANGED_79_OTHER_EXACT_PASS",pins[BOT])
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    args=p.parse_args()
    apply(args.base,args.out,args.enabled=="true")
