#!/usr/bin/env python3
"""Make ONE full original H1 Game with 2 modes, owned scout, and DEV DataStore writes.
This source build never calls Roblox DataStore or publishes any game; generated
Place is exclusively for owner's privately API-enabled Studio test.
"""
from pathlib import Path
import hashlib,shutil,json,subprocess,sys,argparse
HERE=Path(__file__).resolve();REPO=HERE.parents[3];OWN=HERE.parents[1]
UP=REPO/"handoffs/P0D-EGG-RUMBLE-REAL-SCOUT-20261113-01"
UP_DIST=UP/"dist/EGG_RAID_RUMBLE_FREE_HATCH_EQUIP_REAL_3D_SCOUT_PRIVATE_STUDIO"
DST=OWN/"dist/EGG_RAID_RUMBLE_TWO_MODES_FREE_HATCH_DATASTORE_PRIVATE_STUDIO"
PIN={
 "server/Game.server.luau":"9f98dc057b782413982580674139879c2966d0e2",
 "client/HUD.client.luau":"25cd101691eff366158c7bd76f6ddda1f3655c46",
 "server/PersistentHatchStore.luau":"47541bdc4f28516d6edcec6624890bcae88bde32"
}
def gitblob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def source(root):
 return {p.relative_to(root/"src").as_posix():p.read_bytes()
         for p in sorted((root/"src").rglob("*.luau"))}
def assemble():
 subprocess.run([sys.executable,"-B",str(UP/"tools/assemble.py"),"--assemble"],check=True,cwd=REPO)
 baseline=source(UP_DIST)
 assert len(baseline)==33,len(baseline)
 for path,sha in PIN.items():
  inp=OWN/"inputs"/Path(path).name
  assert inp.is_file(),inp
  assert gitblob(inp.read_bytes())==sha,(path,gitblob(inp.read_bytes()),sha)
 if DST.exists():shutil.rmtree(DST)
 shutil.copytree(UP_DIST,DST)
 for path in PIN:
  target=DST/"src"/path
  target.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(OWN/"inputs"/Path(path).name,target)
 proj=DST/"default.project.json"
 meta=json.loads(proj.read_text(encoding="utf-8"))
 assert meta["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 meta["name"]="EGG_RAID_RUMBLE_TWO_MODES_DURABLE_HATCH_STUDIO_QA_DO_NOT_PUBLISH"
 proj.write_text(json.dumps(meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 rendered=source(DST)
 assert len(rendered)==34,len(rendered)
 assert sorted(set(rendered)-set(baseline))==["server/PersistentHatchStore.luau"]
 assert sorted(k for k in baseline if baseline[k]!=rendered[k])==[
  "client/HUD.client.luau","server/Game.server.luau"]
 assert all(baseline[k]==rendered[k] for k in baseline if k not in
            ("client/HUD.client.luau","server/Game.server.luau"))
 assert all(gitblob(rendered[k])==sha for k,sha in PIN.items())
 assert len([k for k in rendered if k.endswith(".server.luau")])==2
 assert len([k for k in rendered if k.endswith(".client.luau")])==5
 assert [k for k in rendered if k.endswith("/Game.server.luau")]==["server/Game.server.luau"]
 assert gitblob(rendered["server/RewardEquipRules.luau"])=="0edf0993e41785b1e206b6ad09955a9984a346e5"
 assert gitblob(rendered["server/H2FiveEggRules.luau"])=="0999d69391c176b9b95b04c5444d822e63d7ce04"
 game=rendered["server/Game.server.luau"].decode("utf-8")
 hud=rendered["client/HUD.client.luau"].decode("utf-8")
 pure=rendered["server/PersistentHatchStore.luau"].decode("utf-8")
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert game.count('remote.OnServerEvent:Connect(')==1
 assert game.count('PersistentHatch.grant(')==1
 assert game.count('PersistentHatch.equip(')==1
 assert game.count('PersistentHatch.load(')==1
 assert 'DataStoreService:GetDataStore("EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1")' in game
 assert 'DataStoreGetOptions.new()' in game
 assert 'hatchSaveStatus = persistenceState[player] or "LOCAL_ONLY"' in game
 assert 'hatchSaved = persistenceState[player]=="SAVED"' in game
 assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in game
 assert 'local function spawnActualScout(' in game
 assert 'RewardRules.finishRound(rewardState,match.serial,eligible,rare)' in game
 assert 'if p.receipts[epoch] then return true, p.receipts[epoch], "ALREADY_GRANTED" end' in rendered["server/RewardEquipRules.luau"].decode()
 assert 'function Store.grant(' in pure and 'store:UpdateAsync(key,function(original)' in pure
 assert 'store:GetAsync(key,options)' in pure
 assert 'SetAsync(' not in pure
 assert not any("task.wait(" in line.split("--",1)[0] for line in pure.splitlines())
 assert hud.count('local seq = 0')==1 and hud.count('remote:FireServer(')==3
 assert 'ActualSaveStatus' in hud and 'SAVE_FAILED' in hud and 'LOCAL_ONLY' in hud
 rec={
  "game":"EGG RAID RUMBLE","internal_id":"TRAP_RAIDERS",
  "baseline_full_game_fixed_SHA":"6274b38ed13079a97cf3b53d634f815649f6be13",
  "complete_actual_Luau_count":34,
  "unchanged_prior_original_scripts":31,
  "overlays":["server/Game.server.luau","client/HUD.client.luau"],
  "new_pure_server_module":"server/PersistentHatchStore.luau",
  "old_first_beast_rules_byte_exact":True,
  "one_original_Game":True,
  "one_original_S1_Remote":True,
  "both_game_modes_preserved":True,
  "DataStore_actual_GetAsync_UpdateAsync_code":True,
  "DEV_DATASTORE_NAME":"EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1",
  "Studio_API_access_must_be_enabled_by_owner":True,
  "real_Studio_API_save_reconnect_verified":False,
  "actual_Studio_two_clients_verified":False,"Android_verified":False,
  "actual_FUN_gate_accepted":False,"published":False,"paid":False,
  "other_5_collection_categories_implemented":False,
  "record_limit":"2048 receipts per owner; fails closed and needs migration",
  "actual_source_gitblobs":{k:gitblob(v) for k,v in rendered.items()}
 }
 (DST/"SOURCE_LOCK.json").write_text(json.dumps(rec,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("EGG_RUMBLE_FULL_ORIGINAL_2_MODE_GAME_34_LUAU_PERSISTENT_STORE_SOURCE_LOCK_PASS")
 return rec
if __name__=="__main__":
 parser=argparse.ArgumentParser()
 parser.add_argument("--assemble",required=True,action="store_true")
 parser.parse_args()
 assemble()
