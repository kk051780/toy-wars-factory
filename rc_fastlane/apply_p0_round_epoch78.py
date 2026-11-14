#!/usr/bin/env python3
"""P0 independent QA child: race-proof resetRound epoch and spectator role denial.

Input: full PRIVATE78 after #393 robust lobby recovery; 78 native Luau.
Patch ONLY existing Game. Canonical RC/main/parents are never mutated.
"""
from __future__ import annotations
import argparse,json,os,shutil,tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob,BASE_RC

GAME="server/Game.server.luau"
FEATURE="FB005_PRIVATE78_ROUND_EPOCH_SPECTATOR_ROLE_QA"
EPOCH_GUARD='''    -- FB005_PRIVATE78_ROUND_EPOCH_SPECTATOR_ROLE_QA: LoadCharacter may yield.
    -- A leaver can end the match during that yield; do not revive objectives
    -- or start the canonical round after a RESULT or newer match serial.
    if match.phase~="ACTIVE" or match.serial~=startupSerial then return end
'''
ROLE_GUARD='''    -- A Studio late-join observer has no role selection authority.
    -- Guard BEFORE the shared input sequence ceiling is consumed.
    if player:GetAttribute("P0D_LateJoinSpectator")==true then return end
    local side=getTeamName(player)
    if side~="RED" and side~="BLUE" then return end
'''
PROMOTION='''                    roles[entrant]="RAIDER"
                    lastRoleChange[entrant]=-math.huge
'''

def patch_region(s:str,start:str,end:str,fn)->str:
    assert s.count(start)==1,("BOUNDARY_START_DRIFT",start,s.count(start))
    head,part=s.split(start,1)
    assert end in part,("BOUNDARY_END_DRIFT",end)
    content,tail=part.split(end,1)
    return head+start+fn(content)+end+tail

def one(s:str,a:str,b:str)->str:
    assert s.count(a)==1,("PINNED_AUTHORED_FRAGMENT_DRIFT",a[:120],s.count(a))
    return s.replace(a,b,1)

