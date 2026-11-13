#!/usr/bin/env python3
"""Actual private H1 rich-game assembly: existing #220 latched SOLO+audit 44 +
exact feature-owner DojoRules and original author Game/HUD patch => 45 Luau.
This is NOT a 6-track V4/paid/stored dojo. Fail closed on any source drift.
"""
from __future__ import annotations
import argparse, hashlib, json, pathlib, runpy, shutil, subprocess, sys

HERE=pathlib.Path(__file__).resolve()
ROOT=HERE.parents[1]
REPO=HERE.parents[3]
ORIGINAL=REPO/"handoffs/P0D-RC-B42V7-SKY-SOLO-20261113-01"
PREVIEW=ORIGINAL/"dist/EGG_RAID_RUMBLE_B42_V7_SKYCASTLE_SOLO_UNPUBLISHED"
DIST=ROOT/"dist/P0D_B42_V7_SKYCASTLE_LATCH_AUDIT_DOJO_H1_PRIVATE"
AUTHOR=ROOT/"tools/author_dojo_patch.py"
DOJO=ROOT/"src/DojoRules.luau"
AUTHOR_PATCH_BLOB="850194ede74b426e003a08dfa1a80205a713e649"
AUTHOR_RULE_BLOB="120bac439c979310c9ddeb2fcf2ffa002b6d1add"
BASE_AUDIT_BLOB="b09e5fa2b3374cb88cad789b2c4966d4c777b3ef"
BASE_SOLO_BLOB="de0e0df12346de2b4e7b607c74eddaaac693dc99"
H1_DOJO_SOURCE_SHA="ce4e1ebcf6d16313c9d144c56129bdfae548e1bf"
FULL_RICH_ORIGINAL_SHA="a3dfc9b98f22b8edf0a7d0d978d65b1072aed933"

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

def scripts(root):
    return {p.relative_to(root/"src").as_posix():p.read_bytes()
            for p in sorted((root/"src").rglob("*.luau"))}

