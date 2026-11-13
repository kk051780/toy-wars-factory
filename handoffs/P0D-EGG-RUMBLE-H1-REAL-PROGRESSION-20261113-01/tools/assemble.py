#!/usr/bin/env python3
"""Full original EGG RAID RUMBLE 2-mode real H1 game + #281 exact progression.
Native/Rojo Studio source build only. NEVER publish/merge official sole RC.
"""
from pathlib import Path
import hashlib,sys,subprocess,shutil,json,argparse
HERE=Path(__file__).resolve();REPO=HERE.parents[3];OWN=HERE.parents[1]
BASE=REPO/"handoffs/P0D-EGG-RUMBLE-DURABLE-HATCH-20261113-01"
OLD=BASE/"dist/EGG_RAID_RUMBLE_TWO_MODES_FREE_HATCH_DATASTORE_PRIVATE_STUDIO"
NEW=OWN/"dist/EGG_RAID_RUMBLE_H1_TWO_MODES_XP_MASTERY_DEV_STUDIO_ONLY"
PIN={
"server/Game.server.luau":"28a51605efcee572029154f978761622959df587",
"client/HUD.client.luau":"6ef75cc76002e14b00cfb984cc799098e5cd033a",
"server/PersistentHatchStore.luau":"7205035fa710bfa1e2a629aa9f093b9ddb8fcb9d",
"server/ProgressionRules.luau":"a72830b039a46ca02d02f6aab7d6a4805bec8860"
}
def blob(raw):return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def src(root):return {p.relative_to(root/"src").as_posix():p.read_bytes() for p in sorted((root/"src").rglob("*.luau"))}
def build():
 subprocess.run([sys.executable,"-B",str(BASE/"tools/assemble.py"),"--assemble"],check=True,cwd=REPO)
 old=src(OLD)
 assert len(old)==34,len(old)
 for rel,sha in PIN.items():
  path=OWN/"inputs"/Path(rel).name
  assert path.is_file() and blob(path.read_bytes())==sha,(rel,sha)
 if NEW.exists():shutil.rmtree(NEW)
 shutil.copytree(OLD,NEW)
 for rel in PIN:
  to=NEW/"src"/rel;to.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(OWN/"inputs"/Path(rel).name,to)
 project=NEW/"default.project.json"
 data=json.loads(project.read_text(encoding="utf-8"))
 assert data["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 data["name"]="EGG_RAID_RUMBLE_H1_TWO_MODES_XP_MASTERY_DEV_STUDIO_UNPUBLISHED"
 project.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 all=src(NEW)
 assert len(all)==35,len(all)
 assert sorted(set(all)-set(old))==["server/ProgressionRules.luau"]
 assert sorted(k for k in old if all[k]!=old[k])==[
   "client/HUD.client.luau","server/Game.server.luau",
   "server/PersistentHatchStore.luau"]
 assert all(all[k]==old[k] for k in old if k not in
    ("client/HUD.client.luau","server/Game.server.luau","server/PersistentHatchStore.luau"))
 assert all(blob(all[k])==val for k,val in PIN.items())
 assert len([k for k in all if k.endswith("/Game.server.luau")])==1
 assert len([k for k in all if k.endswith(".server.luau")])==2
 assert len([k for k in all if k.endswith(".client.luau")])==5
 assert blob(all["server/RewardEquipRules.luau"])=="0edf0993e41785b1e206b6ad09955a9984a346e5"
 assert blob(all["server/H2FiveEggRules.luau"])=="0999d69391c176b9b95b04c5444d822e63d7ce04"
 g=all["server/Game.server.luau"].decode()
 h=all["client/HUD.client.luau"].decode()
 store=all["server/PersistentHatchStore.luau"].decode()
 xp=all["server/ProgressionRules.luau"].decode()
 assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert g.count('remote.OnServerEvent:Connect(')==1
 assert "Progression.recordEvent(round,eventId,kind,true)" in g
 assert "Progression.previewXp(round,outcome,duration,true)" in g
 assert "Progression.commit(profile,round,outcome,duration,true)" in g
 assert 'recordServerProgress(player,"PICKUP")' in g
 assert 'recordServerProgress(player,"DEPOSIT")' in g
 assert 'recordServerProgress(player,"EQUIP_USE")' in g
 assert 'recordServerProgress(rec.owner,"DEFEND")' in g
 assert 'PersistentHatch.settleProgress(' in g
 assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in g
 assert 'local function spawnActualScout(' in g
 assert 'RewardRules.finishRound(rewardState,match.serial,eligible,rare)' in g
 assert 'function Store.settleProgress(' in store
 assert 'store:UpdateAsync(key,function(original)' in store
 assert 'state.progress={' in store and 'progress=cloneProgress(raw.progress)' in store
 assert 'Store.MAX_PROGRESS_ROUNDS=Progression.MAX_RECORDED_ROUNDS' in store
 assert "function P.commit(" in xp and "P.XP_CAP_PER_ROUND = 150" in xp
 assert h.count("local seq = 0")==1 and h.count("remote:FireServer(")==3
 assert "RealH1ServerLevel" in h
 assert "progressLastAward" in h and "progressSaveStatus" in h
 record={
  "internal_game":"TRAP_RAIDERS","visible_game":"EGG RAID RUMBLE",
  "stage":"FULL_AUTHENTIC_H1_2_MODES_HATCH_SCOUT_XP_LEVEL_MASTERY_ATOMIC_DEV_STUDIO",
  "source_base_commit":"de8cb430a929e99f97bebcfb3e01633312b26df1",
  "original_policy_source_commit":"cf2d99b3289c69a0f0e076fed6dccb2e4b261299",
  "original_policy_gitblob":PIN["server/ProgressionRules.luau"],
  "all_Luau_scripts":35,"original_modules_identical":31,
  "original_existing_overlays":[
    "server/Game.server.luau","client/HUD.client.luau",
    "server/PersistentHatchStore.luau"],
  "new_original_server_module":"server/ProgressionRules.luau",
  "one_original_Game":True,"one_original_S1_Remote":True,
  "verified_server_objective_event_types":["PICKUP","DEPOSIT","DEFEND","EQUIP_USE"],
  "account_level_1_to_50":True,"round_focus_1_to_3":True,
  "equipped_beast_mastery_1_to_10":True,"max_XP_per_round":150,
  "XP_affects_HP_damage_speed":False,"paid_XP":False,
  "same_inventory_store_atomic_UpdateAsync_code":True,
  "original_DEV_store_name":"EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1",
  "actual_Roblox_DataStore_service_executed":False,
  "studio_2_client_actual_tested":False,"Android_tested":False,
  "owner_fun_gate_accepted":False,"live_Place_approved":False,
  "published":False,"paid":False,"same_DataStore_migration_source":"existing_schema1 optional progress",
  "source_gitblob":{k:blob(v) for k,v in all.items()}
 }
 (NEW/"SOURCE_LOCK.json").write_text(json.dumps(record,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("EGG_RUMBLE_TRUE_FULL_H1_2_MODES_35_SOURCE_XP_MASTERY_AND_INVENTORY_ATOMIC_ASSEMBLY_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--assemble",required=True,action="store_true")
 p.parse_args();build()
