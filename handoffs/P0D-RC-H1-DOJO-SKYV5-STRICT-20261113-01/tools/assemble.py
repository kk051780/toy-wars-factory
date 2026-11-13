#!/usr/bin/env python3
"""Source-locked integration of the two author-proven safety fixes into H1 45 Place.

Existing rich 45 B42 + V7 Horde + sky + latched solo + author AFK dojo + 4-stage
diagnostic is reconstructed using its exact historical assembler. EXACT TWO
independent author files replace world and Studio-only observer ONLY; Game,
HUD, Dojo, Horde, eggs, persistence, Remote and every other source byte unchanged.
Official rc/main are neither read-write nor checked out.
"""
from pathlib import Path
import argparse,hashlib,json,shutil,subprocess,sys

HERE=Path(__file__).resolve()
ROOT=HERE.parents[1]
REPO=HERE.parents[3]
UP=REPO/"handoffs/P0D-RC-B42V7-SKY-SOLO-DOJO-H1-20261113-01"
BASE=UP/"dist/P0D_B42_V7_SKYCASTLE_LATCH_AUDIT_DOJO_H1_PRIVATE"
DIST=ROOT/"dist/P0D_H1_DOJO_SKYV5_STRICT4_PRIVATE"
WORLD=ROOT/"src/H1FunWorld_SKYCASTLE_GROUNDDOCK_V5.server.luau"
OBSERVER=ROOT/"src/P0DStudioTrialAudit_STRICT_V4.client.luau"
ORIGINAL_RICH_SHA="a3dfc9b98f22b8edf0a7d0d978d65b1072aed933"
ORIGINAL_H1_DOJO_SHA="79804116b0a144a33c6466340cfb476eefa3ca4d"
GROUND_AUTHOR_SHA="f607cf4de4ac50e1e886adbd5b9f6070fe5c0450"
GROUND_WORLD_BLOB="7a90affd4eb7eebcdfba39d833a2875ff665d5cf"
GROUND_BEFORE_BLOB="0a6360392f4384dc2f0ab1e9afc1d840d66a22b8"
STRICT_AUDIT_AUTHOR_SHA="634c26a6b698c25a339fc948169c58c4773e9810"
STRICT_AUDIT_BLOB="ee96518a7eeaaaba98d2a8e2aff6dad780fae8c7"
PREVIOUS_AUDIT_BLOB="b09e5fa2b3374cb88cad789b2c4966d4c777b3ef"
ORIGINAL_DOJO_BLOB="120bac439c979310c9ddeb2fcf2ffa002b6d1add"
LATCH_SOLO_BLOB="de0e0df12346de2b4e7b607c74eddaaac693dc99"

