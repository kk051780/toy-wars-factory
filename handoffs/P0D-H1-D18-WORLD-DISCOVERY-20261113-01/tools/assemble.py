#!/usr/bin/env python3
"""Private actual #270 H1 full game + exact original #271 D18 two models (32 Luau).
No unapproved new server Game/Round/egg/win authority or original H1 code changes.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

REPO=Path(__file__).resolve().parents[3]
OWN=Path(__file__).resolve().parents[1]
BASE=REPO/"handoffs/P0D-H1-FAST-JOY-COMBINED-20261113-01"
SRC=BASE/"dist/TRAP_RAIDERS_H1_FAST_SEA_SKY_JOY_STUDIO_ONLY"
DST=OWN/"dist/TRAP_RAIDERS_H1_D18_WORLD_DISCOVERY_STUDIO_ONLY"
NEW={
    "D18Batch10Catalog.luau":"d46180c9e071a1a8a2b0b9c8cd9d22a4a89bce43",
    "D18PairRouteDiscover.client.luau":"855a14c9bf8c89622de44bca3faac758bc8909a8"
}
def gitblob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def scripts(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def assemble():
    subprocess.run([sys.executable,str(BASE/"tools/assemble.py"),"--assemble"],cwd=REPO,check=True)
    base=scripts(SRC)
    assert len(base)==30,("EXPECTED_ORIGINAL_H1_30",len(base))
    original_server=base["server/Game.server.luau"].decode("utf-8")
    assert original_server.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert gitblob(base["server/Game.server.luau"])=="adecfee41a594bdd54393050b4890a5733a536ce"
    assert gitblob(base["server/H1FunWorld.server.luau"])=="7aaa2a48d3e58c7c00bc805b74d0c9d8737217ea"
    assert gitblob(base["client/HUD.client.luau"])=="313484a69eb10ce01bbdb4872afee215133b01d4"
    assert gitblob(base["client/EggJoy.client.luau"])=="4066bf4ab5b157be39c14d1d57a7a0f0af107139"
    if DST.exists():shutil.rmtree(DST)
    shutil.copytree(SRC,DST)
    for name,expected_sha in NEW.items():
        item=(OWN/"client"/name).read_bytes()
        assert gitblob(item)==expected_sha,("D18_PIN_FAILED",name,gitblob(item))
        assert "client/"+name not in base,("D18_ALREADY_PRESENT",name)
        (DST/"src/client"/name).write_bytes(item)
    project_path=DST/"default.project.json"
    project=json.loads(project_path.read_text(encoding="utf-8"))
    project["name"]="TRAP_RAIDERS_H1_D18_2_LANDMARKS_REAL_GAME_STUDIO_ONLY"
    clients=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    for module,filename in [("D18Batch10Catalog","D18Batch10Catalog.luau"),
                            ("D18PairRouteDiscover","D18PairRouteDiscover.client.luau")]:
        assert module not in clients,("DUPLICATED_H1_SCRIPT",module)
        clients[module]={"$path":"src/client/"+filename}
    project_path.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    full=scripts(DST)
    assert len(full)==32
    assert all(full[k]==v for k,v in base.items()),"H1_EXISTING_GAME_SOURCE_CHANGED"
    assert set(full)-set(base)==set("client/"+k for k in NEW)
    assert sum(k.endswith(".server.luau") for k in full)==2
    assert sum(k.endswith(".client.luau") for k in full)==6
    client=full["client/D18PairRouteDiscover.client.luau"].decode("utf-8")
    for text in ("RunService:IsStudio()","TRCA-BE-108","TRCA-TR-090",
                 "MAX_NEARBY_MODELS=2","ProximityPrompt","discoveredCount+=1",
                 "CanCollide=false","CanTouch=false","CanQuery=false",
                 'Name="P0D_H1_D18_LOCAL_DECORATIONS_STUDIO_ONLY"'):
        assert text in client,("MISSING_LOCAL_SAFETY",text)
    for n in NEW:
        content=full["client/"+n].decode("utf-8")
        for banned in ('FireServer','RemoteEvent','DataStoreService','MarketplaceService',
                       'TakeDamage','GamePassService','Humanoid.WalkSpeed','GetAsync',
                       'SetAsync','ProcessReceipt','score +','score +='):
            assert banned not in content,("D18_WRONG_AUTHORITY",n,banned)
    receipt={
      "stage":"PRELAUNCH_H1_PRIVATE_STUDIO_ONLY",
      "source_issue":"#274",
      "adoption_id":"P0D-FUN-H1-001",
      "original_30_game_sha":"1f63a529dc512487145cea86557d38cec7f19e03",
      "d18_original_batch10_catalog_sha":"6b30db10ea77ea3ea1161976ae29c5d1b634b2d2",
      "original_30_unchanged":True,
      "new_client_only_2_script_gitblobs":{"client/"+n:sha for n,sha in NEW.items()},
      "original_game_sources_sha1":{k:gitblob(v) for k,v in sorted(base.items())},
      "total_luau_sources":32,
      "new_d18_visual_models":["TRCA-BE-108","TRCA-TR-090"],
      "mirrored_local_landmarks":4,"max_nearby_models_per_client":2,
      "game_server_mutated":False,"gameplay_scoring_changed":False,
      "reward_inventory_monetization":False,"multiegg_feature_integrated":False,
      "real_studio2client_tested":False,"real_android_tested":False,
      "human_child_fun_reviewed":False,"official_rc_adopted":False,"published":False
    }
    (DST/"SOURCE_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("P0D_H1_D18_ORIGINAL_30_UNCHANGED_PLUS_2_CLIENT_NEW_32_REAL_GAME_SOURCE_PASS")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--assemble",action="store_true",required=True)
    parser.parse_args()
    assemble()
