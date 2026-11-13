#!/usr/bin/env python3
"""Build a THIRD, optional PRIVATE Studio preview: B42 + V7 + S2 sea gate.
Own new isolated source only. Does not modify #220 official RC or owner branches.
The B42+V7 original 42-script builder is invoked in a separate immutable checkout.
"""
from __future__ import annotations
import argparse, difflib, hashlib, json, shutil, subprocess, sys
from pathlib import Path

HERE=Path(__file__).resolve()
ROOT=HERE.parents[1]
REAL_GITHUB_HEAD="70714a081a555d716832bb6a640611e05a1f3eca"
EXPECTED_GAME="21b866e801a53ba7ebd66132ae55fe28608750d6"
EXPECTED_HORDE="fc6ca46d36bb81ce5f1cd3d327ad2ab714b4be38"
MODULES=("GateRules","GateVisual","EliteKOBridge","GateRouteOverlay","GateLiveRuntime")
ORIGINAL_MODULES_BLOBS={
    "GateRules":"bcd9f18d75dc12edada37cf5faa33c889ca81046",
    "GateVisual":"f94b495725dc7c53e35e35b4e05e753a9a9dd794",
    "EliteKOBridge":"1de469cf589816956b6a35806b4f094bf52d77b1",
    "GateRouteOverlay":"013465a62378722cb35b37e66f9eae399bc4e7e6",
}
def gitblob(raw: bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def files(folder: Path)->dict[str,bytes]:
    return {p.relative_to(folder/"src").as_posix():p.read_bytes()
            for p in sorted((folder/"src").rglob("*.luau"))}
def unique_change(src: str, needle: str, replacement: str)->str:
    count=src.count(needle)
    assert count==1,("FROZEN_ORIGINAL_GAME_ANCHOR_DRIFT",needle[:60],count)
    return src.replace(needle,replacement,1)

def patch_original_game(original: str)->str:
    g=original
    g=unique_change(g,
      'local MusouHorde = require(script.Parent:WaitForChild("MusouHorde"))',
      'local MusouHorde = require(script.Parent:WaitForChild("MusouHorde"))\n'
      'local GateLiveRuntime = require(script.Parent:WaitForChild("GateLiveRuntime")) -- PRIVATE S2 overlay only')
    g=unique_change(g,'local horde=MusouHorde.new(map.model)',
      'local horde=MusouHorde.new(map.model)\n'
      'local s2HeistGate=GateLiveRuntime.new(map.model) -- uses same match.serial and server tick')
    evolved='''                local hits=horde:hit(currentRoot.Position,currentRoot.CFrame.LookVector,
                    if stage>=3 then 40 else 26,serverNow(),player.Character)'''
    g=unique_change(g,evolved,
      '                local beforeElite=s2HeistGate:beforeHit(horde)\n'
      +evolved+'\n'
      '                s2HeistGate:afterHit(horde,beforeElite,serverNow())')
    attack='''        local touched,defeated = horde:hit(root.Position,look,
            Config.CombatDamage[roles[player] or "RAIDER"]
                *earnedDamageMultiplier(player,"MINION"),now,player.Character)'''
    g=unique_change(g,attack,
      '        local beforeElite=s2HeistGate:beforeHit(horde)\n'
      +attack+'\n'
      '        s2HeistGate:afterHit(horde,beforeElite,now)')
    g=unique_change(g,
      '    if RunService:IsStudio() then horde:reset(match.serial,serverNow()) end',
      '    if RunService:IsStudio() then\n'
      '        horde:reset(match.serial,serverNow())\n'
      '        s2HeistGate:startRound(match.serial,serverNow())\n'
      '    end')
    g=unique_change(g,'local function tickRound()\n    local now = serverNow()',
      'local function tickRound()\n'
      '    local now = serverNow()\n'
      '    s2HeistGate:tick(now,match.serial,match.phase) -- existing sole server clock')
    assert g.count("s2HeistGate:beforeHit(horde)")==2
    assert g.count("s2HeistGate:afterHit(horde,beforeElite,")==2
    assert g.count("s2HeistGate:startRound(")==1
    assert g.count("s2HeistGate:tick(")==1
    assert g.count("horde:hit(")==original.count("horde:hit(")==2
    assert g.count("remote.OnServerEvent:Connect(")==1
    assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert g.count("local function tickRound()")==1
    assert g.count("local function resetRound()")==1
    assert "First90Guide.mark(guideProgress[player],match.serial" in g
    assert "Power.beginAwaken(" in g and "Evolution.nextEvolution(" in g
    assert 'if mobHits>0 then return end' in g
    assert g.count('Instance.new("RemoteEvent")')==original.count('Instance.new("RemoteEvent")')
    return g

def main(v7_repo: Path, out_dir: Path)->None:
    base=v7_repo/"handoffs/P0D-FIRST90-MUSOUV7-UPGRADE-20261113-01"
    v7dist=base/"dist/EGG_RAID_RUMBLE_FIRST90_MUSOUV7_SINGLE_GAME_PRIVATE"
    assert not v7dist.exists(),"DO_NOT_OVERWRITE_FROZEN_V7_DIST"
    assert not out_dir.exists(),"DO_NOT_OVERWRITE_PRIVATE_TRIAL"
    for name,expect in ORIGINAL_MODULES_BLOBS.items():
        actual=gitblob((ROOT/"src"/(name+".luau")).read_bytes())
        assert actual==expect,("GATE_AUTHOR_SRC_DRIFT",name,actual)
    live_src=(ROOT/"src/GateLiveRuntime.luau").read_bytes()
    assert b"workspace:GetPartBoundsInBox" in live_src
    assert b"GateRouteOverlay.create" in live_src
    subprocess.run([sys.executable,"-B",str(base/"tools/assemble.py"),
                    "--assemble"],check=True,cwd=v7_repo)
    old=files(v7dist)
    assert len(old)==42
    assert gitblob(old["server/Game.server.luau"])==EXPECTED_GAME
    assert gitblob(old["server/MusouHorde.luau"])==EXPECTED_HORDE
    assert sum(n.endswith(".server.luau") for n in old)==2
    assert sum(n.endswith(".client.luau") for n in old)==5
    shutil.copytree(v7dist,out_dir)
    game_original=old["server/Game.server.luau"].decode("utf-8")
    game_patched=patch_original_game(game_original)
    (out_dir/"src/server/Game.server.luau").write_text(game_patched,encoding="utf-8")
    for name in MODULES:
        (out_dir/"src/server"/(name+".luau")).write_bytes((ROOT/"src"/(name+".luau")).read_bytes())
    new=files(out_dir)
    assert len(new)==47, len(new)
    assert len(set(new)-set(old))==5
    assert set(new)-set(old)=={"server/"+n+".luau" for n in MODULES}
    changes=[k for k in old if new[k]!=old[k]]
    assert changes==["server/Game.server.luau"],changes
    assert all(new[k]==old[k] for k in old if k!="server/Game.server.luau")
    assert sum(k.endswith(".server.luau") for k in new)==2
    assert sum(k.endswith(".client.luau") for k in new)==5
    assert sum(k.endswith("/Game.server.luau") for k in new)==1
    assert len([k for k in new if k.endswith(".luau")])-7==40
    # preserve original Rojo layout, only add siblings under same server folder.
    proj=out_dir/"default.project.json"
    data=json.loads(proj.read_text("utf-8"))
    assert data["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    data["name"]="P0D_B42_FIRST90_MUSOUV7_SHARED_SEA_GATE_PRIVATE_UNPUBLISHED"
    proj.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lock={
      "feature":"P0D-S2-ELITE-SEA-GATE-PRIVATE-47",
      "base_original_exact_v7_commit":REAL_GITHUB_HEAD,
      "source_modules":{n:gitblob(new["server/"+n+".luau"]) for n in MODULES},
      "original_b42_game_blob":EXPECTED_GAME,
      "original_v7_horde_blob":EXPECTED_HORDE,
      "original_unchanged_41":True,
      "new_sources":47,
      "changed_original":["server/Game.server.luau"],
      "game_authority_count":1,"remote_count":1,"studio_only":True,
      "rojo_built":False,"original_studio_run":"NOT_TESTED",
      "owner_android":"NOT_TESTED","owner_fun":"NOT_TESTED",
      "official_s1_rc_adopted":False,"published":False,"paid":False,
      "source_git_sha1":{k:gitblob(v) for k,v in sorted(new.items())}
    }
    (out_dir/"SOURCE_LOCK.json").write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out_dir/"GAME_ONE_OWNER_CHANGE.diff").write_text(
      "".join(difflib.unified_diff(game_original.splitlines(keepends=True),
      game_patched.splitlines(keepends=True),
      fromfile="original_B42_V7_server/Game.server.luau",
      tofile="S2_PRIVATE_TRIAL_ONLY_server/Game.server.luau")),
      encoding="utf-8")
    print("P0D_B42_V7_S2_47_SOURCE_LOCK_PREVIEW_ASSEMBLED_PASS")
    print("ORIGINAL_UNCHANGED_41_NEW_MODULES_5_CHANGES_GAME_ONLY")
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original-v7-repo",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    args=p.parse_args()
    main(args.original_v7_repo.resolve(),args.output.resolve())
