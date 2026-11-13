#!/usr/bin/env python3
"""Immutable private H1 preview: B42 + V6 bridge -> V7 true-damage popup, ONE Horde swap.
No RC/main/other feature branch writes. Fail closed on all source drift.
"""
from __future__ import annotations
import argparse, hashlib, json, re, shutil, subprocess, sys
from pathlib import Path
HERE=Path(__file__).resolve()
OWN=HERE.parents[1];REPO=HERE.parents[3]
V6=REPO/"handoffs/P0D-FIRST90-MUSOUV6-BRIDGE-20261113-01"
OLD=V6/"dist/EGG_RAID_RUMBLE_FIRST90_MUSOUV6_SINGLE_GAME_PRIVATE"
DIST=OWN/"dist/EGG_RAID_RUMBLE_FIRST90_MUSOUV7_SINGLE_GAME_PRIVATE"
V6_HORDE="e67b186f08a0e9ca20d5f09a7c5b22205e2b7240"
V7_HORDE="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
V6_GAME="21b866e801a53ba7ebd66132ae55fe28608750d6"
V6_HUD="ce6707dc1f833600e1c6913504d30911b24cb2a4"
def gitblob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def scripts(root:Path)->dict[str,bytes]:
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}
def horde_api(b:bytes)->set[str]:
    return set(re.findall(r"function Horde[.:](\w+)\s*\(",b.decode("utf8")))
def main():
    assert not OLD.exists() and not DIST.exists(),"FAIL_CLOSED_NO_BUILD_OVERWRITE"
    source=OWN/"inputs/MusouHorde.luau"
    assert gitblob(source.read_bytes())==V7_HORDE,"V7_AUTHOR_SOURCE_DRIFT"
    assert gitblob((OWN/"inputs/MusouCombatRules.luau").read_bytes())=="7865af9fb057a368e146941ac5bd7bf89cddc88b"
    subprocess.run([sys.executable,"-B",str(V6/"tools/assemble.py"),"--assemble"],cwd=REPO,check=True)
    old=scripts(OLD)
    assert len(old)==42 and gitblob(old["server/MusouHorde.luau"])==V6_HORDE
    assert gitblob(old["server/Game.server.luau"])==V6_GAME
    assert gitblob(old["client/HUD.client.luau"])==V6_HUD
    assert horde_api(old["server/MusouHorde.luau"])==horde_api(source.read_bytes())
    shutil.copytree(OLD,DIST)
    (DIST/"src/server/MusouHorde.luau").write_bytes(source.read_bytes())
    new=scripts(DIST)
    assert len(new)==42 and sorted(old)==sorted(new)
    changes=[k for k in old if old[k]!=new[k]]
    assert changes==["server/MusouHorde.luau"],changes
    assert all(new[k]==old[k] for k in old if k not in changes)
    assert gitblob(new["server/MusouHorde.luau"])==V7_HORDE
    assert sum(k.endswith("/Game.server.luau") for k in new)==1
    assert sum(k.endswith(".server.luau") for k in new)==2
    assert sum(k.endswith(".client.luau") for k in new)==5
    game=new["server/Game.server.luau"].decode("utf8")
    mob=new["server/MusouHorde.luau"].decode("utf8")
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert "First90WaypointRules" in game and "First90GuideRules" in game
    assert "Evolution.nextEvolution(" in game and "Power.beginAwaken(" in game
    assert "if mobHits>0 then return end" in game
    assert "MUSOU_SOURCE_MAP_ARENA_REQUIRED" in mob
    assert "ELITE_SWEEP_DANGER_RADIUS" in mob
    assert 'Instance.new("BillboardGui")' in mob
    assert "m.popup" in mob and ".72" in mob
    assert 'Instance.new("RemoteEvent")' not in mob
    assert "DataStoreService" not in mob
    assert "MarketplaceService" not in mob
    project=DIST/"default.project.json"
    p=json.loads(project.read_text("utf8"))
    assert p["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    p["name"]="EGG_RAID_RUMBLE_FIRST90_MUSOUV7_UNPUBLISHED"
    project.write_text(json.dumps(p,ensure_ascii=False,indent=2)+"\n","utf8")
    lock={
      "packet_id":"P0D-FIRST90-MUSOUV7-UPGRADE-20261113-01",
      "base_v6_bridge_sha":"63442fb415d361855d72f5a15171f7cdd4a2486f",
      "original_b42_sha":"837853e66278e38bb79f6399c3e8bfc9a2403be6",
      "v7_source_author_sha":"76cc75b71f0a1a7a5a9976f14c10276c636493f2",
      "old_horde_blob":V6_HORDE,"new_horde_blob":V7_HORDE,
      "scripts_total":42,"modules_changed":["server/MusouHorde.luau"],
      "other_scripts_byte_exact":41,"server_game_count":1,"remote_count":1,
      "owner_studio_2client":"NOT_TESTED","android":"NOT_TESTED",
      "owner_fun":"NOT_TESTED","official_s1_rc_adopted":False,
      "private_unpublished":True,"robux_payment":False,
      "sha1_source_lock":{k:gitblob(v) for k,v in sorted(new.items())}
    }
    (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_B42_V7_42_SINGLE_GAME_SOURCE_ASSEMBLED_PASS")
if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--assemble",action="store_true",required=True)
    ap.parse_args()
    main()
