#!/usr/bin/env python3
"""Build immutable first90 guided game from actual 40-Luau full H1, one Game one Remote."""
from __future__ import annotations
from pathlib import Path
import sys,subprocess,shutil,hashlib,json,argparse
HERE=Path(__file__).resolve()
OWN=HERE.parents[1];REPO=HERE.parents[3]
BASE=REPO/"handoffs/P0D-EARNED-EVOLUTION-FULL-H1-20261113-01"
OLD=BASE/"dist/EGG_RAID_RUMBLE_EARNED_EVOLUTION_FULL_H1_PRIVATE_STUDIO_ONLY"
DIST=OWN/"dist/EGG_RAID_RUMBLE_FIRST90_H1_PRIVATE_STUDIO_UNPUBLISHED"
OVERRIDES={
 "server/Game.server.luau":("Game.server.luau","71496d7ea8e84d79c2e7cf353012dacec365fba6"),
 "client/HUD.client.luau":("HUD.client.luau","58140a33da247dc582403b1b0638e3643ab797fe"),
 "server/MusouHorde.luau":("MusouHorde.luau","8c147c801e7fa1ff362922d66c9a6fd432fc8b6e"),
 "server/First90GuideRules.luau":("First90GuideRules.luau","644073946930d63e6b06c20ca249739b9ecfa5ad"),
}
def gitblob(data:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def scripts(root:Path):
 return {p.relative_to(root/"src").as_posix():p.read_bytes()
  for p in (root/"src").rglob("*.luau")}
def main():
 assert not DIST.exists(),"FAIL_CLOSED_DO_NOT_OVERWRITE"
 subprocess.run([sys.executable,"-B",str(BASE/"tools/assemble.py"),"--assemble"],cwd=REPO,check=True)
 original=scripts(OLD)
 assert len(original)==40 and gitblob(original["server/MusouHorde.luau"])=="7edfda9e5a1d4ac8ae47d66ea7cf908eb8e4af6e"
 for rel,(filename,sha) in OVERRIDES.items():
  raw=(OWN/"inputs"/filename).read_bytes()
  assert gitblob(raw)==sha,("SOURCE_BLOB_CHANGED",filename)
 shutil.copytree(OLD,DIST)
 for rel,(filename,sha) in OVERRIDES.items():
  target=DIST/"src"/rel;target.parent.mkdir(exist_ok=True,parents=True)
  target.write_bytes((OWN/"inputs"/filename).read_bytes())
 now=scripts(DIST)
 assert len(now)==41,len(now)
 assert sorted(set(now)-set(original))==["server/First90GuideRules.luau"]
 edits=sorted(k for k in original if original[k]!=now[k])
 assert edits==["client/HUD.client.luau","server/Game.server.luau","server/MusouHorde.luau"],edits
 assert all(now[k]==original[k] for k in original if k not in edits)
 assert len([k for k in now if k.endswith(".server.luau")])==2
 assert len([k for k in now if k.endswith(".client.luau")])==5
 g=now["server/Game.server.luau"].decode("utf8")
 h=now["client/HUD.client.luau"].decode("utf8")
 mob=now["server/MusouHorde.luau"].decode("utf8")
 assert g.count("remote.OnServerEvent:Connect(")==1
 assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert g.count("local function applyAttack(")==1
 assert g.count("local function tickRound(")==1
 assert g.count('First90Guide = require(script.Parent:WaitForChild("First90GuideRules"))')==1
 assert "First90Guide.mark(guideProgress[player],match.serial,\"HIT\",true)" in g
 assert "First90Guide.mark(guideProgress[player],match.serial,kind,true)" in g
 assert "First90Guide.mark(guideProgress[player],match.serial,\"SCOUT\",true)" in g
 assert "First90Guide.newRound(match.serial)" in g
 assert "MUSOU_SOURCE_MAP_ARENA_REQUIRED" in mob
 assert "ELITE_SWEEP_DANGER_RADIUS" in mob
 assert "horde:eliteWarningSeconds(now)" in g
 assert "赤い円の外へ" in h
 assert "First90RealObjectiveGuide" in h
 assert "if mobHits>0 then return end" in g
 assert "Power.beginAwaken(" in g and "Evolution.nextEvolution(" in g
 assert "PromptProductPurchase" not in g
 proj=DIST/"default.project.json"
 info=json.loads(proj.read_text("utf8"))
 assert info["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 info["name"]="EGG_RAID_RUMBLE_FIRST90_GUIDED_41_PRIVATE_STUDIO_UNPUBLISHED"
 proj.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n","utf8")
 lock={
  "packet_id":"P0D-FIRST90-GUIDED-H1-20261113-01",
  "source_parent_full_40":"1b21bf8e5fc6afa5c74813d7f1037f877e1273ed",
  "source_latest_horde_v5":"adb1150951c5b5a6221f71204ce91ea693e34847",
  "original_unchanged":37,"original_changed":edits,
  "source_count":41,"new_pure_policy":["server/First90GuideRules.luau"],
  "one_server_game":True,"one_remote":True,
  "first90_certified_server_only":True,
  "studio_only":True,"published":False,"paid":False,
  "official_rc_adopted":False,"roblox_studio_2client_tested":False,
  "android_tested":False,"human_FUN":"FUN_NO_GO",
  "source_blob_sha1":{k:gitblob(v) for k,v in sorted(now.items())}
 }
 (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
 print("P0D_FIRST90_41_LUAU_REAL_SINGLE_GAME_ASSEMBLED_PASS")
if __name__=="__main__":
 a=argparse.ArgumentParser();a.add_argument("--assemble",action="store_true",required=True)
 a.parse_args();main()
