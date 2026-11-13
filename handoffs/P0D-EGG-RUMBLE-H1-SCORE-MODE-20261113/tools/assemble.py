#!/usr/bin/env python3
"""Generate real full existing H1 30+1 server scoring module, with A untouched-scoring mode
or B H2 scored-mode enabled privately inside Studio ONLY. Never publish either trial.
The only changed original H1 script is the SINGLE EXISTING Game.server.luau.
"""
import argparse,hashlib,json,shutil,subprocess,sys
from pathlib import Path

HERE=Path(__file__).resolve()
REPO=HERE.parents[3]
OWN=HERE.parents[1]
UP=REPO/"handoffs/P0D-H1-FAST-JOY-COMBINED-20261113-01"
UP_DIST=UP/"dist/TRAP_RAIDERS_H1_FAST_SEA_SKY_JOY_STUDIO_ONLY"
DEST_BASE=OWN/"dist"
BLOBS={
    "server/Game.server.luau":"4d49fd068d55f08978eec9a6239dec767e30fd72",
    "server/H2FiveEggRules.luau":"0999d69391c176b9b95b04c5444d822e63d7ce04",
}
BASE_GAME_BLOB="adecfee41a594bdd54393050b4890a5733a536ce"
MODE_LINE="local EXPERIMENTAL_FIVE_EGG_MODE = RunService:IsStudio()"

def gitblob(data):
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def all_source(parent):
    return {p.relative_to(parent/"src").as_posix():p.read_bytes()
            for p in sorted((parent/"src").rglob("*.luau"))}
def assemble(mode):
    assert mode in ("ORIGINAL_RULES","FIVE_EGG_STUDIO"),mode
    subprocess.run([sys.executable,"-B",str(UP/"tools/assemble.py"),"--assemble"],check=True,cwd=REPO)
    baseline=all_source(UP_DIST)
    assert len(baseline)==30,("BASE_30_EXPECTED",len(baseline))
    assert gitblob(baseline["server/Game.server.luau"])==BASE_GAME_BLOB
    assert len([p for p in baseline if p.endswith("/Game.server.luau")])==1
    for rel,h in BLOBS.items():
        raw=(OWN/"inputs"/Path(rel).name).read_bytes()
        assert gitblob(raw)==h,("AUTHORED_OR_IMPORTED_SOURCE_TAMPERED",rel,gitblob(raw),h)
    dst=DEST_BASE/("EGG_RAID_RUMBLE_H2_SCORED_PRIVATE_STUDIO" if mode=="FIVE_EGG_STUDIO"
                   else "EGG_RAID_RUMBLE_H1_ORIGINAL_RULES_PRIVATE_STUDIO")
    if dst.exists():shutil.rmtree(dst)
    shutil.copytree(UP_DIST,dst)
    game=(OWN/"inputs/Game.server.luau").read_text(encoding="utf-8")
    assert game.count(MODE_LINE)==1
    if mode=="ORIGINAL_RULES":
        game=game.replace(MODE_LINE,"local EXPERIMENTAL_FIVE_EGG_MODE = false")
    (dst/"src/server/Game.server.luau").write_text(game,encoding="utf-8")
    shutil.copyfile(OWN/"inputs/H2FiveEggRules.luau",dst/"src/server/H2FiveEggRules.luau")
    project=json.loads((dst/"default.project.json").read_text(encoding="utf-8"))
    project["name"]="EGG_RAID_RUMBLE_H1_STUDIO_ONLY_"+mode
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    (dst/"default.project.json").write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    result=all_source(dst)
    assert len(result)==31
    assert set(result)-set(baseline)=={"server/H2FiveEggRules.luau"}
    assert [p for p in sorted(baseline) if baseline[p]!=result[p]]==["server/Game.server.luau"]
    assert all(result[k]==v for k,v in baseline.items() if k!="server/Game.server.luau")
    assert len([p for p in result if p.endswith(".server.luau")])==2
    assert len([p for p in result if p.endswith(".client.luau")])==5
    assert len([p for p in result if p.endswith("/Game.server.luau")])==1
    assert gitblob(result["server/H2FiveEggRules.luau"])==BLOBS["server/H2FiveEggRules.luau"]
    source=game
    # All old roles, combat and Sky+Sea and first egg-joy retained; no alternate Game/Remote.
    for src in ("server/Game.server.luau","client/HUD.client.luau",
                "server/H1FunWorld.server.luau","client/D18MascotGuide.client.luau",
                "client/EggJoy.client.luau"):
        assert src in result,src
    assert source.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert source.count("remote.OnServerEvent:Connect(")==1
    assert source.count("H2Score.pickup(")==1
    assert source.count("H2Score.deposit(")==1
    assert source.count("H2Score.advance(")==1
    assert source.count("H2Score.drop(")==1
    assert source.count('map.teams[team].eggPrompt.Triggered:Connect')==1
    assert source.count('map.teams[team].scorePrompt.Triggered:Connect')==1
    assert "stopWind(player)" in source and "TrapRules.canPlace({" in source
    for id in ("R1","R2","B1","B2","N1"):
        assert id in source
    assert "FIVE_EGG_SCORE_240S" in source
    assert "H2_REAL_H1_FIVE_EGG_INTEGRITY" in source
    assert "H2FiveEggRules" in source
    assert 'Models.create("SPACE",creatures)' in result["server/H1FunWorld.server.luau"].decode()
    assert 'TacticalAlternativeRoute' in result["server/H1FunWorld.server.luau"].decode()
    assert "FireServer" not in result["server/H2FiveEggRules.luau"].decode()
    if mode=="FIVE_EGG_STUDIO":
        assert MODE_LINE in source
    else:
        assert "local EXPERIMENTAL_FIVE_EGG_MODE = false" in source
    receipt={
        "game":"EGG RAID RUMBLE",
        "internal_game_id":"TRAP_RAIDERS",
        "adoption":"EXPERIMENTAL_H2_NOT_OFFICIAL_RC",
        "original_full_h1_sha":"1f63a529dc512487145cea86557d38cec7f19e03",
        "original_full_h1_script_count":30,
        "new_full_game_script_count":31,
        "only_existing_script_replaced":"server/Game.server.luau",
        "original_other_29_scripts_unchanged":True,
        "one_additional_original_h2_rule_script":"server/H2FiveEggRules.luau",
        "mode":mode,
        "non_Studio_scored_game_enabled":False,
        "Studio2client_tested":False,
        "mobile_tested":False,
        "human_fun_gate":"NO_GO_NOT_TESTED",
        "5_egg_identities":["R1","R2","B1","B2","N1"],
        "physical_paths":"ORIGINAL_H1_6_SEA_SKY_FAST",
        "existing_canonical_Game_count":1,
        "existing_game_Remote_count":1,
        "original30_gitblobs":{k:gitblob(v) for k,v in baseline.items()},
        "actual31_gitblobs":{k:gitblob(v) for k,v in result.items()},
        "paid_features":False,"published":False,"official_RC_adopted":False,
        "hatch_6_category_persisted_and_usable":False
    }
    (dst/"SOURCE_LOCK.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("P0D_EGG_RUMBLE_REAL_SINGLE_GAME_FULL_H1_"+mode+"_31_LUAU_STAGED_PASS")
    return dst

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--mode",required=True,choices=["ORIGINAL_RULES","FIVE_EGG_STUDIO"])
    args=p.parse_args()
    assemble(args.mode)
