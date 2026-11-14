#!/usr/bin/env python3
"""P0 FB006 author #393 robust results/spectator respawn in cumulative PRIVATE78.

Exact author helper is extracted from immutable Git source; sole existing Game
is amended, 77 other Luau are byte identical. Nothing writes canonical RC.
"""
from __future__ import annotations
import argparse,json,os,shutil,tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob,BASE_RC

ROOT=Path(__file__).resolve().parent
AUTHOR=ROOT/"features/p0_recovery_v2_78/qa_firstplay_p0_AUTHOR393.py"
AUTHOR_BLOB="b0bad82c454d851dc5071b04c0abfae32c7a455c"
GAME="server/Game.server.luau"
ID="FB006_RESULTS_SPECTATOR_SAFE_RESPAWN_V2_QA"
RESULTS_OLD='''                    elseif (team=="RED" or team=="BLUE") and p.Parent==Players then
                        -- #391 authored Game recovery: the existing CharacterAdded
                        -- handler places this player on the physical lobby island.
                        task.defer(function()
                            if p.Parent~=Players or match.phase~="LOBBY" then return end
                            local refreshed=healthy(p)
                            if not refreshed then
                                local ok,err=pcall(function() p:LoadCharacter() end)
                                if not ok then warn("P0D_LOBBY_RESPAWN_FAIL",err) end
                            end
                        end)
                    end'''
RESULTS_NEW='''                    elseif (team=="RED" or team=="BLUE"
                        or p:GetAttribute("P0D_LateJoinSpectator")==true)
                        and p.Parent==Players then
                        scheduleLobbyRecovery(p)
                    end'''
OBSERVER_OLD='''                    else
                        task.defer(function()
                            if entrant.Parent==Players and match.phase=="LOBBY"
                                and not healthy(entrant) then
                                local loaded,err=pcall(function() entrant:LoadCharacter() end)
                                if not loaded then warn("FB005_SPECTATOR_PROMOTION_LOAD_FAIL",err) end
                            end
                        end)
                    end'''
OBSERVER_NEW='''                    else
                        scheduleLobbyRecovery(entrant)
                    end'''

def author_helper()->str:
    raw=AUTHOR.read_bytes()
    assert gitblob(raw)==AUTHOR_BLOB, "AUTHOR393_SOURCE_GIT_BLOB_MISMATCH"
    src=raw.decode("utf8")
    assert src.count('    recovery = """')==1
    part=src.split('    recovery = """',1)[1].split('"""',1)[0]
    for phrase in ('local function scheduleLobbyRecovery(player: Player)',
        'Players.CharacterAutoLoads','Players.RespawnTime',
        'player.Character~=originalCharacter','number < 3','task.delay(2,',
        'local lobbyRecoveryPending: {[Player]: boolean} = {}'):
        assert phrase in part, ("AUTHOR393_RESPAWN_CONTRACT_DRIFT",phrase)
    for forbidden in ('Instance.new("RemoteEvent")','OnServerEvent:Connect(',
                      'DataStoreService','FireServer(', 'MarketplaceService'):
        assert forbidden not in part
    return part

def one_region(src:str, start:str,end:str,old:str,new:str)->str:
    assert src.count(start)==1,(start,src.count(start))
    i=src.index(start)
    j=src.index(end,i+len(start))
    body=src[i:j]
    assert body.count(old)==1,("RECOVERY_V2_UNEXPECTED_TARGET",old[:90],body.count(old))
    return src[:i]+body.replace(old,new,1)+src[j:]

def patch_game(src:str)->str:
    assert 'local function scheduleLobbyRecovery(' not in src, "RECOVERY_DUPLICATED"
    assert src.count('P0D_LOBBY_RESPAWN_FAIL')==1
    assert src.count('P0D_LateJoinSpectator')>=4,"SPECTATOR_PARENT_MISSING"
    assert src.count('remote.OnServerEvent:Connect(')==1
    assert src.count('local function tickRound()')==1
    src=one_region(src,
        'elseif match.phase == "RESULTS" then',
        '-- Recovery uses the existing server-only authoritative tick',
        RESULTS_OLD,RESULTS_NEW)
    src=one_region(src,
        'if match.phase == "LOBBY" then',
        '    elseif match.phase == "COUNTDOWN" then',
        OBSERVER_OLD,OBSERVER_NEW)
    assert src.count('local function tickRound()')==1
    src=src.replace('local function tickRound()',author_helper()+'local function tickRound()',1)
    assert src.count('local function scheduleLobbyRecovery(')==1
    assert src.count('scheduleLobbyRecovery(p)')==1
    assert src.count('scheduleLobbyRecovery(entrant)')==1
    assert 'P0D_LOBBY_RESPAWN_FAIL"' not in src
    assert src.count('remote.OnServerEvent:Connect(')==1
    return src

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_PRIVATE78_RECOVERY_V2_OFF_ZERO_WRITE")
        return False
    base=base.absolute();out=out.absolute()
    assert base.is_dir() and not base.is_symlink(),"RECOVERY_V2_MISSING_PARENT"
    assert out.parent.is_dir() and not out.exists() and not out.is_symlink()
    assert base!=out and not base.is_relative_to(out) and not out.is_relative_to(base)
    before=read(base)
    assert len(before)==78 and GAME in before
    sl=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(b) for p,b in sorted(before.items())}
    assert sl["total_scripts"]==fl["total_sources"]==78
    assert sl["blobs"]==fl["source_gitblobs"]==pins
    assert fl["p0_private77"]["official_base"]==BASE_RC
    assert fl["p0_spectator_h2_78"]["other76_byte_exact"]
    assert fl["p0_lobby_rebalance78"]["original_77_other_sources_exact"]
    assert fl["p0_solo78"]["new_feature_count"]==0
    assert "p0_recovery_v2_78" not in fl and "p0_recovery_v2_78" not in sl
    after={**before,GAME:patch_game(before[GAME].decode("utf8")).encode("utf8")}
    assert {p for p in before if before[p]!=after[p]}=={GAME}
    pins78={p:gitblob(b) for p,b in sorted(after.items())}
    receipt={"id":ID,"author_pr":393,"author_source_blob":AUTHOR_BLOB,
      "game_only_changed":True,"other77_scripts_byte_exact":True,
      "count":78,"additional_feature_ids":0,"new_remote":False,
      "auto_respawn":"CHARACTER_AUTOLOADS_RESPAWN_TIME_PLUS_GRACE",
      "manual_retry":"MAX_3_FAILURE_AWARE_ATTEMPTS",
      "spectator_promotion":"SAME_SAFE_SCHEDULER",
      "studio":"NOT_TESTED","two_client":"NOT_TESTED","android":"NOT_TESTED",
      "owner_art":"ART_NO_GO","owner_fun":"FUN_NO_GO","official_adoption":0,
      "rollback":"omit isolated recovery_v2 overlay"}
    sl["blobs"]=pins78;fl["source_gitblobs"]=pins78
    sl["p0_recovery_v2_78"]=receipt;fl["p0_recovery_v2_78"]=receipt
    tmp=Path(tempfile.mkdtemp(prefix=".p0_recovery_v2_",dir=out.parent))
    stage=tmp/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(after[GAME])
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins78
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins78
        assert not out.exists()
        os.replace(stage,out)
    finally:
        shutil.rmtree(tmp,ignore_errors=True)
    assert read(base)==before
    print("P0_PRIVATE78_RECOVERY_V2_AUTHORED_GAME_ONLY_SOURCE_LOCK_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    args=p.parse_args()
    apply(args.base,args.out,args.enabled=="true")
