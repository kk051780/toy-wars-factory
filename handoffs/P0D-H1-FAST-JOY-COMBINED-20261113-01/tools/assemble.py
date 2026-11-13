#!/usr/bin/env python3
"""Create one original H1 child-joy Place: 28 original #262 sources + 2 NEW client-only.
No edits to server Game, original HUD, D18 guide, creatures, world, RC or main.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
OWN=Path(__file__).resolve().parents[1]
BASE=REPO/"handoffs/P0D-H1-FAST-ROUTES-WITH-UX-20261113-01"
SRC=BASE/"dist/TRAP_RAIDERS_H1_WOW_STUDIO_ONLY"
DST=OWN/"dist/TRAP_RAIDERS_H1_FAST_SEA_SKY_JOY_STUDIO_ONLY"
NEW=("EggJoyRules.luau","EggJoy.client.luau")
EXPECTED={
    "server/Game.server.luau":"adecfee41a594bdd54393050b4890a5733a536ce",
    "server/MapBuilder.luau":"94655d019fdf9798fa24a350ebf49f8290465ac0",
    "server/H1FunWorld.server.luau":"7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea",
    "server/S1RaiderWindRules.luau":"7d5706774b874759e7ab994dc0654c3ae9a46502",
    "client/HUD.client.luau":"313484a69eb10ce01bbdb4872afee215133b01d4",
    "client/D18Batch8Catalog.luau":"41079553d2141940fc3fee57b23969e292770614",
    "client/D18MascotGuideRules.luau":"328b8a4d70261e633f163a5e166822a29d7eb1ba",
    "client/D18MascotGuide.client.luau":"39a2e35e4b2e8635d6d87359cd86f783aedf8756",
}
def blob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def scripts(d):
    return {p.relative_to(d/"src").as_posix():p.read_bytes()
            for p in sorted((d/"src").rglob("*.luau"))}
def main():
    subprocess.run([sys.executable,str(BASE/"tools/assemble.py"),"--assemble"],check=True,cwd=REPO)
    original=scripts(SRC)
    assert len(original)==28
    for n,gitsha in EXPECTED.items():
        assert blob(original[n])==gitsha,("BROKEN_PIN",n,blob(original[n]))
    assert "client/EggJoy.client.luau" not in original
    if DST.exists():shutil.rmtree(DST)
    shutil.copytree(SRC,DST)
    for n in NEW:
        shutil.copyfile(OWN/"client"/n,DST/"src/client"/n)
    data=json.loads((DST/"default.project.json").read_text(encoding="utf8"))
    data["name"]="TRAP_RAIDERS_H1_FAST_SEA_SKY_FIRST90_EGG_JOY_PRIVATE_STUDIO_ONLY"
    clients=data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    for name,filename in (("EggJoyRules","EggJoyRules.luau"),
                           ("EggJoy","EggJoy.client.luau")):
        assert name not in clients
        clients[name]={"$path":"src/client/"+filename}
    (DST/"default.project.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    merged=scripts(DST)
    assert len(merged)==30 and sorted(set(merged)-set(original))==[
        "client/EggJoy.client.luau","client/EggJoyRules.luau"]
    assert all(merged[n]==raw for n,raw in original.items()),"ORIGINAL_GAME_MODIFIED"
    assert len([n for n in merged if n.endswith(".server.luau")])==2
    assert len([n for n in merged if n.endswith(".client.luau")])==5
    j=merged["client/EggJoy.client.luau"].decode("utf8")
    r=merged["client/EggJoyRules.luau"].decode("utf8")
    assert 'remote.OnClientEvent:Connect' in j
    assert 'if not RunService:IsStudio() then return end' in j
    assert 'previous.serial ~= current.serial' in r
    assert 'snap.updateId <= previous.updateId' in r
    assert 'current.scores[current.team] > previous.scores[current.team]' in r
    assert 'previous.carrying == "" and current.carrying ~= ""' in r
    assert j.count('Instance.new("Frame")')==2 # panel + gem frames, each instantiated 8 times max
    for n in NEW:
        content=merged["client/"+n].decode("utf8")
        for forbidden in ('FireServer','Instance.new("RemoteEvent")','DataStoreService',
                          'MarketplaceService','TakeDamage','GamePassService'):
            assert forbidden not in content,("UNAUTHORIZED_CLIENT",n,forbidden)
    receipt={
        "stage":"PRELAUNCH_PRIVATE_STUDIO_ONLY",
        "adoption_id":"P0D-FUN-H1-001",
        "issue":"#266",
        "base_game_28_commit":"8f2a4aed7f6483f0bd00e31fcd733a823aa5c008",
        "exact_base_28_files":28,
        "new_client_only_files":[f"client/{n}" for n in NEW],
        "script_total":30,
        "original_all_28_gitblobs":{n:blob(raw) for n,raw in original.items()},
        "new_2_gitblobs":{f"client/{n}":blob(merged["client/"+n]) for n in NEW},
        "game_server_mutated":False,
        "original_HUD_mutated":False,
        "Studio2client_tested":False,
        "mobile_tested":False,
        "human_FTUE_fun_approved":False,
        "official_RC_adopted":False,
        "published":False,
    }
    (DST/"SOURCE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("P0D_H1_FAST_ROUTES_EGG_JOY_28_UNCHANGED_PLUS_2_EXACT_NEW_30_PASS")
if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--assemble",action="store_true",required=True);p.parse_args();main()