def blob(raw):
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def sources(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def assemble():
    assert not BASE.exists() and not DIST.exists(),"FAIL_CLOSED_REFUSE_DIST_OVERWRITE"
    assert blob(WORLD.read_bytes())==GROUND_WORLD_BLOB,"SOURCE_DRIFT_WORLD"
    assert blob(OBSERVER.read_bytes())==STRICT_AUDIT_BLOB,"SOURCE_DRIFT_AUDIT"
    world=WORLD.read_text("utf8")
    strict=OBSERVER.read_text("utf8")
    assert world.count('local world=Instance.new("Folder")')==1
    assert world.count('local fort=box("FLOATING_SKY_ISLAND"')==1
    assert world.count('world:SetAttribute("GroundDocksPhysical",4)')==1
    for p in ("SKY_GROUND_BOOT_RED","SKY_GROUND_BOOT_BLUE",
              "SKY_SCORE_DOCK_RED","SKY_SCORE_DOCK_BLUE"):
        assert world.count('path("'+p+'"')==1
    for term in ('SKY_WITH_EGG','SCORE_AFTER_SKY','ROUTE_RESET',
                 'SCORE_NOT_QUALIFIED','workspace:Raycast',
                 '-- SOURCE_QA_NATIVE_BEGIN','-- SOURCE_QA_NATIVE_END'):
        assert term in strict,term
    for forbidden in ('FireServer(', 'Instance.new("RemoteEvent")',
                      'OnServerEvent:Connect(', 'GetDataStore(', 'UpdateAsync('):
        assert forbidden not in world and forbidden not in strict,forbidden
    assert strict.count('if not RunService:IsStudio() then return end')==1
    subprocess.run([sys.executable,"-B",str(UP/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,check=True)
    prior=sources(BASE)
    assert len(prior)==45,len(prior)
    base=json.loads((BASE/"SOURCE_LOCK.json").read_text("utf8"))
    assert base["all_scripts"]==45 and base["base_scripts_unchanged"]==42
    assert base["official_rc_adopted"] is False
    assert blob(prior["server/H1FunWorld.server.luau"])==GROUND_BEFORE_BLOB
    assert blob(prior["client/P0DStudioTrialAudit.client.luau"])==PREVIOUS_AUDIT_BLOB
    assert blob(prior["server/DojoRules.luau"])==ORIGINAL_DOJO_BLOB
    assert blob(prior["server/StudioSoloPreviewRules.luau"])==LATCH_SOLO_BLOB
    shutil.copytree(BASE,DIST)
    (DIST/"src/server/H1FunWorld.server.luau").write_bytes(WORLD.read_bytes())
    (DIST/"src/client/P0DStudioTrialAudit.client.luau").write_bytes(OBSERVER.read_bytes())
    config=DIST/"default.project.json"
    proj=json.loads(config.read_text("utf8"))
    assert proj["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    assert proj["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DStudioTrialAudit"]["$path"]=="src/client/P0DStudioTrialAudit.client.luau"
    proj["name"]="P0D_H1_DOJO_SKYV5_STRICT4_STUDIO_PRIVATE"
    config.write_text(json.dumps(proj,indent=2,ensure_ascii=False)+"\n","utf8")
    after=sources(DIST)
    assert len(after)==45
    assert set(after)==set(prior)
    changed=sorted(k for k in prior if after[k]!=prior[k])
    assert changed==["client/P0DStudioTrialAudit.client.luau",
                    "server/H1FunWorld.server.luau"],changed
    assert len(prior)-len(changed)==43
    for p in prior:
        if p not in changed:
            assert after[p]==prior[p],p
    assert blob(after[changed[0]])==STRICT_AUDIT_BLOB
    assert blob(after[changed[1]])==GROUND_WORLD_BLOB
    game=after["server/Game.server.luau"].decode("utf8")
    hud=after["client/HUD.client.luau"].decode("utf8")
    assert game.count('remote.OnServerEvent:Connect(')==1
    assert game.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game.count('local function tickRound()')==1
    assert game.count('local function resetRound()')==1
    assert game.count('Dojo.tick(')==1
    assert game.count('Dojo.pveDamageMultiplier(')==2
    assert game.count('StudioSolo.isSoloRound(')==1
    assert game.count('horde:tick(')==1
    assert game.count('H2Score.deposit(')==1
    assert game.count('scorePrompt.Triggered:Connect(')==1
    assert hud.count('dojoBadge.Visible=valid')==1
    assert len([p for p in after if p.endswith(".server.luau")])==2
    assert len([p for p in after if p.endswith(".client.luau")])==6
    receipt={
       "status":"UNPUBLISHED_45_RICH_DOJO_SKY_V5_STRICT4_OWNER_STUDIO_AB_ONLY",
       "base_private_45_source_sha":ORIGINAL_H1_DOJO_SHA,
       "original_rich_game_sha":ORIGINAL_RICH_SHA,
       "world_author_sha":GROUND_AUTHOR_SHA,
       "world_author_blob":GROUND_WORLD_BLOB,
       "strict_audit_author_sha":STRICT_AUDIT_AUTHOR_SHA,
       "strict_audit_author_blob":STRICT_AUDIT_BLOB,
       "original_scripts":45,
       "identical_to_previous":43,
       "changed":changed,
       "new_scripts":[],"total_scripts":45,
       "one_game":True,"one_remote":True,
       "world_ground_docks":4,
       "ground_entry_red_blue":True,"ground_exit_red_blue":True,
       "real_ground_walkability":"NOT_TESTED",
       "strict_single_egg_sky_score_observer":True,
       "strict_view_4of4_engine":"NOT_TESTED",
       "original_b42_1_and_5_eggs":True,
       "original_v7_horde":True,
       "original_dojo_beast_weapon":True,
       "original_studio_solo_latch":True,
       "six_skill_v4":False,"dojo_persistence":False,
       "published":False,"paid":False,"official_rc_adopted":False,
       "owner_fun":"NOT_TESTED","studio_1client":"NOT_TESTED",
       "studio_2client":"NOT_TESTED","android":"NOT_TESTED",
       "blobs":{p:blob(d) for p,d in sorted(after.items())}
    }
    (DIST/"SOURCE_LOCK.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_H1_DOJO_SKYV5_STRICT4_SOURCE_45_EXACT_43_UNCHANGED_PASS")
    return receipt

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--assemble",required=True,action="store_true")
    p.parse_args()
    assemble()
