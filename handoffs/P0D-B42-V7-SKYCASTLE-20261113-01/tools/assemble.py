#!/usr/bin/env python3
"""Build one real B42/V7 source game; switch only its existing world to authored SkyCastle."""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys
HERE=Path(__file__).resolve(); OWN=HERE.parents[1];REPO=HERE.parents[3]
BASE=REPO/"handoffs/P0D-FIRST90-MUSOUV7-UPGRADE-20261113-01"
OLD=BASE/"dist/EGG_RAID_RUMBLE_FIRST90_MUSOUV7_SINGLE_GAME_PRIVATE"
DIST=OWN/"dist/EGG_RAID_RUMBLE_FIRST90_V7_SKYCASTLE_PRIVATE"
ORIGINAL_WORLD_SHA256="a02291dbbc6204e6a898c9da2bf0abc9e2502b11275140bfdbd03061e0865cd6"
SKY_BLOB="0a6360392f4384dc2f0ab1e9afc1d840d66a22b8"
V7_HORDE="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
B42_GAME="21b866e801a53ba7ebd66132ae55fe28608750d6"
B42_HUD="ce6707dc1f833600e1c6913504d30911b24cb2a4"
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def scripts(root):
 return {p.relative_to(root/"src").as_posix():p.read_bytes()
         for p in sorted((root/"src").rglob("*.luau"))}
def main():
 assert not OLD.exists() and not DIST.exists(),"FAIL_CLOSED_NO_OVERWRITE"
 candidate=OWN/"src/H1FunWorld_SKY_CASTLE_TEST.server.luau"
 assert blob(candidate.read_bytes())==SKY_BLOB,"SKY_SOURCE_DRIFT"
 subprocess.run([sys.executable,"-B",str(BASE/"tools/assemble.py"),"--assemble"],cwd=REPO,check=True)
 old=scripts(OLD)
 assert len(old)==42
 assert {p for p in old if p.endswith(".server.luau")}=={
 "server/Game.server.luau","server/H1FunWorld.server.luau"}
 assert blob(old["server/Game.server.luau"])==B42_GAME
 assert blob(old["client/HUD.client.luau"])==B42_HUD
 assert blob(old["server/MusouHorde.luau"])==V7_HORDE
 assert hashlib.sha256(old["server/H1FunWorld.server.luau"]).hexdigest()==ORIGINAL_WORLD_SHA256,\
        "PRIVATE_WORLD_DRIFT"
 shutil.copytree(OLD,DIST)
 (DIST/"src/server/H1FunWorld.server.luau").write_bytes(candidate.read_bytes())
 current=scripts(DIST)
 assert len(current)==42 and sorted(old)==sorted(current)
 changes=sorted(k for k in old if old[k]!=current[k])
 assert changes==["server/H1FunWorld.server.luau"],changes
 assert all(current[p]==old[p] for p in old if p not in changes)
 assert blob(current["server/H1FunWorld.server.luau"])==SKY_BLOB
 game=current["server/Game.server.luau"].decode("utf8")
 sky=current["server/H1FunWorld.server.luau"].decode("utf8")
 assert game.count("remote.OnServerEvent:Connect(")==1
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 for x in ("First90GuideRules","First90WaypointRules","Evolution.nextEvolution(","Power.beginAwaken("):
  assert x in game,x
 assert sky.count('local world=Instance.new("Folder")')==1
 assert 'assert(not arena:FindFirstChild("H1_FUN_WORLD")' in sky
 assert "if not RunService:IsStudio() then" in sky
 for x in ("SKY_FORT_ENTRY_RED","SKY_FORT_ENTRY_BLUE","SKY_FORT_ESCAPE_RED","SKY_FORT_ESCAPE_BLUE"):
  assert 'path("'+x+'"' in sky,x
 assert "Vector3.new(0,28,49),rgb(103,194,151),true" in sky
 for forbidden in ('Instance.new("RemoteEvent")',"OnServerEvent:Connect(","DataStoreService","MarketplaceService","TeleportService"):
  assert forbidden not in sky,forbidden
 p=DIST/"default.project.json";doc=json.loads(p.read_text("utf8"))
 assert doc["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 doc["name"]="EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_UNPUBLISHED"
 p.write_text(json.dumps(doc,ensure_ascii=False,indent=2)+"\n","utf8")
 lock={"packet":"P0D-B42-V7-SKYCASTLE-20261113-01",
  "baseline_commit":"70714a081a555d716832bb6a640611e05a1f3eca",
  "sky_author_commit":"7a00fc1d90af10fa1c21473998496fc2b55c88d6",
  "sky_original_blob":SKY_BLOB,"V7_original_horde_blob":V7_HORDE,
  "original_source_count":42,"unchanged_source_count":41,
  "changed":["server/H1FunWorld.server.luau"],
  "single_server_Game":True,"one_Remote":True,
  "actual_studio_2client":"NOT_TESTED","android":"NOT_TESTED",
  "owner_fun":"NOT_TESTED","official_RC_adopted":False,
  "public_release":False,"paid":False,
  "source_blobs":{p:blob(b) for p,b in sorted(current.items())}}
 (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
 print("P0D_B42_V7_SKYCASTLE_ONE_GAME_42_SOURCE_41_UNCHANGED_PASS")
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--assemble",action="store_true",required=True)
 a.parse_args();main()
