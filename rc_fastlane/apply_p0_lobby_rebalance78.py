#!/usr/bin/env python3
"""FB-007 QA: keep team-balance teleports inside the physical lobby.

Exact private78 parent from #389 required. Separate private output; only one
existing Game source patched. No extra feature IDs or authority / official RC.
"""
from __future__ import annotations
import argparse, json, os, shutil, tempfile
from pathlib import Path
from apply_p0_motion78 import read,gitblob,BASE_RC

GAME="server/Game.server.luau"
FEATURE="FB007_LOBBY_REBALANCE_STAYS_IN_DOJO_QA_V1"
OLD='''                root.CFrame = map.teams[move.to].spawn + Vector3.new(0, 2, 0)'''
NEW='''                -- FB007 correction: during LOBBY a team-balance move must
                -- land on the selected TEAM'S separated lobby island.
                -- The original field spawn is valid only outside Studio.
                root.AssemblyLinearVelocity=Vector3.zero
                root.AssemblyAngularVelocity=Vector3.zero
                root.CFrame = if RunService:IsStudio()
                    then LobbyIsland.spawn(move.to)
                    else map.teams[move.to].spawn + Vector3.new(0, 2, 0)'''

def patch_game(src:str)->str:
    assert FEATURE not in src,"TEAM_REBALANCE_ALREADY_FIXED"
    assert src.count("local function rebalanceLobbyTeams()")==1
    assert src.count("local function assignSpawn(")==1
    head,rest=src.split("local function rebalanceLobbyTeams()",1)
    body,tail=rest.split("local function assignSpawn(",1)
    assert body.count(OLD)==1,("REBALANCE_FIELD_TELEPORT_SOURCE_DRIFT",body.count(OLD))
    assert 'if match.phase ~= "LOBBY" then return end' in body
    assert "local planned = LobbyTeamRecovery.plan(roster)" in body
    assert "dropEgg(player)" in body
    assert "player.Team = teamInstances[move.to]" in body
    assert "if alive and root then" in body
    assert 'LobbyIsland' in src and src.count('remote.OnServerEvent:Connect(')==1
    out=head+"local function rebalanceLobbyTeams()"+body.replace(OLD,NEW,1)+"local function assignSpawn("+tail
    assert out.count(FEATURE)==1
    assert out.count("local function resetRound()")==1
    assert out.count("local function tickRound()")==1
    assert out.count("remote.OnServerEvent:Connect(")==1
    assert out.count("local function rebalanceLobbyTeams()")==1
    return out

def apply(base:Path,out:Path,enabled:bool)->bool:
    if not enabled:
        print("P0_LOBBY_REBALANCE78_OFF_ZERO_WRITE")
        return False
    base=base.absolute();out=out.absolute()
    assert base.is_dir() and not base.is_symlink(),"LOBBY_REBALANCE_MISSING_78"
    assert out.parent.is_dir() and not out.exists() and not out.is_symlink(),"LOBBY_REBALANCE_BAD_OUTPUT"
    assert base!=out and not out.is_relative_to(base) and not base.is_relative_to(out),"LOBBY_REBALANCE_OVERLAP"
    before=read(base)
    assert len(before)==78 and GAME in before,"LOBBY_REBALANCE_REQUIRES_78"
    lock=json.loads((base/"SOURCE_LOCK.json").read_text("utf8"))
    fl=json.loads((base/"RC_FEATURE_LOCK.json").read_text("utf8"))
    pins={p:gitblob(v) for p,v in sorted(before.items())}
    assert lock["total_scripts"]==fl["total_sources"]==78
    assert lock["blobs"]==fl["source_gitblobs"]==pins
    assert fl["p0_private77"]["official_base"]==BASE_RC
    assert fl["p0_solo78"]["new_feature_count"]==0
    assert fl["feature_flags"]["FB007_LOBBY_DOJO_PHYSICAL_V1"] is True
    assert "p0_lobby_rebalance78" not in fl and "p0_lobby_rebalance78" not in lock
    patched=patch_game(before[GAME].decode("utf8")).encode("utf8")
    after={**before,GAME:patched}
    assert len(after)==78 and all(after[k]==before[k] for k in before if k!=GAME)
    receipt={"id":FEATURE,"fb":"FB-007","authored_game":"sole_existing_Game",
      "formal_feature_id_added":False,"new_scripts":0,"source_count":78,
      "original_77_other_sources_exact":True,"parent_78_untouched":True,
      "scope":"LOBBY balancing only; unchanged READY/round reset/real battle/game authority",
      "studio_solo":"NOT_TESTED","android":"NOT_TESTED",
      "owner_fun":"FUN_NO_GO","owner_art":"ART_NO_GO",
      "formal_rc_adopted":False,"rollback":"omit source-only private78 QA overlay"}
    newpins={p:gitblob(v) for p,v in sorted(after.items())}
    lock["blobs"]=newpins;fl["source_gitblobs"]=newpins
    lock["p0_lobby_rebalance78"]=receipt;fl["p0_lobby_rebalance78"]=receipt
    staging=Path(tempfile.mkdtemp(prefix=".p0d_lobby_rebalance78_",dir=str(out.parent)))
    stage=staging/"dist"
    try:
        shutil.copytree(base,stage,symlinks=False)
        (stage/"src"/GAME).write_bytes(patched)
        (stage/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
        (stage/"RC_FEATURE_LOCK.json").write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
        assert read(stage)==after
        assert json.loads((stage/"SOURCE_LOCK.json").read_text("utf8"))["blobs"]==newpins
        assert json.loads((stage/"RC_FEATURE_LOCK.json").read_text("utf8"))["source_gitblobs"]==newpins
        assert not out.exists()
        os.replace(stage,out)
    finally:
        shutil.rmtree(staging,ignore_errors=True)
    assert read(base)==before,"PARENT_PRIVATE78_MUTATED"
    print("P0_LOBBY_REBALANCE78_SINGLE_GAME_SOURCE_EXACT_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--base",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),required=True)
    a=p.parse_args()
    apply(a.base,a.out,a.enabled=="true")
