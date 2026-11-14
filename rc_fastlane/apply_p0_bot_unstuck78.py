#!/usr/bin/env python3
"""P0 FB005: source-locked optional #400 bot motion repair in full PRIVATE78.

Applies to #403's FINAL full-game+art 78 source distribution. All 77 OTHER
Luau scripts are byte-identical; only the existing SoloTeamBots ModuleScript
changes. Never writes main/official RC or duplicates a second AI authority.
"""
from __future__ import annotations
import argparse,json,os,shutil,tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob,BASE_RC

BOT="server/SoloTeamBots.luau"
FEATURE="FB005_BOT_STUCK_5S_LATERAL_RECOVERY_PRIVATE78_QA"
AUTHOR_PR=400
STUCK_MARKER="FB005_BOT_5S_UNSTUCK_PRIVATE78_QA"

def once(s:str,a:str,b:str)->str:
    assert s.count(a)==1,("BOT_UNSTUCK_SOURCE_DRIFT",a[:100],s.count(a))
    return s.replace(a,b,1)

def patch_bot(s:str)->str:
    assert STUCK_MARKER not in s,"UNSTUCK_ALREADY_APPLIED"
    assert "P0D_LateJoinSpectator" in s,"REQUIRES_REAL_#401_SPECTATOR_BOT"
    assert "if bot.planning and now-(bot.planningSince or now)>=8 then" in s
    assert "params.FilterDescendantsInstances={attackerCharacter}" in s
    assert "if eligible~=1 then Bot.stop();return end" in s
    assert s.count("function Bot.start(")==s.count("function Bot.tick(")==1
    assert s.count("local function move(bot,goal,now)")==1
    s=once(s,"local TICK_MIN=.35",
        """local TICK_MIN=.35
-- #400 author keeps costly yielding planners capped. Old callbacks can finish
-- after the current bot or global match was canceled, but never claim a route.
local MAX_INFLIGHT_PATHS=10
local inflightPaths=0""")
    s=once(s,
        "lastAttack=0,lastGoal=nil,pathGeneration=0,planningSince=nil}",
        """lastAttack=0,lastGoal=nil,pathGeneration=0,planningSince=nil,
        lastProgressPos=nil,lastProgressAt=0,unstuckAttempts=0}""")
    s=once(s,
        """    if bot.planning or now<bot.nextRepath then return end
    bot.nextRepath=now+REPATH_SECONDS
    local token=epoch""",
        """    if bot.planning or now<bot.nextRepath
        or inflightPaths>=MAX_INFLIGHT_PATHS then return end
    inflightPaths+=1
    bot.nextRepath=now+REPATH_SECONDS
    local token=epoch""")
    s=once(s,
        """        -- Both the global match and this particular bot/goal must still be
        -- current. A respawn can happen while ComputeAsync is yielding.""",
        """        inflightPaths=math.max(0,inflightPaths-1)
        -- Both the global match and this particular bot/goal must still be
        -- current. A respawn can happen while ComputeAsync is yielding.""")
    # Exact same LATERAL 5s recovery from author #400, except do not
    # unstuck-telegraph if goal is already within melee range. Existing
    # pathfollowing and Score/Egg callbacks are untouched.
    move_start="local function move(bot,goal,now)"
    move_end="local function nearestEnemyBot(bot,maxDistance)"
    before,after=s.split(move_start,1)
    body,tail=after.split(move_end,1)
    assert body.count("    bot.lastGoal=goal\n    pathTo(bot,goal,now)")==1
    replacement="""    -- FB005_BOT_5S_UNSTUCK_PRIVATE78_QA: #400 original physical unstuck.
    if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then
        invalidatePath(bot)
        bot.lastProgressPos=bot.root.Position
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
    end
    bot.lastGoal=goal
    local position=bot.root.Position
    if bot.lastProgressPos==nil then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
    elseif (position-bot.lastProgressPos).Magnitude>=3.5 then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
        bot.unstuckAttempts=0
    elseif (goal-position).Magnitude>=6 and now-bot.lastProgressAt>=5 then
        bot.lastProgressPos=position
        bot.lastProgressAt=now
        bot.unstuckAttempts=((bot.unstuckAttempts or 0)%4)+1
        -- Path worker may finish late. Invalidate and restore the same intent.
        invalidatePath(bot)
        bot.lastGoal=goal
        local side=if bot.unstuckAttempts%2==0 then -1 else 1
        local toGoal=goal-position
        local lateral=Vector3.new(-toGoal.Z,0,toGoal.X)
        local detour=if lateral.Magnitude>.2 then
            lateral.Unit*(side*7) else Vector3.new(side*7,0,0)
        bot.hum.Jump=true
        bot.hum:MoveTo(position+detour)
        return
    end
    pathTo(bot,goal,now)"""
    old="""    -- Rival positions and the raid objective can change WHILE ComputeAsync
    -- yields. Revoke any path planned for a materially different destination.
    if bot.lastGoal==nil or (bot.lastGoal-goal).Magnitude>8 then
        invalidatePath(bot)
    end
    bot.lastGoal=goal
    pathTo(bot,goal,now)"""
    assert body.count(old)==1,"BOT_MOVE_HEADER_DRIFT"
    body=body.replace(old,replacement,1)
    s=before+move_start+body+move_end+tail
    assert s.count(STUCK_MARKER)==1
    assert "bot.hum:MoveTo(position+detour)" in s
    assert "elseif (goal-position).Magnitude>=6 and now-bot.lastProgressAt>=5 then" in s
    assert s.count("local MAX_INFLIGHT_PATHS=10")==1
    assert s.count("inflightPaths=math.max(0,inflightPaths-1)")==1
    assert s.count("function Bot.start(")==s.count("function Bot.tick(")==1
    assert s.count("local function move(bot,goal,now)")==1
    return s

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_PRIVATE78_BOT_UNSTUCK_OFF_ZERO_WRITE");return False
    base=base.absolute();out=out.absolute()
    assert base.is_dir() and not base.is_symlink(),"BOT_UNSTUCK_MISSING_PRIVATE78"
    assert out.parent.is_dir() and not out.exists() and not out.is_symlink()
    assert base!=out and not base.is_relative_to(out) and not out.is_relative_to(base)
    prev=read(base)
    assert len(prev)==78 and BOT in prev,"BOT_UNSTUCK_REQUIRES_78"
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins0={p:gitblob(v) for p,v in sorted(prev.items())}
    assert sl["total_scripts"]==fl["total_sources"]==78
    assert sl["blobs"]==fl["source_gitblobs"]==pins0
    assert fl["p0_private77"]["official_base"]==BASE_RC
    assert fl["p0_recovery_v2_78"]["other77_scripts_byte_exact"]
    assert fl["p0_round_epoch_role78"]["other77_sources_byte_exact"]
    assert fl["p0_spectator_h2_78"]["other76_byte_exact"]
    assert "p0_bot_unstuck78" not in fl and "p0_bot_unstuck78" not in sl
    newbot=patch_bot(prev[BOT].decode("utf8")).encode("utf8")
    after={**prev,BOT:newbot}
    assert {p for p in prev if after[p]!=prev[p]}=={BOT}
    pins={p:gitblob(v) for p,v in sorted(after.items())}
    receipt={"id":FEATURE,"author_pr":AUTHOR_PR,
      "only_existing_bot_module_changed":True,"other77_source_bytes_exact":True,
      "total_source_count":78,"new_game":False,"new_script_count":0,
      "new_remote_count":0,"new_feature_ids":0,
      "stalled_movement":"5S_3_5_STUD_JUMP_SIDE_STEP_7STUD_ALTERNATE",
      "inflight_path_limit":10,"no_teleport":True,
      "no_art_game_egg_hp_score_authority_change":True,
      "official_adoption":0,"owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
      "studio_physics":"NOT_TESTED","android":"NOT_TESTED",
      "rollback":"omit optional single-module unstuck overlay"}
    sl["blobs"]=pins;fl["source_gitblobs"]=pins
    sl["p0_bot_unstuck78"]=receipt;fl["p0_bot_unstuck78"]=receipt
    tmp=Path(tempfile.mkdtemp(prefix=".p0_ai_unstuck78_",dir=out.parent))
    stage=tmp/"dist"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/BOT).write_bytes(newbot)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins
        assert not out.exists()
        os.replace(stage,out)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
    assert read(base)==prev,"PARENT_PRIVATE78_MUTATED"
    print("P0_PRIVATE78_BOT_UNSTUCK_AUTHOR400_ONE_MODULE_LOCK_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
