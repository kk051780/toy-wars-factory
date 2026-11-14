#!/usr/bin/env python3
"""P0 PRIVATE78 results-to-lobby recovery, same 78 scripts, Game-only source repair.

Source-level adaptation of authored #391. No extra Game, egg/HP authority,
feature ID, Remote, Store or main/official-branch write.
"""
from __future__ import annotations
import argparse, hashlib, json, os, shutil, tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob
GAME="server/Game.server.luau"
REPAIR="P0D_LOBBY_RESPAWN_FAIL"
AUTHORED_PR=391
BASE_RC="43543378f976374e2cac2d68b3136ac355d3191b"
OLD='''                        root.CFrame=LobbyIsland.spawn(team)
                    end'''
NEW='''                        root.CFrame=LobbyIsland.spawn(team)
                    elseif (team=="RED" or team=="BLUE") and p.Parent==Players then
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

def patch_game(source:str)->str:
    assert REPAIR not in source, "RESULTS_REPAIR_ALREADY_INSTALLED"
    assert source.count(OLD)==1,("RESULTS_RETURN_SOURCE_ANCHOR_DRIFT",source.count(OLD))
    assert source.count('-- Move real players to the separated lobby AFTER result display.')==1,"P0_RESULTS_LOBBY_OWNER_MISSING"
    assert source.count('remote.OnServerEvent:Connect(')==1,"P0_RESULTS_SINGLE_REMOTE"
    assert source.count('local function tickRound()')==1
    start=source.index('local function tickRound()')
    end=source.index('-- Recovery uses the existing server-only authoritative tick',start)
    section=source[start:end]
    assert section.count(OLD)==1
    assert 'elseif match.phase == "RESULTS" then' in section
    assert 'match.phase = "LOBBY"' in section
    assert 'LobbyIsland.spawn(team)' in section
    assert 'for _, player in ipairs(Players:GetPlayers()) do roundReady[player] = false end' in source, "RESULTS_READY_RESET_MISSING"
    after=source.replace(OLD,NEW,1)
    assert after.count(REPAIR)==1
    assert after.count('remote.OnServerEvent:Connect(')==1
    return after

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_PRIVATE78_RESULTS_OFF_ZERO_WRITE");return False
    base=base.absolute();out=out.absolute()
    assert out.parent.is_dir() and not out.exists(),"RESULTS_OUTPUT_ALREADY_EXISTS"
    assert base!=out and not out.is_relative_to(base) and not base.is_relative_to(out),"RESULTS_OUTPUT_OVERLAP"
    before=read(base)
    assert len(before)==78 and GAME in before,"RESULTS_REQUIRE_TRUE_PRIVATE78"
    lock=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    feats=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(v) for p,v in sorted(before.items())}
    assert lock["total_scripts"]==feats["total_sources"]==78
    assert lock["blobs"]==feats["source_gitblobs"]==pins
    assert feats["p0_motion78"]["source_count"]==78
    assert feats["p0_motion78"]["original77_byte_exact"]
    assert feats["p0_private77"]["official_base"]==BASE_RC
    assert feats["feature_flags"]["FB007_LOBBY_DOJO_PHYSICAL_V1"] is True
    assert "p0_results78" not in feats and "p0_results78" not in lock
    original=before[GAME].decode("utf8")
    amended=patch_game(original).encode("utf8")
    after={**before,GAME:amended}
    assert len(after)==78
    assert [p for p in before if before[p]!=after[p]]==[GAME]
    assert all(after[p]==before[p] for p in before if p!=GAME)
    pins78={p:gitblob(v) for p,v in sorted(after.items())}
    receipt={
        "id":"FB007_RESULTS_LOBBY_DEFEATED_PLAYER_RECOVERY_QA_V1",
        "authored_pr":AUTHORED_PR,
        "no_new_feature_id":True,
        "no_new_source":True,"total_sources":78,
        "patched":GAME,"other77_sources_exact":True,
        "parent78_unmodified":True,"formal_rc_adopted":False,
        "studio_engine":"NOT_TESTED","two_clients":"NOT_TESTED",
        "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
        "rollback":"omit private78 results patch; parent private78 is exact",
    }
    lock["blobs"]=pins78;feats["source_gitblobs"]=pins78
    lock["p0_results78"]=receipt;feats["p0_results78"]=receipt
    staging=Path(tempfile.mkdtemp(prefix=".p0d_results78_",dir=out.parent))
    stage=staging/"candidate"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(amended)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(feats,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==pins78
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==pins78
        assert not out.exists()
        os.replace(stage,out)
    finally:
        shutil.rmtree(staging,ignore_errors=True)
    assert read(base)==before,"RESULTS_PARENT78_MODIFIED"
    print("P0_PRIVATE78_DEFEATED_LOBBY_SOURCE_PINNED_GAME_ONLY_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",required=True,type=Path)
    p.add_argument("--out",required=True,type=Path)
    p.add_argument("--enabled",required=True,choices=("true","false"))
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
