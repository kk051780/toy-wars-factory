#!/usr/bin/env python3
"""Rebuild the actual 42-script B42 one-Game experience; integrate only V6 Horde.
Do not modify B42 or V6 author roots, official RC, main, or any Roblox place.
"""
from __future__ import annotations
from pathlib import Path
import argparse, hashlib, json, shutil, subprocess, sys
HERE = Path(__file__).resolve()
OWN = HERE.parents[1]
REPO = HERE.parents[3]
BASE = REPO / "handoffs/P0D-FIRST90-GUIDED-H1-20261113-01"
BASE_DIST = BASE / "dist/EGG_RAID_RUMBLE_FIRST90_H1_PRIVATE_STUDIO_UNPUBLISHED"
DIST = OWN / "dist/EGG_RAID_RUMBLE_FIRST90_MUSOUV6_SINGLE_GAME_PRIVATE"
OLD_BLOB = "8c147c801e7fa1ff362922d66c9a6fd432fc8b6e"
NEW_BLOB = "e67b186f08a0e9ca20d5f09a7c5b22205e2b7240"
B42_GAME_BLOB = "21b866e801a53ba7ebd66132ae55fe28608750d6"
B42_HUD_BLOB = "ce6707dc1f833600e1c6913504d30911b24cb2a4"

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def sources(dst: Path) -> dict[str,bytes]:
    return {p.relative_to(dst / "src").as_posix():p.read_bytes()
            for p in sorted((dst / "src").rglob("*.luau"))}

def main():
    assert not DIST.exists(), "FAIL_CLOSED_EXISTING_BUILD_NO_OVERWRITE"
    source = OWN / "inputs/MusouHorde.luau"
    assert blob(source.read_bytes()) == NEW_BLOB, "V6_SOURCE_DRIFT"
    combat = OWN / "inputs/MusouCombatRules.luau"
    assert blob(combat.read_bytes()) == "7865af9fb057a368e146941ac5bd7bf89cddc88b"
    # Reproduce B42 using its own existing canonical assembler; no edits to author sources.
    subprocess.run([sys.executable, "-B", str(BASE / "tools/assemble.py"), "--assemble"],
                   cwd=REPO, check=True)
    before = sources(BASE_DIST)
    assert len(before)==42 and blob(before["server/MusouHorde.luau"])==OLD_BLOB
    assert blob(before["server/Game.server.luau"])==B42_GAME_BLOB
    assert blob(before["client/HUD.client.luau"])==B42_HUD_BLOB
    shutil.copytree(BASE_DIST,DIST)
    (DIST/"src/server/MusouHorde.luau").write_bytes(source.read_bytes())
    after = sources(DIST)
    assert len(after)==42 and set(before)==set(after)
    changed = sorted(k for k in before if before[k] != after[k])
    assert changed==["server/MusouHorde.luau"],changed
    assert all(before[p]==after[p] for p in before if p not in changed)
    assert blob(after["server/MusouHorde.luau"])==NEW_BLOB
    assert sum(n.endswith("/Game.server.luau") for n in after)==1
    assert sum(n.endswith(".server.luau") for n in after)==2
    assert sum(n.endswith(".client.luau") for n in after)==5
    game=after["server/Game.server.luau"].decode("utf8")
    hud=after["client/HUD.client.luau"].decode("utf8")
    horde=after["server/MusouHorde.luau"].decode("utf8")
    for sig in ("function Horde.new(", "function Horde:clear(", "function Horde:reset(",
                "function Horde:livingCount(", "function Horde:eliteWarningSeconds(",
                "function Horde:hit(", "function Horde:tick("):
        assert sig in horde, ("Horde API drift",sig)
    assert "local Combat=require(script.Parent:WaitForChild(\"MusouCombatRules\"))" in horde
    assert "ELITE_SWEEP_DANGER_RADIUS" in horde
    assert "MUSOU_SOURCE_MAP_ARENA_REQUIRED" in horde
    assert "m.arms[1].Orientation" in horde and ".65" in horde
    assert "First90WaypointRules" in game and "First90GuideRules" in game
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert "if mobHits>0 then return end" in game
    assert "currentRoot.Position" in game
    assert "Evolution.nextEvolution(" in game and "Power.beginAwaken(" in game
    assert "First90RealObjectiveGuide" in hud
    assert "PromptProductPurchase" not in game
    project = DIST / "default.project.json"
    project_data = json.loads(project.read_text("utf8"))
    assert project_data["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    project_data["name"]="EGG_RAID_RUMBLE_FIRST90_MUSOUV6_UNPUBLISHED"
    project.write_text(json.dumps(project_data,ensure_ascii=False,indent=2)+"\n","utf8")
    lock={
      "game_id":"TRAP_RAIDERS","work_id":"p0d-siege-v19",
      "packet_id":"P0D-FIRST90-MUSOUV6-BRIDGE-20261113-01",
      "parent_b42_full_game_commit":"837853e66278e38bb79f6399c3e8bfc9a2403be6",
      "source_horde_v6_commit":"4b09de3eb70abb2e79268ce41bdecc4b614d39df",
      "parent_42_scripts_unchanged":41,
      "new_module_count":0,"modified_modules":["server/MusouHorde.luau"],
      "all_42_scripts":42,"one_Game_server":True,"one_Remote":True,
      "source_sha1":{k:blob(v) for k,v in sorted(after.items())},
      "official_rc_adopted":False,"studio_engine_tested":False,
      "physical_android_tested":False,"owner_fun":"NOT_TESTED",
      "studio_only":True,"roblox_published":False,"paid":False,
    }
    (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_FIRST90_MUSOUV6_FULL_42_SCRIPT_SINGLE_GAME_SOURCE_PASS")

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true",required=True)
    p.parse_args()
    main()
