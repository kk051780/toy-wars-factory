#!/usr/bin/env python3
"""C5 actual ORIGINAL C4 48-Luau private Place + one additive read-only QA LocalScript.
One original Game/Remote/World, no extra controller, gameplay all byte-identical.
"""
from __future__ import annotations
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
C4_FIXED="496019ee87608793d80b31b8f92db59a056a8077"
V7_FIXED="70714a081a555d716832bb6a640611e05a1f3eca"
def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
def scripts(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}
def main(repo:Path,dest:Path):
    assert not dest.exists(),"C5_OUTPUT_EXISTS_REFUSE_OVERWRITE"
    c4=dest.parent/"_C4_ACTUAL_UNCHANGED_48_OWNER_BASE"
    assert not c4.exists(),"C5_SOURCE_PARENT_EXISTS_REFUSE_OVERWRITE"
    subprocess.run([sys.executable,"-B",str(ROOT/"tools/build_48_c4_gameplay_audit.py"),
       "--original-v7-repo",str(repo),"--output",str(c4)],check=True)
    before=scripts(c4)
    assert len(before)==48
    original_game_blob=blob(before["server/Game.server.luau"])
    original_runtime_blob=blob(before["server/GateLiveRuntime.luau"])
    original_world_blob=blob(before["server/H1FunWorld.server.luau"])
    assert original_world_blob=="7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea"
    shutil.copytree(c4,dest)
    observer=(ROOT/"src/OwnerGateRealPlayObserverC5.client.luau").read_bytes()
    text=observer.decode("utf-8")
    assert 'if not RunService:IsStudio() then return end' in text
    assert 'originalRemote.OnClientEvent:Connect(' in text
    assert 'RunService.Heartbeat:Connect(' in text
    assert 'REAL_AVATAR_CROSSED_OPEN_' in text
    assert 'BOTH_DOORS_ACTUALLY_NONCOLLIDING_NONQUERYING' in text
    assert 'ACTIVE_12S_NO_PHYSICAL_SEA_GATES' in text
    for banned in ("OnServerEvent:Connect","FireServer(","InvokeServer(",
                   "Instance.new(","TakeDamage(","SetAsync(","UpdateAsync("):
        assert banned not in text,("READ_ONLY_CLIENT_POLICY_VIOLATION",banned)
    path=dest/"src/client/OwnerGateRealPlayObserverC5.client.luau"
    assert not path.exists()
    path.write_bytes(observer)
    project=dest/"default.project.json"
    data=json.loads(project.read_text("utf-8"))
    players=data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert players["TrapRaidersHUD"]["$path"]=="src/client/HUD.client.luau"
    assert "OwnerGateRealPlayObserverC5" not in players
    players["OwnerGateRealPlayObserverC5"]={
      "$path":"src/client/OwnerGateRealPlayObserverC5.client.luau"}
    data["name"]="P0D_C5_B42_V7_ELITE_GATE_OBSERVED_ENGINE_PRIVATE"
    project.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    now=scripts(dest)
    assert len(now)==49
    assert set(now)-set(before)=={"client/OwnerGateRealPlayObserverC5.client.luau"}
    assert all(before[k]==now[k] for k in before)
    assert blob(now["server/Game.server.luau"])==original_game_blob
    assert blob(now["server/GateLiveRuntime.luau"])==original_runtime_blob
    assert blob(now["server/H1FunWorld.server.luau"])==original_world_blob
    assert sum(k.endswith(".server.luau") for k in now)==2
    assert sum(k.endswith(".client.luau") for k in now)==6
    assert sum(k.endswith("/Game.server.luau") for k in now)==1
    g=now["server/Game.server.luau"].decode("utf8")
    assert g.count('remote.OnServerEvent:Connect(')==1
    assert g.count('remote.Name = "TrapRaidersS1Remote"')==1
    receipt={
      "name":"P0D_C5_OWNER_GATE_REAL_ENGINE_OBSERVER",
      "exact_parent_C4_SHA":C4_FIXED,"exact_owner_V7_base_SHA":V7_FIXED,
      "original_48_luau_byte_identical":True,
      "only_added_local_script":"client/OwnerGateRealPlayObserverC5.client.luau",
      "script_count":49,"server_Game_count":1,
      "Game_Remote_count":1,"world_unchanged":True,
      "not_automated_roblox_engine_test":True,
      "owner_studio":"NOT_TESTED","two_client":"NOT_TESTED",
      "android":"NOT_TESTED","fun":"NOT_TESTED",
      "official_RC_adopted":False,"published":False,
      "source_lock_git_sha1":{k:blob(v) for k,v in sorted(now.items())},
    }
    (dest/"SOURCE_LOCK.json").write_text(json.dumps(receipt,indent=2)+"\n",encoding="utf-8")
    print("P0D_C5_REAL_C4_48_UNCHANGED_PLUS_ONE_PASS")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--original-v7-repo",required=True,type=Path)
    p.add_argument("--output",required=True,type=Path)
    a=p.parse_args();main(a.original_v7_repo.resolve(),a.output.resolve())
