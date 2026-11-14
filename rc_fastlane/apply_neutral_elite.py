#!/usr/bin/env python3
"""P0D-017: add pure giant/dragon policy to EXACT existing original Game-Horde pair.
Use only after official RC66 assembly; never writes official/main refs.
OFF mode has zero writes. Only original Horde may write impact list to Game.
"""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
KEY="P0D_017_NEUTRAL_ELITE_BOSS_V1"
HORDE="server/MusouHorde.luau"
MODULE="server/NeutralElitePhasePolicy.luau"
ORIGINAL_HORDE="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
PATCHED_HORDE="8852f8034d1faa068647924edafc6fb9fc00dff7"
POLICY_BLOB="9f8d805b866216cdd62c4820c8264f9fd6ed4d69"
SOURCE_HORDE=ROOT/"features/neutral_elite/MusouHordeBossed.luau"
SOURCE_POLICY=ROOT/"features/neutral_elite/NeutralElitePhasePolicy.luau"
def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+bytes([0])+raw).hexdigest()
def collect(d:Path)->dict[str,bytes]:
    return {x.relative_to(d/"src").as_posix():x.read_bytes() for x in sorted((d/"src").rglob("*.luau"))}
def apply(dist:Path,enabled:bool|None=None)->bool:
    flags=json.loads((ROOT/"FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    cfg=flags[KEY]
    on=cfg["enabled"] if enabled is None else enabled
    assert type(on) is bool
    if not on:
        print("P0D_017_OFF_PRESERVES_CANONICAL66_ALL_BYTES_PASS")
        return False
    assert cfg["official_rc_adopted"] is False
    assert cfg["policy_git_blob"]==POLICY_BLOB and cfg["horde_git_blob"]==PATCHED_HORDE
    before=collect(dist)
    assert len(before)==66,("EXACT_RC66_REQUIRED",len(before))
    assert HORDE in before and MODULE not in before
    assert blob(before[HORDE])==ORIGINAL_HORDE,("ORIGINAL_HORDE_DRIFT",blob(before[HORDE]))
    assert blob(SOURCE_HORDE.read_bytes())==PATCHED_HORDE
    assert blob(SOURCE_POLICY.read_bytes())==POLICY_BLOB
    assert b'local ElitePhase=require(script.Parent:WaitForChild("NeutralElitePhasePolicy"))' in SOURCE_HORDE.read_bytes()
    assert b'ElitePhase.step(boss,self.round,now,targetDistance,bossVisible,true)' in SOURCE_HORDE.read_bytes()
    assert b'table.insert(impacts,{player=bossTarget,' in SOURCE_HORDE.read_bytes()
    original_game=before["server/Game.server.luau"]
    if b'horde:tick(' not in original_game or b'horde:hit(' not in original_game:
        raise AssertionError("NO_EXISTING_SINGLE_HORDE_GAME_AUTHORITY")
    for banned in (b'Instance.new("RemoteEvent")',b'DataStoreService',b'UpdateAsync(',b'MarketplaceService',b'OnServerEvent:Connect('):
        assert banned not in SOURCE_POLICY.read_bytes() and banned not in SOURCE_HORDE.read_bytes(),banned
    lock_file=dist/"SOURCE_LOCK.json"
    feat_file=dist/"RC_FEATURE_LOCK.json"
    project_file=dist/"default.project.json"
    lock=json.loads(lock_file.read_text("utf8"))
    feat=json.loads(feat_file.read_text("utf8"))
    assert lock["total_scripts"]==66 and feat["total_sources"]==66
    oldpins={z:blob(raw) for z,raw in sorted(before.items())}
    assert lock["blobs"]==oldpins and feat["source_gitblobs"]==oldpins
    assert (dist/"src"/MODULE).exists() is False
    assert json.loads(project_file.read_text("utf8"))["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    # No write performed before ALL source/lock preflight checks.
    (dist/"src"/HORDE).write_bytes(SOURCE_HORDE.read_bytes())
    (dist/"src"/MODULE).write_bytes(SOURCE_POLICY.read_bytes())
    after=collect(dist)
    assert len(after)==67 and all(after[z]==raw for z,raw in before.items() if z!=HORDE)
    assert after["server/Game.server.luau"]==original_game
    newpins={z:blob(raw) for z,raw in sorted(after.items())}
    for item in (lock,feat):
        item["blobs" if "blobs" in item else "source_gitblobs"]=newpins
        item["total_scripts" if "total_scripts" in item else "total_sources"]=67
        item["rc_neutral_elite_overlay"]={
          "id":KEY,"new_module":MODULE,"replaced_module":HORDE,
          "horde_original_gitblob":ORIGINAL_HORDE,"horde_boss_gitblob":PATCHED_HORDE,
          "pure_policy_gitblob":POLICY_BLOB,
          "original_other65_source_bytes_preserved":True,
          "only_one_horde_hit_and_game_owner":True,
          "owner_fun":"NOT_TESTED","engine_2client":"NOT_TESTED",
          "official_rc_adopted":False,
        }
    feat["feature_flags"][KEY]=True
    lock_file.write_text(json.dumps(lock,indent=2,ensure_ascii=False)+"\n","utf8")
    feat_file.write_text(json.dumps(feat,indent=2,ensure_ascii=False)+"\n","utf8")
    assert collect(dist)==after
    print("P0D_017_ORIGINAL_HORDE_PLUS_PURE_BOSS_PHASE_SOURCE67_SINGLE_AUTHORITY_PASS")
    return True
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--dist",required=True)
    ap.add_argument("--enabled",choices=["true","false"],required=True)
    args=ap.parse_args()
    apply(Path(args.dist),args.enabled=="true")
