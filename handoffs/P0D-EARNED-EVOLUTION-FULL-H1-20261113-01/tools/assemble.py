#!/usr/bin/env python3
"""Reproduce actual existing H1 39-Luau game and overlay verified earned evolution.
Isolated unpublished private Studio source. Never mutates official RC/main/original packages.
"""
from __future__ import annotations
import sys,json,hashlib,subprocess,shutil,argparse
from pathlib import Path
HERE=Path(__file__).resolve()
OWN=HERE.parents[1]
REPO=HERE.parents[3]
BASE=REPO/"handoffs/P0D-MUSOU-EARNED-POWER-H1-20261113-01"
OLD=BASE/"dist/EGG_RAID_RUMBLE_MUSOU_EARNED_POWER_H1_PRIVATE_STUDIO_ONLY"
DIST=OWN/"dist/EGG_RAID_RUMBLE_EARNED_EVOLUTION_FULL_H1_PRIVATE_STUDIO_ONLY"
OVERRIDES={
 "server/Game.server.luau":("Game.server.luau","8b5fdf62f764ab6c963758d699cdfc681ed2ef96"),
 "client/HUD.client.luau":("HUD.client.luau","8c83efc18f63cea077de3dc3a8006bc11f05200c"),
 "server/PersistentHatchStore.luau":("PersistentHatchStore.luau","7e00a53e72479ffa643556ae5fe07c931f7507e7"),
 "server/MusouHorde.luau":("MusouHorde.luau","7edfda9e5a1d4ac8ae47d66ea7cf908eb8e4af6e"),
 "server/EvolutionRules.luau":("EvolutionRules.luau","0efca67b41e34917038fdc883c8ad34f3eb3c2e2"),
}
def gitblob(raw:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def read_scripts(root:Path)->dict[str,bytes]:
 return {p.relative_to(root/"src").as_posix():p.read_bytes()
  for p in sorted((root/"src").rglob("*.luau"))}
def assemble():
 assert not DIST.exists(),"FAIL_CLOSED_NO_DESTRUCTIVE_DIST_OVERWRITE"
 subprocess.run([sys.executable,"-B",str(BASE/"tools/assemble.py"),"--assemble"],
  cwd=REPO,check=True)
 old=read_scripts(OLD)
 assert len(old)==39,len(old)
 assert "server/PowerFantasyRules.luau" in old
 assert "server/MusouHorde.luau" in old
 assert old["server/PowerFantasyRules.luau"]==(BASE/"inputs"/"PowerFantasyRules.luau").read_bytes()
 assert gitblob(old["server/PowerFantasyRules.luau"])=="86e79877cf0e58603a4de67db29155bf98cc511d"
 for rel,(name,sha) in OVERRIDES.items():
  p=OWN/"inputs"/name
  assert p.is_file() and gitblob(p.read_bytes())==sha,("BLOB_DRIFT",rel,sha)
 shutil.copytree(OLD,DIST)
 for rel,(name,sha) in OVERRIDES.items():
  target=DIST/"src"/rel
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes((OWN/"inputs"/name).read_bytes())
 scripts=read_scripts(DIST)
 assert len(scripts)==40,len(scripts)
 assert sorted(set(scripts)-set(old))==["server/EvolutionRules.luau"]
 modified=sorted(k for k in old if old[k]!=scripts[k])
 assert modified==["client/HUD.client.luau","server/Game.server.luau",
  "server/MusouHorde.luau","server/PersistentHatchStore.luau"],modified
 assert all(old[k]==scripts[k] for k in old if k not in modified)
 assert len([k for k in scripts if k.endswith("/Game.server.luau")])==1
 assert len([k for k in scripts if k.endswith(".server.luau")])==2
 assert len([k for k in scripts if k.endswith(".client.luau")])==5
 game=scripts["server/Game.server.luau"].decode("utf8")
 hud=scripts["client/HUD.client.luau"].decode("utf8")
 store=scripts["server/PersistentHatchStore.luau"].decode("utf8")
 horde=scripts["server/MusouHorde.luau"].decode("utf8")
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert game.count("remote.OnServerEvent:Connect(")==1
 assert game.count("local function applyAttack(")==1
 assert game.count("local function tickRound(")==1
 assert game.count('Evolution.nextEvolution(')==2
 assert 'applyEvolveScout(player,data)' in game
 assert game.count("Power.beginAwaken(")==1
 assert '*earnedDamageMultiplier(player,"PLAYER")' in game
 assert 'local hits=horde:hit(anchor,currentRoot.CFrame.LookVector,' in game
 assert 'if not blocked then hum:TakeDamage(impact.damage) end' in game
 assert "m.attackAt=now+1.5 -- fair re-entry" in horde
 assert "MUSOU_SOURCE_MAP_ARENA_REQUIRED" in horde
 assert "if mobHits>0 then return end" in game
 assert "Evolution.creditRound(evo,data.id,round.objectiveEvents" in store
 assert "return store:UpdateAsync(key,function(original)" in store
 assert store.count("function Store.evolveTransition(")==1
 assert store.count("function Store.settleProgressTransition(")==1
 assert "PromptProductPurchase" not in game
 assert "EVOLVE_SCOUT" in hud and "AWAKEN_POWER" in hud
 assert hud.count("local seq = 0")==1
 project=DIST/"default.project.json"
 info=json.loads(project.read_text("utf8"))
 assert info["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 info["name"]="EGG_RAID_RUMBLE_REAL_EARNED_EVOLUTION_PRIVATE_STUDIO_ONLY"
 project.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n","utf8")
 lock={
  "packet_id":"P0D-EARNED-EVOLUTION-FULL-H1-20261113-01",
  "work_id":"p0d-siege-v19","game_id":"TRAP_RAIDERS",
  "initial_horde_baseline":"55ad13b45907a5a3e9deae7196a7c202a0672c0c",
  "latest_horde_v3_base":"1117513a27f66f44e0a2dbaa0e387812d2bc0c73",
  "power_baseline":"cb2540dc4a3e5b819c0e3598d4af5e2b6dca76d3",
  "pure_power_blob":"86e79877cf0e58603a4de67db29155bf98cc511d",
  "pure_evolution_blob":"0efca67b41e34917038fdc883c8ad34f3eb3c2e2",
  "luau_total":40,"original_game_sources":39,
  "original_unchanged":35,"original_modified":modified,
  "new_pure_modules":["server/EvolutionRules.luau"],
  "same_atomic_datastore":True,"existing_remote_count":1,
  "real_player_account_level":True,"real_owned_beast":True,
  "fake_evolution_levels":False,"live_Store_schema":1,
  "private_dev_datastore":True,"studio_only":True,
  "paid_power":False,"published":False,
  "official_rc_adopted":False,"actual_studio_tested":False,
  "android_tested":False,"human_fun":"FUN_NO_GO",
  "source_blob_sha1":{k:gitblob(v) for k,v in sorted(scripts.items())},
  "source_sha256":{k:hashlib.sha256(v).hexdigest() for k,v in sorted(scripts.items())}
 }
 (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
 print("P0D_REAL_EVOLUTION_FULL_SINGLE_GAME_40_LUAU_ASSEMBLY_PASS")
if __name__=="__main__":
 a=argparse.ArgumentParser()
 a.add_argument("--assemble",action="store_true",required=True)
 a.parse_args()
 assemble()
