#!/usr/bin/env python3
"""Exact C3 48-Luau original Place -> C4 objective/telemetry/safe-handoff ONE-module delta.
Builds a PRIVATE reviewer Studio Place; no official RC, no production.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys,difflib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
ORIGINAL_B42V7="70714a081a555d716832bb6a640611e05a1f3eca"
ORIGINAL_C3="2370c36a83755f3e5d998ab0b29fc85aa405b26d"
ORIGINAL_GATE_RUNTIME_GITBLOB="473d5c5e0bd24e2e663b2f22076cbae24a3e9030"
def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def source(root:Path):
    return {x.relative_to(root/"src").as_posix():x.read_bytes()
            for x in sorted((root/"src").rglob("*.luau"))}
def main(v7repo:Path,dest:Path):
    assert not dest.exists(),"C4_FAIL_CLOSED_NO_OUTPUT_OVERWRITE"
    base=dest.parent/"_C3_FROZEN_UNCHANGED_RUNTIME_PARENT"
    assert not base.exists(),"C4_FAIL_CLOSED_NO_PARENT_OVERWRITE"
    assert (ROOT/"tools/build_48_c3_safety.py").is_file()
    subprocess.run([sys.executable,"-B",str(ROOT/"tools/build_48_c3_safety.py"),
         "--original-v7-repo",str(v7repo),"--output",str(base)],check=True)
    before=source(base)
    assert len(before)==48
    assert blob(before["server/GateLiveRuntime.luau"])==ORIGINAL_GATE_RUNTIME_GITBLOB
    assert "function GateLiveRuntime:tick" in before["server/GateLiveRuntime.luau"].decode()
    shutil.copytree(base,dest)
    newruntime=(ROOT/"src/GateLiveRuntimeUXC4.luau").read_bytes()
    code=newruntime.decode("utf-8")
    assert "GetPartBoundsInBox" in code
    assert 'Vector3.new(4,4,20)' in code
    assert 'SEA_GATES_MOUNTED' in code
    assert 'ELITE_KO_CONFIRMED' in code
    assert 'ROUND_END_SAFE_OPEN' in code
    assert 'lastPhase~=snapshot.phase' in code
    assert 'MaxDistance=145' in code
    assert 'CanCollide=false' in code and 'CanQuery=false' in code
    assert 'OnServerEvent' not in code
    (dest/"src/server/GateLiveRuntime.luau").write_bytes(newruntime)
    after=source(dest)
    assert len(after)==48
    assert sorted(after)==sorted(before)
    changed=[x for x in before if before[x]!=after[x]]
    assert changed==["server/GateLiveRuntime.luau"],changed
    assert all(before[k]==after[k] for k in before if k not in changed)
    assert sum(k.endswith(".server.luau") for k in after)==2
    assert sum(k.endswith(".client.luau") for k in after)==5
    assert sum(k.endswith("/Game.server.luau") for k in after)==1
    game=after["server/Game.server.luau"].decode("utf-8")
    assert game.count("s2HeistGate:beforeHit(horde)")==2
    assert game.count("s2HeistGate:tick(")==1
    assert game.count("remote.OnServerEvent:Connect(")==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert "StudioSoloGateRules.activePractice(" in game
    visual=after["server/GateVisual.luau"].decode("utf-8")
    assert 'door.CanCollide = false\n        door.CanQuery = false' in visual
    proj=dest/"default.project.json"
    j=json.loads(proj.read_text("utf-8"))
    assert j["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    j["name"]="P0D_C4_GATE_FUN_SAFETY_OBJECTIVE_PRIVATE_STUDIO"
    proj.write_text(json.dumps(j,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    receipt={
      "name":"P0D_C4_ONE_REAL_GATE_RUNTIME_OBSERVABILITY",
      "frozen_original_B42V7":ORIGINAL_B42V7,
      "base_c3_head":ORIGINAL_C3,
      "total_luau":48,"unchanged_c3_scripts":47,
      "only_changed_original":changed,
      "game_server_count":1,"server_RemoteEvent_count":1,
      "studio_only":True,"no_official_rc":True,"published":False,
      "owner_studio_real_run":"NOT_TESTED","android":"NOT_TESTED",
      "two_client":"NOT_TESTED","human_fun":"NOT_TESTED",
      "git_blob_sha1":{k:blob(v) for k,v in sorted(after.items())},
    }
    (dest/"SOURCE_LOCK.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    patch="".join(difflib.unified_diff(
        before["server/GateLiveRuntime.luau"].decode().splitlines(True),
        code.splitlines(True),fromfile="C3_GateLiveRuntime",
        tofile="C4_GateLiveRuntime"))
    (dest/"C3_C4_ONE_MODULE_RUNTIME.diff").write_text(patch,encoding="utf-8")
    print("P0D_C4_ONE_RUNTIME_DELTA_47_OF_48_BYTE_IDENTICAL_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original-v7-repo",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args()
    main(a.original_v7_repo.resolve(),a.output.resolve())
