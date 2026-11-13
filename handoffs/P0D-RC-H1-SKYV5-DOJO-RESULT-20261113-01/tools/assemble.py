#!/usr/bin/env python3
"""Read-only owner private results advisor over the actual 45 Luau H1 SkyV5 Dojo.

No Gameplay authority files are modified. Exact original author pure advisor
+ one Studio-only client projection. Does not invent solo KOs/rescues/hatches.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys

HERE=Path(__file__).resolve()
ROOT=HERE.parents[1]
REPO=HERE.parents[3]
PRIOR=REPO/"handoffs/P0D-RC-H1-DOJO-SKYV5-STRICT-20261113-01"
BASE=PRIOR/"dist/P0D_H1_DOJO_SKYV5_STRICT4_PRIVATE"
DIST=ROOT/"dist/P0D_H1_SKYV5_DOJO_RESULT7_STUDIO_PRIVATE"
ADVISOR=ROOT/"src/NextStepAdvisor.luau"
CLIENT=ROOT/"src/ResultNextStep.client.luau"
ADVISOR_BLOB="d212dae56b328d48bfed5dafa742caff9afe82c7"
CLIENT_BLOB="82266497751a15945f1a87c66a3b9d15738e0a03"
BASE_WORLD_BLOB="7a90affd4eb7eebcdfba39d833a2875ff665d5cf"
BASE_STRICT_BLOB="ee96518a7eeaaaba98d2a8e2aff6dad780fae8c7"
BASE_DOJO_BLOB="120bac439c979310c9ddeb2fcf2ffa002b6d1add"
BASE_SOLO_BLOB="de0e0df12346de2b4e7b607c74eddaaac693dc99"

def blob(raw:bytes)->str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def sources(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def assemble():
    assert not BASE.exists() and not DIST.exists(),"NO_OVERWRITE_PRIOR_DIST"
    assert blob(ADVISOR.read_bytes())==ADVISOR_BLOB,"AUTHOR_ADVISOR_DRIFT"
    assert blob(CLIENT.read_bytes())==CLIENT_BLOB,"STUDIO_CLIENT_SOURCE_DRIFT"
    advisor=ADVISOR.read_text("utf8")
    client=CLIENT.read_text("utf8")
    assert advisor.count("function Advisor.build(")==1 and advisor.count("return Advisor")==1
    assert 'if not RunService:IsStudio() then return end' in client
    assert client.count('remote.OnClientEvent:Connect(')==1
    assert client.count('task.delay(7,')==1
    assert client.count('local function summarize(')==1
    assert 'canHatch=false' in client
    assert 'availableSkills={"beast", "weapon"}' in client
    assert 'type(snapshot.dojo)' in client
    assert 'チーム得点' in client
    assert 'musouLastKOs' not in client and 'neutralDefeats=' not in client
    for invalid in ('FireServer(', 'FireClient(', 'OnServerEvent:Connect(',
                    'GetDataStore(', 'UpdateAsync(', 'MarketplaceService',
                    'PromptProductPurchase('):
        assert invalid not in advisor and invalid not in client,invalid
    subprocess.run([sys.executable,"-B",str(PRIOR/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,check=True)
    before=sources(BASE)
    assert len(before)==45,len(before)
    lock=json.loads((BASE/"SOURCE_LOCK.json").read_text("utf8"))
    assert lock["total_scripts"]==45 and lock["identical_to_previous"]==43
    assert lock["official_rc_adopted"] is False
    for path,digest in {
        "server/H1FunWorld.server.luau":BASE_WORLD_BLOB,
        "client/P0DStudioTrialAudit.client.luau":BASE_STRICT_BLOB,
        "server/DojoRules.luau":BASE_DOJO_BLOB,
        "server/StudioSoloPreviewRules.luau":BASE_SOLO_BLOB
    }.items():
        assert blob(before[path])==digest,path
    shutil.copytree(BASE,DIST)
    (DIST/"src/client/ResultNextStep.client.luau").write_bytes(CLIENT.read_bytes())
    (DIST/"src/shared/NextStepAdvisor.luau").write_bytes(ADVISOR.read_bytes())
    cfg=DIST/"default.project.json"
    data=json.loads(cfg.read_text("utf8"))
    assert data["tree"]["ReplicatedStorage"]["TrapRaidersShared"]["$path"]=="src/shared"
    starter=data["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert starter["P0DStudioTrialAudit"]["$path"]=="src/client/P0DStudioTrialAudit.client.luau"
    assert "ResultNextStep" not in starter
    starter["ResultNextStep"]={"$path":"src/client/ResultNextStep.client.luau"}
    data["name"]="P0D_H1_SKYV5_DOJO_READONLY_RESULT7_PRIVATE"
    cfg.write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n","utf8")
    after=sources(DIST)
    assert len(after)==47,len(after)
    assert sorted(set(after)-set(before))==[
        "client/ResultNextStep.client.luau",
        "shared/NextStepAdvisor.luau"]
    assert not (set(before)-set(after))
    for path in before:
        assert after[path]==before[path],path
    assert blob(after["shared/NextStepAdvisor.luau"])==ADVISOR_BLOB
    assert blob(after["client/ResultNextStep.client.luau"])==CLIENT_BLOB
    assert sum(p.endswith(".server.luau") for p in after)==2
    assert sum(p.endswith(".client.luau") for p in after)==7
    assert sum(p.endswith("/Game.server.luau") for p in after)==1
    game=after["server/Game.server.luau"].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count('Dojo.tick(')==1
    assert game.count('scorePrompt.Triggered:Connect(')==1
    assert game.count('StudioSolo.isSoloRound(')==1
    receipt={
        "status":"P0D_PRIVATE_47_READONLY_RESULT_NEXT_STEP_H1",
        "prior_45_source_head":"646cd9bd18b3428235ada06a763f9c5ac65b6883",
        "author_advisor_exact_source_head":"13d78bfe91db855a04b405b53c8a9d224e99a6b6",
        "author_advisor_exact_blob":ADVISOR_BLOB,
        "original_45_unchanged":45,
        "new_scripts":["client/ResultNextStep.client.luau",
                       "shared/NextStepAdvisor.luau"],
        "total_scripts":47,
        "one_game":True,"one_remote":True,
        "results_card_7_seconds":True,"dismissible":True,
        "studio_only":True,"team_score_only":True,
        "individual_KOs_not_claimed":True,"rescues_not_claimed":True,
        "hatch_readiness_not_claimed":True,
        "server_verified_evolution_flag":True,
        "dojo_beast_weapon_actual":True,
        "six_skill_v4":False,"dojo_persistence":False,
        "published":False,"paid":False,"official_rc_adopted":False,
        "studio_1client":"NOT_TESTED",
        "studio_2client":"NOT_TESTED",
        "android":"NOT_TESTED","owner_fun":"NOT_TESTED",
        "blobs":{p:blob(raw) for p,raw in sorted(after.items())}
    }
    (DIST/"SOURCE_LOCK.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_H1_RESULT_ADVISOR_47_SOURCES_ALL_45_PRIOR_BYTE_IDENTICAL_PASS")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",required=True,action="store_true")
    p.parse_args()
    assemble()