def patch_game(src:str)->str:
    assert FEATURE not in src, "EPOCH_ROLE_QA_ALREADY_APPLIED"
    assert src.count("remote.OnServerEvent:Connect(")==1
    assert src.count("local function resetRound()")==1
    assert src.count("local function applyRole(player: Player, data)")==1
    assert src.count('local function scheduleLobbyRecovery(')==1,"MUST_START_AFTER_ROBUST_393"
    assert 'P0D_LateJoinSpectator' in src and 'LOBBY_REBALANCE_STAYS_IN_DOJO' in src

    def reset(body:str)->str:
        # Freeze this exact serial before any Player:LoadCharacter (yielding)
        # and stop safely if an H2 leaver moved the current match to RESULTS.
        body=one(body,'    match.serial += 1\n',
            '    match.serial += 1\n    local startupSerial=match.serial\n')
        start=body.index("    for _, p in ipairs(Players:GetPlayers()) do")
        stop=body.index("    for _, team in ipairs({\"RED\", \"BLUE\"}) do",start)
        assert "p:LoadCharacter()" in body[start:stop],"ROUND_LOADING_FRAGMENT_DRIFT"
        body=body[:stop]+EPOCH_GUARD+body[stop:]
        assert body.index("p:LoadCharacter()")<body.index(EPOCH_GUARD)
        assert body.index(EPOCH_GUARD)<body.index("setObjectiveEnabled(true)")
        assert body.index(EPOCH_GUARD)<body.index("startCanonical()")
        return body
    src=patch_region(src,"local function resetRound()","local function chooseTeam(",reset)

    def role(body:str)->str:
        # The wide body also contains other handlers with their own replay
        # ceilings. Split at applyRole's first function-closing end so ONLY
        # spectator ROLE authority changes, never ATTACK/TRAP/MAGIC logic.
        assert '\nend\n' in body, "APPLY_ROLE_FIRST_END_MISSING"
        role_only,others=body.split('\nend\n',1)
        role_only=one(role_only,
            '    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end\n',
            ROLE_GUARD+'    if not Rules.validSeq(data.seq, lastSeq[player] or 0) then return end\n')
        return role_only+'\nend\n'+others
    src=patch_region(src,"local function applyRole(player: Player, data)",
        "remote.OnServerEvent:Connect(function(player: Player, data)",role)

    def lobby(body:str)->str:
        anchor='''                    chooseTeam(entrant)
                    roundReady[entrant]=false'''
        replacement='''                    chooseTeam(entrant)
'''+PROMOTION+'''                    roundReady[entrant]=false'''
        return one(body,anchor,replacement)
    src=patch_region(src,'local function tickRound()','    elseif match.phase == "COUNTDOWN" then',lobby)

    assert src.count(FEATURE)==1
    assert src.count("local function resetRound()")==1
    assert src.count('local function scheduleLobbyRecovery(')==1
    assert src.count("remote.OnServerEvent:Connect(")==1
    assert src.count('local function applyRole(')==1
    return src

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_ROUND_EPOCH_ROLE_OFF_ZERO_WRITE");return False
    base=base.absolute();out=out.absolute()
    assert base.is_dir() and not base.is_symlink(),"MISSING_PRIVATE78_RECOVERY_V2"
    assert out.parent.is_dir() and not out.exists() and not out.is_symlink(),"NEW_PRIVATE_OUTPUT_REQUIRED"
    assert base!=out and not base.is_relative_to(out) and not out.is_relative_to(base),"PATH_OVERLAP"
    original=read(base)
    assert GAME in original and len(original)==78,"EXPECTED_ALL_78_SOURCE_SCRIPTS"
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    originalPins={p:gitblob(b) for p,b in sorted(original.items())}
    assert sl["total_scripts"]==fl["total_sources"]==78
    assert sl["blobs"]==fl["source_gitblobs"]==originalPins
    assert fl["p0_private77"]["official_base"]==BASE_RC
    assert fl["p0_recovery_v2_78"]["other77_scripts_byte_exact"]
    assert fl["p0_spectator_h2_78"]["other76_byte_exact"]
    assert "p0_round_epoch_role78" not in fl and "p0_round_epoch_role78" not in sl
    revised=patch_game(original[GAME].decode("utf8")).encode("utf8")
    result={**original,GAME:revised}
    assert {p for p in original if original[p]!=result[p]}=={GAME}
    pins={p:gitblob(b) for p,b in sorted(result.items())}
    receipt={"id":FEATURE,"original_source":"ONE_S1_GAME",
      "preserved_private78_parent":True,"other77_sources_byte_exact":True,
      "scripts":78,"new_scripts":0,"new_feature_ids":0,
      "sole_change":"ROUND_START_SERIAL_GUARD_AND_OBSERVER_ROLE_AUTH",
      "role":"DENY_FLAGGED_AND_NON_FIGHTER_BEFORE_SEQ",
      "role_promotion":"RESET_RAIDER_AND_COOLDOWN",
      "round_start":"ABORT_IF_RESULTS_OR_DIFFERENT_MATCH_AFTER_CHARACTER_YIELD",
      "official_adoption":0,"owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
      "studio_physics":"NOT_TESTED","android":"NOT_TESTED",
      "rollback":"omit private QA overlay"}
    sl["blobs"]=pins;fl["source_gitblobs"]=pins
    sl["p0_round_epoch_role78"]=receipt;fl["p0_round_epoch_role78"]=receipt
    stageparent=Path(tempfile.mkdtemp(prefix=".p0_epoch_role78_",dir=str(out.parent)))
    stage=stageparent/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(revised)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==result
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins
        assert not out.exists()
        os.replace(stage,out)
    finally:
        shutil.rmtree(stageparent,ignore_errors=True)
    assert read(base)==original,"PARENT_PRIVATE78_MUTATED"
    print("P0_PRIVATE78_ROUND_EPOCH_ROLE_ONE_GAME_GUARDED_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
