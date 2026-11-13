#!/usr/bin/env python3
"""P0D isolated full original #288 38-Luau game + #285 source-authorized earned power.
Never mutate official rc/main, original #288 sources, game publish or real DataStore.
"""
from __future__ import annotations
import sys,json,hashlib,subprocess,shutil,argparse
from pathlib import Path
HERE=Path(__file__).resolve()
OWN=HERE.parents[1]
REPO=HERE.parents[3]
BASE=REPO/"handoffs/P0D-MUSOU-CHAOS-H1-20261113-01"
OLD=BASE/"dist/EGG_RAID_RUMBLE_MUSOU_CHAOS_H1_DEV_STUDIO_ONLY"
DIST=OWN/"dist/EGG_RAID_RUMBLE_MUSOU_EARNED_POWER_H1_PRIVATE_STUDIO_ONLY"
OVERRIDES={
 "server/Game.server.luau":("Game.server.luau","ac995ea5e960942a557ee0a2a4116bff8ceadfe8"),
 "client/HUD.client.luau":("HUD.client.luau","405fd17e2a2965f5fae2939d984050847c01d840"),
 "server/PowerFantasyRules.luau":("PowerFantasyRules.luau","86e79877cf0e58603a4de67db29155bf98cc511d"),
}
def blob(raw:bytes)->str:
 return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def src(root:Path)->dict[str,bytes]:
 return {p.relative_to(root/"src").as_posix():p.read_bytes()
         for p in sorted((root/"src").rglob("*.luau"))}
def main():
 assert not DIST.exists(),"FAIL_CLOSED: dist path already exists, do not replace"
 subprocess.run([sys.executable,"-B",str(BASE/"tools/assemble.py"),"--assemble"],
                cwd=REPO,check=True)
 old=src(OLD)
 assert len(old)==38,len(old)
 assert blob(old["server/Game.server.luau"])=="f8c45bcf109dc3229c0459e4fb9fa224ab6c38a4"
 assert blob(old["client/HUD.client.luau"])=="070a2cbc76b79061c0744160b4e201fdd5d15ab3"
 for rel,(name,sha) in OVERRIDES.items():
  file=OWN/"inputs"/name
  assert file.is_file() and blob(file.read_bytes())==sha,(rel,sha)
 shutil.copytree(OLD,DIST)
 for rel,(name,_) in OVERRIDES.items():
  target=DIST/"src"/rel
  target.parent.mkdir(parents=True,exist_ok=True)
  target.write_bytes((OWN/"inputs"/name).read_bytes())
 current=src(DIST)
 assert len(current)==39,len(current)
 assert sorted(set(current)-set(old))==["server/PowerFantasyRules.luau"]
 changed=[p for p in old if old[p]!=current[p]]
 assert sorted(changed)==["client/HUD.client.luau","server/Game.server.luau"],changed
 assert all(old[k]==current[k] for k in old if k not in changed)
 game=current["server/Game.server.luau"].decode("utf8")
 hud=current["client/HUD.client.luau"].decode("utf8")
 policy=current["server/PowerFantasyRules.luau"].decode("utf8")
 assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
 assert game.count("remote.OnServerEvent:Connect(")==1
 assert game.count("local function applyAttack(")==1
 assert game.count("local function tickRound(")==1
 assert len([k for k in current if k.endswith("/Game.server.luau")])==1
 assert len([k for k in current if k.endswith(".server.luau")])==2
 assert len([k for k in current if k.endswith(".client.luau")])==5
 assert game.count('local Power = require(script.Parent:WaitForChild("PowerFantasyRules"))')==1
 assert game.count("Power.makeRound(")==1
 assert game.count("Power.recordObjective(state,eventId,kind,true)")==1
 assert game.count('*earnedDamageMultiplier(player,"MINION")')==1
 assert game.count('*earnedDamageMultiplier(player,"PLAYER")')==1
 assert game.count("Power.beginAwaken(")==1
 assert 'elseif data.action == "AWAKEN_POWER" then applyEarnedAwaken(player,data)' in game
 assert "return math.max(0,math.floor(serverNow()-match.startedAt))" in game
 assert "if not RunService:IsStudio() or match.phase~=\"ACTIVE\"" in game
 assert "Power.endRound(" in game
 assert "Power.TELEGRAPH_SECONDS = 2" in policy
 assert 'awakenButton.MouseButton1Click:Connect(function() action("AWAKEN_POWER",nil) end)' in hud
 assert "Enum.KeyCode.V" in hud
 assert hud.count("local seq = 0")==1
 assert len([x for x in current if x.endswith("PowerFantasyRules.luau")])==1
 assert not any(x in game for x in ["game:Publish(", "MarketplaceService:PromptProductPurchase"])
 project=DIST/"default.project.json"
 desc=json.loads(project.read_text("utf8"))
 assert desc["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
 desc["name"]="EGG_RAID_RUMBLE_H1_EARNED_MUSOU_POWER_PRIVATE_ONLY_UNPUBLISHED"
 project.write_text(json.dumps(desc,indent=2,ensure_ascii=False)+"\n","utf8")
 lock={
  "packet_id":"P0D-MUSOU-EARNED-POWER-H1-20261113-01",
  "game_id":"TRAP_RAIDERS",
  "game_brand":"EGG RAID RUMBLE",
  "parent_game_sha":"55ad13b45907a5a3e9deae7196a7c202a0672c0c",
  "original_pure_power_sha":"5e18a52e1e74f10cc1b85ac3b60f695e064bb088",
  "pure_power_blob":OVERRIDES["server/PowerFantasyRules.luau"][1],
  "total_luau":39,
  "unchanged_original_modules":36,
  "overlaid_existing":sorted(changed),
  "one_new_original_pure_server_module":["server/PowerFantasyRules.luau"],
  "studio_only":True,"first_release_authorized":False,
  "official_rc_adopted":False,"actual_studio_tested":False,
  "mobile_tested":False,"human_fun_gate":"FUN_NO_GO",
  "real_earned_pve_multiplier":True,"real_earned_pvp_multiplier":True,
  "server_only_awaken":True,"client_level_trusted":False,
  "real_player_health_multiplier":False,
  "evolution_integrated":False,
  "source_blob_sha1":{k:blob(v) for k,v in sorted(current.items())},
  "source_sha256":{k:hashlib.sha256(v).hexdigest() for k,v in sorted(current.items())}
 }
 (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,indent=2,ensure_ascii=False)+"\n","utf8")
 print("P0D_H1_REAL_EARNED_POWER_39_SOURCE_ASSEMBLED_ONE_GAME_PASS")
if __name__=="__main__":
 parser=argparse.ArgumentParser();parser.add_argument("--assemble",action="store_true",required=True)
 parser.parse_args();main()
