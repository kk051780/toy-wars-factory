#!/usr/bin/env python3
"""B42+V7+SkyCastle one-Game Private Studio 1-client preview, no public behavior change.
Rebuild frozen base, mount exact tested pure Solo module and patch ONLY original Game.
"""
from __future__ import annotations
import argparse,hashlib,json,subprocess,sys,shutil
from pathlib import Path
HERE=Path(__file__).resolve();OWN=HERE.parents[1];REPO=HERE.parents[3]
UP=REPO/"handoffs/P0D-B42-V7-SKYCASTLE-20261113-01"
BASE=UP/"dist/EGG_RAID_RUMBLE_FIRST90_V7_SKYCASTLE_PRIVATE"
DST=OWN/"dist/EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_STUDIO_SOLO_UNPUBLISHED"
SOURCE_SOLO="22e7e22e8837dbf44c57fdfb30efd480457022fb"
GAME_B42="21b866e801a53ba7ebd66132ae55fe28608750d6"
WORLD="0a6360392f4384dc2f0ab1e9afc1d840d66a22b8"
V7_HORDE="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
def gitblob(raw):
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def source(root):
 return {p.relative_to(root/"src").as_posix():p.read_bytes() for p in sorted((root/"src").rglob("*.luau"))}
def once(s,original,updated,label):
 assert s.count(original)==1,(label,s.count(original))
 return s.replace(original,updated)
def upgrade_game(s):
 s=once(s,
 'local RunService = game:GetService("RunService")',
 'local RunService = game:GetService("RunService")\n'
 'local StudioSolo = require(script.Parent:WaitForChild("StudioSoloPreviewRules"))',
 "one_original_import")
 s=once(s,
 'if count >= Config.MinPlayers and teamCount("RED") > 0 and teamCount("BLUE") > 0 then',
 'if StudioSolo.canStart(RunService:IsStudio(),count,\n'
 '            teamCount("RED"),teamCount("BLUE"),Config.MinPlayers) then',
 "lobby_starts_only_once")
 s=once(s,
 'if count < Config.MinPlayers or teamCount("RED") == 0 or teamCount("BLUE") == 0 then',
 'if not StudioSolo.canStart(RunService:IsStudio(),count,\n'
 '            teamCount("RED"),teamCount("BLUE"),Config.MinPlayers) then',
 "countdown_guard_only_once")
 s=once(s,
 '        if teamCount("RED") <= 0 then stopRound("BLUE", "TEAM_EMPTY")\n'
 '        elseif teamCount("BLUE") <= 0 then stopRound("RED", "TEAM_EMPTY")\n'
 '        elseif EXPERIMENTAL_FIVE_EGG_MODE and h2ScoreState',
 '        local emptyWinner=StudioSolo.emptyWinner(RunService:IsStudio(),count,\n'
 '            teamCount("RED"),teamCount("BLUE"))\n'
 '        if emptyWinner~=nil then stopRound(emptyWinner, "TEAM_EMPTY")\n'
 '        elseif EXPERIMENTAL_FIVE_EGG_MODE and h2ScoreState',
 "one_original_active_empty_team_guard")
 assert s.count("StudioSolo.canStart(")==2
 assert s.count("StudioSolo.emptyWinner(")==1
 assert s.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert s.count("remote.OnServerEvent:Connect(")==1
 assert s.count("local function tickRound()")==1
 assert s.count("local function resetRound()")==1
 assert s.count("local function stopRound(")==1
 assert s.count("Config.MinPlayers")==3,\
     ("MinPlayers reference drift",s.count("Config.MinPlayers"))
 assert 'if #online < Config.MinPlayers then return end' in s
 assert 'EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE' in s
 for token in ("First90GuideRules","First90WaypointRules","Evolution.nextEvolution(","Power.beginAwaken(","horde:hit("):
  assert token in s,("missing original H1 gameplay",token)
 return s
def main():
 assert not BASE.exists() and not DST.exists(),"FAIL_CLOSED_NO_DESTRUCTIVE_REBUILD"
 original_policy=(OWN/"inputs/StudioSoloPreviewRules.luau").read_bytes()
 assert gitblob(original_policy)==SOURCE_SOLO,"SOLO_SOURCE_DRIFT"
 subprocess.run([sys.executable,"-B",str(UP/"tools/assemble.py"),"--assemble"],
                check=True,cwd=REPO)
 before=source(BASE)
 assert len(before)==42,len(before)
 assert gitblob(before["server/Game.server.luau"])==GAME_B42
 assert gitblob(before["server/MusouHorde.luau"])==V7_HORDE
 assert gitblob(before["server/H1FunWorld.server.luau"])==WORLD
 shutil.copytree(BASE,DST)
 (DST/"src/server/StudioSoloPreviewRules.luau").write_bytes(original_policy)
 patched=upgrade_game(before["server/Game.server.luau"].decode("utf8"))
 (DST/"src/server/Game.server.luau").write_text(patched,encoding="utf8")
 after=source(DST)
 assert len(after)==43 and len(set(after)-set(before))==1
 assert set(after)-set(before)=={"server/StudioSoloPreviewRules.luau"}
 assert [p for p in before if before[p]!=after[p]]==["server/Game.server.luau"]
 assert sum(p.endswith("/Game.server.luau") for p in after)==1
 assert sum(p.endswith(".server.luau") for p in after)==2
 assert sum(p.endswith(".client.luau") for p in after)==5
 assert gitblob(after["server/StudioSoloPreviewRules.luau"])==SOURCE_SOLO
 assert all(before[p]==after[p] for p in before if p!="server/Game.server.luau")
 project=DST/"default.project.json"
 desc=json.loads(project.read_text("utf8"))
 assert desc["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 desc["name"]="P0D_B42_MUSOUV7_SKYCASTLE_STUDIO_SOLO_PRIVATE_UNPUBLISHED"
 project.write_text(json.dumps(desc,ensure_ascii=False,indent=2)+"\n","utf8")
 report={"feature_slice":"P0D_B42_MUSOUV7_SKYCASTLE_STUDIO_SOLO",
  "base_commit":"a3dfc9b98f22b8edf0a7d0d978d65b1072aed933",
  "solo_author_source_commit":"5179628af91d1e89dbf0449e4edd39247082747a",
  "original_solo_policy_blob":SOURCE_SOLO,
  "game_modified":["server/Game.server.luau"],
  "new_module":["server/StudioSoloPreviewRules.luau"],
  "old_sources_byte_exact":41,
  "full_scripts":43,"single_Game":True,"single_Remote":True,
  "solo_only_studio":True,"public_two_team_rule_unchanged":True,
  "official_s1_rc":"NOT_ADOPTED","owner_Studio_test":"NOT_TESTED",
  "android":"NOT_TESTED","owner_FUN":"NOT_TESTED","published":False,
  "source_blobs":{p:gitblob(raw) for p,raw in sorted(after.items())}}
 (DST/"SOURCE_LOCK.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n","utf8")
 print("P0D_B42_V7_SKYCASTLE_SOLO_ONE_GAME_43_SOURCE_PASS")
if __name__=="__main__":
 p=argparse.ArgumentParser()
 p.add_argument("--assemble",required=True,action="store_true")
 p.parse_args();main()
