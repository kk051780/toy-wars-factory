#!/usr/bin/env python3
"""Build one complete original H1 experience containing both lobby-votable modes."""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve();REPO=HERE.parents[3];OWN=HERE.parents[1]
UP=REPO/"handoffs/P0D-EGG-RUMBLE-H1-SCORE-MODE-20261113"
UP_DIST=UP/"dist/EGG_RAID_RUMBLE_H1_ORIGINAL_RULES_PRIVATE_STUDIO"
DST=OWN/"dist/EGG_RAID_RUMBLE_SINGLE_GAME_TWO_MODES_PRIVATE_STUDIO"
NEW={
 "server/Game.server.luau":"df3d330fb67e57842114a2a404cd140530ab3ee7",
 "client/HUD.client.luau":"78ec524881ee9f6e790d39b5c2600e915d0042f7",
 "server/ModeVoteRules.luau":"f929a7cd4c211f29d02bd8a129d38109dc492d6e",
}
def blob(b):return hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
def src(d):return {p.relative_to(d/"src").as_posix():p.read_bytes() for p in sorted((d/"src").rglob("*.luau"))}
def build():
 subprocess.run([sys.executable,"-B",str(UP/"tools/assemble.py"),"--mode","ORIGINAL_RULES"],check=True,cwd=REPO)
 baseline=src(UP_DIST)
 assert len(baseline)==31,len(baseline)
 assert blob(baseline["server/H2FiveEggRules.luau"])=="0999d69391c176b9b95b04c5444d822e63d7ce04"
 for rel,expected in NEW.items():
  path=OWN/"inputs"/Path(rel).name
  assert path.is_file(),path
  assert blob(path.read_bytes())==expected,(rel,blob(path.read_bytes()),expected)
 if DST.exists():shutil.rmtree(DST)
 shutil.copytree(UP_DIST,DST)
 for rel in NEW:
  p=DST/"src"/rel;p.parent.mkdir(parents=True,exist_ok=True)
  shutil.copyfile(OWN/"inputs"/Path(rel).name,p)
 p=DST/"default.project.json"
 project=json.loads(p.read_text(encoding="utf-8"))
 assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 project["name"]="EGG_RAID_RUMBLE_TWO_LOBBY_MODES_SAME_PRIVATE_STUDIO_GAME"
 p.write_text(json.dumps(project,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 new=src(DST)
 assert len(new)==32,len(new)
 assert sorted(set(new)-set(baseline))==["server/ModeVoteRules.luau"]
 assert sorted(k for k in baseline if new[k]!=baseline[k])==["client/HUD.client.luau","server/Game.server.luau"]
 for k in baseline:
  if k not in ("client/HUD.client.luau","server/Game.server.luau"):
   assert new[k]==baseline[k],("ORIGINAL_GAME_CHANGED",k)
 assert all(blob(new[k])==v for k,v in NEW.items())
 assert [k for k in new if k.endswith("/Game.server.luau")]==["server/Game.server.luau"]
 assert len([k for k in new if k.endswith(".server.luau")])==2
 assert len([k for k in new if k.endswith(".client.luau")])==5
 game=new["server/Game.server.luau"].decode("utf-8")
 hud=new["client/HUD.client.luau"].decode("utf-8")
 vote=new["server/ModeVoteRules.luau"].decode("utf-8")
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert game.count('remote.OnServerEvent:Connect(')==1
 assert game.count('elseif data.action == "MODE_VOTE" then')==1
 assert game.count('ModeVote.tally(modeVotes,Players:GetPlayers())')==2
 assert game.count('H2Score.new()')==1
 assert game.count('createFiveEggs()')==2
 assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in game
 assert 'table.clear(modeVotes)' in game
 assert 'modeVotes[player]=nil' in game
 assert 'modeScoreAvailable = RunService:IsStudio()' in game
 assert hud.count('local seq = 0')==1
 assert hud.count('remote:FireServer(')==2
 assert 'MODE_VOTE' in hud and 'ModeVoteRules' not in hud
 assert 'function R.tally(' in vote and 'function R.canVote(' in vote
 for bad in ('FireServer','Instance.new(','MarketplaceService','DataStoreService'):assert bad not in vote
 receipt={
  "visible_title":"EGG RAID RUMBLE","internal_id":"TRAP_RAIDERS",
  "stage":"FULL_H1_SINGLE_PRIVATE_STUDIO_PLACE_TWO_MODES",
  "original_full_31_SHA":"fe476562b083537d8f196e8cf54ee3cfaea43bf0",
  "all_actual_source_count":32,"original_unmodified_source_count":29,
  "one_original_game_authority":True,"one_original_S1_remote":True,
  "original_existing_overlays":["server/Game.server.luau","client/HUD.client.luau"],
  "added_pure_module":"server/ModeVoteRules.luau",
  "classic_mode":"CLASSIC","multi_egg_mode":"SCORE_5",
  "vote_phases":["LOBBY","COUNTDOWN"],
  "on_tie_and_no_vote":"CLASSIC",
  "score_mode_available_outside_studio":False,"gameplay_mode_locked_during_ACTIVE":True,
  "real_studio_2client_tested":False,"mobile_tested":False,"fun_gate_accepted":False,
  "official_RC_adopted":False,"published":False,"paid":False,
  "hatch_owned_equip_real_gameplay_implemented":False,
  "actual_script_gitblobs":{k:blob(v) for k,v in new.items()}
 }
 (DST/"SOURCE_LOCK.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
 print("P0D_EGG_RUMBLE_ONE_REAL_H1_GAME_2_MODES_32_SOURCE_ASSEMBLY_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser();p.add_argument("--assemble",action="store_true",required=True)
 p.parse_args();build()
