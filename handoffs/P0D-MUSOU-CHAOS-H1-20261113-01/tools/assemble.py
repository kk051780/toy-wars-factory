#!/usr/bin/env python3
"""Rebuild the #288 experimental full ONE-game Studio-only project.
Never touch #220 RC/main, deploy, save production Roblox data or start Studio.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

THIS=Path(__file__).resolve()
OWN=THIS.parents[1]
REPO=THIS.parents[3]
BASE=REPO/"handoffs/P0D-EGG-RUMBLE-H1-REAL-PROGRESSION-20261113-01"
BASE_DIST=BASE/"dist/EGG_RAID_RUMBLE_H1_TWO_MODES_XP_MASTERY_DEV_STUDIO_ONLY"
DIST=OWN/"dist/EGG_RAID_RUMBLE_MUSOU_CHAOS_H1_DEV_STUDIO_ONLY"
OVERLAYS={
 "server/Game.server.luau": "Game.server.luau",
 "client/HUD.client.luau": "HUD.client.luau",
 "server/MusouHorde.luau": "MusouHorde.luau",
 "server/MusouBindRules.luau": "MusouBindRules.luau",
 "server/MusouCombatRules.luau": "MusouCombatRules.luau",
}

def sha1_blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def files(root:Path)->dict[str,bytes]:
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}
def build()->dict:
    subprocess.run([sys.executable,"-B",str(BASE/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,check=True)
    assert BASE_DIST.is_dir(),"Missing 35 original H1 sources"
    old=files(BASE_DIST)
    assert len(old)==35,len(old)
    assert "server/Game.server.luau" in old
    assert "client/HUD.client.luau" in old
    assert "server/ProgressionRules.luau" in old
    assert not DIST.exists(),"No destructive overwrite; use isolated new path once"
    shutil.copytree(BASE_DIST,DIST)
    for relative,filename in OVERLAYS.items():
        f=OWN/"inputs"/filename
        assert f.is_file(),f
        target=DIST/"src"/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(f.read_bytes())
    actual=files(DIST)
    assert len(actual)==38,len(actual)
    assert len(set(actual)-set(old))==3
    assert set(actual)-set(old)=={"server/MusouHorde.luau","server/MusouBindRules.luau","server/MusouCombatRules.luau"}
    changed={x for x in old if old[x]!=actual[x]}
    assert changed=={"server/Game.server.luau","client/HUD.client.luau"},changed
    assert all(actual[k]==old[k] for k in old if k not in changed)
    assert len([k for k in actual if k.endswith("/Game.server.luau")])==1
    assert len([k for k in actual if k.endswith(".server.luau")])==2
    assert len([k for k in actual if k.endswith(".client.luau")])==5
    game=actual["server/Game.server.luau"].decode()
    hud=actual["client/HUD.client.luau"].decode()
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count("local function applyAttack(")==1
    assert game.count("local function tickRound(")==1
    assert game.count("horde:reset(match.serial,serverNow())")==1
    assert game.count("horde:tick(now,Players:GetPlayers(),healthy)")==1
    assert game.count("horde:hit(root.Position,look,")==1
    assert game.count('applyNet(player,data)')==1
    assert game.count("applyBreakOrRescue(player,data)")==1
    assert "NET_THROW" in game and "BREAK_FREE" in game and "RESCUE" in game
    assert "local Combat=require(script.Parent:WaitForChild(\"MusouCombatRules\"))" in actual["server/MusouHorde.luau"].decode()
    assert "canStrike(nearest,false)" in actual["server/MusouHorde.luau"].decode()
    assert "canStrike(target,true)" in actual["server/MusouHorde.luau"].decode()
    assert "netImmuneUntil" in game
    assert "if not RunService:IsStudio()" in game
    assert game.count("Progression.recordEvent(round,eventId,kind,true)")==1
    assert game.count('EXPERIMENTAL_FIVE_EGG_MODE=RunService:IsStudio() and chosenMode==ModeVote.SCORE')==1
    assert hud.count("remote:FireServer(")==3
    assert 'local currentNetBound=false' in hud
    assert 'input.KeyCode == Enum.KeyCode.N' in hud
    assert 'input.KeyCode == Enum.KeyCode.B' in hud
    assert not any(t in game for t in ["game:Publish", "MarketplaceService:PromptProductPurchase"])
    project=DIST/"default.project.json"
    data=json.loads(project.read_text(encoding="utf-8"))
    data["name"]="EGG_RAID_RUMBLE_MUSOU_CHAOS_H1_PRIVATE_STUDIO_UNPUBLISHED"
    assert data["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    project.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lock={
      "packet_id":"P0D-MUSOU-CHAOS-H1-20261113-01",
      "game_id":"TRAP_RAIDERS",
      "brand":"EGG RAID RUMBLE",
      "base_commit":"a0331e2e452f4e8e6530d32562ba5ff657b011d9",
      "existing_count":35,"new_count":38,"original_unchanged":33,
      "overlaid_existing":sorted(changed),
      "new_modules":sorted(set(actual)-set(old)),
      "game_remote_count":1,"studio_private_only":True,
      "studio_playtest":"NOT_TESTED","android":"NOT_TESTED",
      "official_RC":"NOT_ADOPTED","owner_fun":"NO_GO",
      "source_blob_sha1":{k:sha1_blob(raw) for k,raw in sorted(actual.items())},
      "source_sha256":{k:hashlib.sha256(raw).hexdigest() for k,raw in sorted(actual.items())},
    }
    (DIST/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return lock

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",action="store_true",required=True)
    p.parse_args()
    result=build()
    print("MUSOU_CHAOS_H1_PRIVATE_38_LUAU_ASSEMBLY_PASS",len(result["source_blob_sha1"]))
