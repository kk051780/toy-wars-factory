#!/usr/bin/env python3
"""Real complete H1 one-place two-mode + original free hatch policy and actual scout.

This is an unpublished PRIVATE Roblox Studio experiment, not official #220/Live.
Uses pinned original #279 real 32-Luau entire game and preserves 30/32 original
source bytes; overlays ONLY original Game+HUD and adds ONE exact #275 module.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve();REPO=HERE.parents[3];OWN=HERE.parents[1]
UP=REPO/"handoffs/P0D-EGG-RUMBLE-DUAL-MODE-LOBBY-20261113"
UP_DIST=UP/"dist/EGG_RAID_RUMBLE_SINGLE_GAME_TWO_MODES_PRIVATE_STUDIO"
DST=OWN/"dist/EGG_RAID_RUMBLE_FREE_HATCH_EQUIP_REAL_3D_SCOUT_PRIVATE_STUDIO"
PIN={
 "server/Game.server.luau":"8f733ec7bac913c37055c8cc5373571e2c3711c7",
 "client/HUD.client.luau":"c0a0e41eb57d1eb7f3d0271da1bf2ad7da16a625",
 "server/RewardEquipRules.luau":"0edf0993e41785b1e206b6ad09955a9984a346e5",
}
def gitblob(data:bytes):
 return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def sources(root):
 return {p.relative_to(root/"src").as_posix():p.read_bytes()
         for p in sorted((root/"src").rglob("*.luau"))}
def assemble():
 subprocess.run([sys.executable,"-B",str(UP/"tools/assemble.py"),"--assemble"],check=True,cwd=REPO)
 base=sources(UP_DIST)
 assert len(base)==32,len(base)
 assert [x for x in base if x.endswith("/Game.server.luau")]==["server/Game.server.luau"]
 for path,sha in PIN.items():
  source=OWN/"inputs"/Path(path).name
  assert source.is_file(),source
  actual=gitblob(source.read_bytes())
  assert actual==sha,("SOURCE_NOT_PINNED",path,actual,sha)
 if DST.exists():shutil.rmtree(DST)
 shutil.copytree(UP_DIST,DST)
 for rel in PIN:
  dst=DST/"src"/rel
  dst.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(OWN/"inputs"/Path(rel).name,dst)
 project_path=DST/"default.project.json"
 project=json.loads(project_path.read_text(encoding="utf-8"))
 assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 project["name"]="EGG_RAID_RUMBLE_2_MODES_FREE_HATCH_EQUIP_REAL_SCOUT_UNPUBLISHED_STUDIO"
 project_path.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 full=sources(DST)
 assert len(full)==33,len(full)
 assert sorted(set(full)-set(base))==["server/RewardEquipRules.luau"]
 assert sorted(k for k in base if full[k]!=base[k])==[
  "client/HUD.client.luau","server/Game.server.luau"]
 assert all(base[k]==full[k] for k in base if k not in ("server/Game.server.luau","client/HUD.client.luau"))
 for k,sha in PIN.items():
  assert gitblob(full[k])==sha,k
 game=full["server/Game.server.luau"].decode()
 hud=full["client/HUD.client.luau"].decode()
 policy=full["server/RewardEquipRules.luau"].decode()
 assert len([k for k in full if k.endswith(".server.luau")])==2
 assert len([k for k in full if k.endswith(".client.luau")])==5
 assert len([k for k in full if k.endswith("/Game.server.luau")])==1
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert game.count('remote.OnServerEvent:Connect(')==1
 assert game.count('RewardRules.finishRound(')==1
 assert game.count('RewardRules.claimFreeHatch(')==1
 assert game.count('RewardRules.equip(')==1
 assert game.count('RewardRules.requestScout(')==1
 assert 'local EXPERIMENTAL_FIVE_EGG_MODE = false' in game
 assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in game
 assert 'modeVotes[player]=data.mode' in game
 assert 'local function spawnActualScout(' in game
 assert 'model.Parent=map.model' in game
 assert 'Highlight.DepthMode=Enum.HighlightDepthMode.Occluded' not in game
 assert 'highlighted.DepthMode=Enum.HighlightDepthMode.Occluded' in game
 assert 'lastFreeHatch[player]=item' in game
 assert 'if scoutModels[player]==model and scoutActivitySerial[player]==generation' in game
 assert 'modeScoreAvailable = RunService:IsStudio()' in game
 assert hud.count('local seq = 0')==1 and hud.count('remote:FireServer(')==3
 assert 'BEAST_HATCH_EQUIP' in hud and 'SummonRealScout' in hud
 assert 'MODE_VOTE' in hud and 'EQUIP_SCOUT' in hud and 'ACTIVATE_SCOUT' in hud
 assert 'function Rules.claimFreeHatch(' in policy and 'function Rules.requestScout(' in policy
 assert 'function Rules.export(' in policy and 'function Rules.restore(' in policy
 for bad in ('FireServer','RemoteEvent','DataStoreService','Instance.new('):
  assert bad not in policy,bad
 assert gitblob(full["server/H2FiveEggRules.luau"])=="0999d69391c176b9b95b04c5444d822e63d7ce04"
 report={
  "visible_title":"EGG RAID RUMBLE",
  "internal_game_id":"TRAP_RAIDERS",
  "previous_original_full_H1_two_modes_fixed_sha":"7e65166bed5b8dc12119a511cfa4974d5b168b31",
  "original_reward_equip_policy_fixed_sha":"86da0ba54dfd0f6308717c9117cb352661551170",
  "original_reward_policy_gitblob":"0edf0993e41785b1e206b6ad09955a9984a346e5",
  "game_scripts":33,
  "original_scripts_byte_identical":30,
  "existing_original_scripts_overlaid":["server/Game.server.luau","client/HUD.client.luau"],
  "one_added_reward_authority_pure_module":"server/RewardEquipRules.luau",
  "one_original_Game":True,
  "one_original_S1_Remote":True,
  "both_original_modes":["CLASSIC","SCORE_5"],
  "score_mode_Studio_only":True,
  "free_hatch_once_per_server_match_epoch":True,
  "inventory_owner_scoped":True,
  "equipped_only_in_lobby_or_countdown":True,
  "actual_summon_server_replication":"Model in MapBuilder world visible to both clients",
  "scout_duration_seconds":5,"scout_cooldown_seconds":18,
  "current_actual_gameplay_category":"BEAST ONLY",
  "other_five_categories_not_implemented":True,
  "DataStore_actual_persistence_implemented":False,
  "free_hatch_items_lost_on_reconnect":True,
  "real_Studio_2client_played":False,"actual_Android_tested":False,
  "human_FUN_gate":False,"official_RC_adopted":False,
  "published":False,"paid_random_items":False,
  "actual_script_gitblobs":{k:gitblob(v) for k,v in full.items()}
 }
 (DST/"SOURCE_LOCK.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 print("EGG_RUMBLE_FREE_HATCH_2MODE_REAL_GAME_SINGLE_AUTHORITY_33_SOURCES_PASS")
 return report
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--assemble",action="store_true",required=True)
 p.parse_args();assemble()