def assemble():
    assert not PREVIEW.exists() and not DIST.exists(), "FAIL_CLOSED_REFUSE_EXISTING_DIST"
    assert blob(AUTHOR.read_bytes())==AUTHOR_PATCH_BLOB,"AUTHOR_PATCH_DRIFT"
    assert blob(DOJO.read_bytes())==AUTHOR_RULE_BLOB,"AUTHOR_DOJO_RULE_DRIFT"
    subprocess.run([sys.executable,"-B",str(ORIGINAL/"tools/assemble.py"),"--assemble"],
                   cwd=REPO,check=True)
    old=scripts(PREVIEW)
    assert len(old)==44,len(old)
    receipt=json.loads((PREVIEW/"SOURCE_LOCK.json").read_text(encoding="utf8"))
    assert receipt["script_total"]==44 and receipt["unchanged_original_h1_scripts"]==41
    assert receipt["audit_original_author_blob"]==BASE_AUDIT_BLOB
    assert receipt["solo_latched_at_round_start"] is True
    assert receipt["official_rc_adopted"] is False
    assert blob(old["server/StudioSoloPreviewRules.luau"])==BASE_SOLO_BLOB
    assert blob(old["client/P0DStudioTrialAudit.client.luau"])==BASE_AUDIT_BLOB

    # Import exactly original feature owner's source patch only, not its own
    # assembler main() (which would create a colliding third private build).
    author=runpy.run_path(str(AUTHOR))
    assert callable(author["patch_game"]) and callable(author["patch_hud"])
    shutil.copytree(PREVIEW,DIST)
    (DIST/"src/server/DojoRules.luau").write_bytes(DOJO.read_bytes())
    game=DIST/"src/server/Game.server.luau"
    hud=DIST/"src/client/HUD.client.luau"
    game.write_text(author["patch_game"](old["server/Game.server.luau"].decode("utf8")),
                    encoding="utf8")
    hud.write_text(author["patch_hud"](old["client/HUD.client.luau"].decode("utf8")),
                   encoding="utf8")
    cfgpath=DIST/"default.project.json"
    config=json.loads(cfgpath.read_text("utf8"))
    assert config["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"]=="src/server"
    assert config["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DStudioTrialAudit"]["$path"]=="src/client/P0DStudioTrialAudit.client.luau"
    config["name"]="P0D_B42_V7_SKY_SOLO_LATCH_AUDIT_DOJO_H1_PRIVATE"
    cfgpath.write_text(json.dumps(config,ensure_ascii=False,indent=2)+"\n","utf8")

    new=scripts(DIST)
    assert len(new)==45 and len(old)==44
    assert sorted(set(new)-set(old))==["server/DojoRules.luau"]
    changed=sorted(k for k in old if new[k]!=old[k])
    assert changed==["client/HUD.client.luau","server/Game.server.luau"],changed
    for p in old:
        if p not in changed:
            assert old[p]==new[p],p
    assert blob(new["server/DojoRules.luau"])==AUTHOR_RULE_BLOB
    assert new["client/P0DStudioTrialAudit.client.luau"]==old["client/P0DStudioTrialAudit.client.luau"]
    assert new["server/StudioSoloPreviewRules.luau"]==old["server/StudioSoloPreviewRules.luau"]

    game_text=new["server/Game.server.luau"].decode("utf8")
    hud_text=new["client/HUD.client.luau"].decode("utf8")
    for marker in ["StudioSolo.isSoloRound(","studioSoloRoundStarted, count,",
                   "Dojo.tick(","Dojo.view(","Dojo.pveDamageMultiplier(",
                   "horde:tick(","First90WaypointRules","Evolution.nextEvolution("]:
        assert marker in game_text,marker
    assert game_text.count('remote.OnServerEvent:Connect(')==1
    assert game_text.count('remote.Name = "TrapRaidersS1Remote"')==1
    assert game_text.count('local function tickRound()')==1
    assert game_text.count('local function resetRound()')==1
    assert game_text.count('local dojoPads:')==1
    assert game_text.count('player:IsFriendsWith(other.UserId)')==1
    assert game_text.count('Dojo.pveDamageMultiplier(')==2
    assert "DojoRules" in game_text and 'status.Text = phaseText(s)' in hud_text
    assert hud_text.count('remote:FireServer(')==3
    assert hud_text.count('dojoBadge.Visible=valid')==1
    assert len([p for p in new if p.endswith(".server.luau")])==2
    assert len([p for p in new if p.endswith(".client.luau")])==6
    assert len([p for p in new if p.endswith(".luau")])==45

    receipt={
       "status":"ISOLATED_RICH_B42_V7_PHYSICAL_SKY_LATCH_AUDIT_BEAST_WEAPON_DOJO_H1_PRIVATE",
       "source_head_game_origin":FULL_RICH_ORIGINAL_SHA,
       "source_author_dojo_commit":H1_DOJO_SOURCE_SHA,
       "source_author_dojo_blob":AUTHOR_RULE_BLOB,
       "source_author_patch_blob":AUTHOR_PATCH_BLOB,
       "source_author_studio_audit_blob":BASE_AUDIT_BLOB,
       "original_base_scripts":44,"base_scripts_unchanged":42,
       "changed_from_original_preview":changed,
       "added":["server/DojoRules.luau"],
       "all_scripts":45,"authoritative_Game":1,"authoritative_Remote":1,
       "latched_1player_Studio_round":True,"on_screen_4stage_observer":True,
       "actual_beast_weapon_dojo":True,"mirrored_pad_count":4,
       "friend_bonus_confirmed_same_server_boolean":1.5,
       "max_session_level":5,"pve_bonus_max":1.2,"pvp_bonus":1,
       "dojo_session_only":True,"dojo_persistence":False,
       "six_disciplines_v4":False,"focus_30min_v4":False,
       "paid":False,"published":False,
       "official_rc_adopted":False,"owner_fun":"NOT_TESTED",
       "roblox_studio_1client":"NOT_TESTED",
       "roblox_studio_2client":"NOT_TESTED",
       "mobile_android":"NOT_TESTED",
       "blobs":{k:blob(v) for k,v in sorted(new.items())}
    }
    (DIST/"SOURCE_LOCK.json").write_text(
        json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
    print("P0D_RICH_H1_DOJO_LATCH_AUDIT_45_SOURCE_LOCK_PASS")
    return receipt

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--assemble",action="store_true",required=True)
    parser.parse_args()
    assemble()
