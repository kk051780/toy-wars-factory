#!/usr/bin/env python3
"""#372 FB015 five-slice cumulative VISUAL PREP against the real official RC66.

A private 71-Luau source-locked, same-HEAD Rojo trial, NOT an official RC
promotion, not a Studio/Android/FUN acceptance. Five existing authored,
pinned source files are copied byte-identically; no reimplementation.
Only NEW visuals; original 66 Game/Horde/HUD/Map/Remote/Store untouched.
Do not feed N>66 official head into this strict fixture. B #220 MUST integrate
each current-head reviewed source, not blind merge a private candidate.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "FB015_FIVE_ART_CUMULATIVE_PREVIEW_V1"
BASE = 66
PREPS = (
    ("ART-CASTLE", "OWNER361_CASTLE_WORLD_ADDON_V1",
     "composite5/CastleBattlefield.server.luau",
     "server/CastleBattlefield.server.luau",
     "3599f7a86be2956d2ecf4f14267dfbb73f8f1074"),
    ("ART-SEA", "FB011_H1_COASTAL_SEASCAPE_V1",
     "composite5/H1CoastalSeascape.server.luau",
     "server/H1CoastalSeascape.server.luau",
     "44b39c3d8b0df9290c86a139318ca1bf68356814"),
    ("ART-WORLD", "FB015_ART_WORLD_LIGHT_FOLIAGE_V1",
     "composite5/FantasyWorldArt.server.luau",
     "server/FantasyWorldArt.server.luau",
     "f2a1d58ab4420c0f331adb8f6d9d0478cf32ad4a"),
    ("ART-MINION", "ART_MINION_THREE_SILHOUETTES_V1",
     "composite5/MinionArtSilhouette.server.luau",
     "server/ArtMinionSilhouette.server.luau",
     "ed5cd56789abc4a7bc8ee3a44b8982aae4f3ff62"),
    ("ART-COMBAT", "FB008_CONFIRMED_HIT_SLASH_VFX_V1",
     "composite5/ConfirmedSlashFX.client.luau",
     "client/ConfirmedSlashFX.client.luau",
     "4b1dce5635b709d349ab3f00bba7a7cf9d9883bd"),
)
CLIENT_PROJECT_NAME = "P0DConfirmedCombatFX"


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def source_map(dist: Path) -> dict[str, bytes]:
    src = dist/"src"
    assert src.is_dir(), "FIVE_ART_MISSING_DIST"
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}


def safety() -> dict[str, bytes]:
    authored = {}
    for category, feat, path, dest, pin in PREPS:
        content = (ROOT/"features"/path).read_bytes()
        assert gitblob(content) == pin, ("FIVE_ART_SOURCE_DRIFT", category)
        text = content.decode("utf8")
        assert "RunService:IsStudio()" in text, ("FIVE_ART_NOT_STUDIO_ONLY", category)
        assert len(content) > 2000
        if category == "ART-CASTLE":
            assert "GrassArena" in text and "NORTH_WOODLAND_TRAIL" in text
            assert "BLUE_CASTLE" in text and "RED_CASTLE" in text
        elif category == "ART-SEA":
            assert "COSMETIC_SEA" in text
            assert 'Terrain' in text and "SEA_BOARDWALK_DECK_" in text
        elif category == "ART-WORLD":
            assert "Lighting" in text and "P0D_FB015_WORLD_ART_V1" in text
        elif category == "ART-MINION":
            assert "MUSOU_MINION_" in text and "MUSOU_ELITE_TELEGRAPH" in text
        else:
            assert "RealDamagePopup" in text and "CONFIRMED_HIT_SLASH_" in text
            assert "Players.LocalPlayer" in text
        for forbidden in (
            'Instance.new("RemoteEvent")', "FireServer(", "OnServerEvent:Connect(",
            "DataStoreService", "MarketplaceService", "TakeDamage(", "UpdateAsync(",
            "PromptProductPurchase(", "TeleportService",
        ):
            assert forbidden not in text, ("FIVE_ART_SECOND_AUTHORITY", category, forbidden)
        assert dest not in authored, ("FIVE_ART_DUPLICATE_DEST", dest)
        authored[dest] = content
    assert len(authored) == len(PREPS) == 5
    assert len({r[1] for r in PREPS}) == 5
    return authored


def apply(dist: Path, enabled: bool) -> bool:
    if not enabled:
        print("FIVE_ART_COMPOSITE_OFF_ALL_SOURCE_LOCK_PROJECT_NO_WRITE")
        return False

    authored = safety()
    old = source_map(dist)
    assert len(old) == BASE, ("FIVE_ART_REQUIRES_OFFICIAL66", len(old))
    assert not (set(old) & set(authored)), "FIVE_ART_ALREADY_PRESENT"
    for required in (
        "server/Game.server.luau", "server/MusouHorde.luau",
        "server/MapBuilder.luau", "server/H1FunWorld.server.luau",
        "client/HUD.client.luau",
    ):
        assert required in old, ("FIVE_ART_GAME_SOURCE_MISSING", required)
    assert old["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1
    assert b"RealDamagePopup" in old["server/MusouHorde.luau"]
    assert b"EGG_RUMBLE_NEUTRAL_MUSOU_EXPERIMENT" in old["server/MusouHorde.luau"]
    assert b"COSMETIC_SEA" in old["server/H1FunWorld.server.luau"]

    pins = {p: gitblob(v) for p,v in sorted(old.items())}
    source_path=dist/"SOURCE_LOCK.json"
    feature_path=dist/"RC_FEATURE_LOCK.json"
    project_path=dist/"default.project.json"
    sl=json.loads(source_path.read_text("utf8"))
    fl=json.loads(feature_path.read_text("utf8"))
    project=json.loads(project_path.read_text("utf8"))
    assert sl["total_scripts"] == BASE and sl["blobs"] == pins, "FIVE_ART_SOURCE_LOCK_DRIFT"
    assert fl["total_sources"] == BASE and fl["source_gitblobs"] == pins, "FIVE_ART_FEATURE_LOCK_DRIFT"
    assert FEATURE not in fl["feature_flags"], "FIVE_ART_ALREADY_ADOPTED"
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    scripts=project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert any(isinstance(v,dict) and v.get("$path")=="src/client/HUD.client.luau"
               for v in scripts.values())
    assert CLIENT_PROJECT_NAME not in scripts
    scripts[CLIENT_PROJECT_NAME]={"$path":"src/client/ConfirmedSlashFX.client.luau"}
    assert len(set(scripts)) == len(scripts)

    total = dict(old)
    total.update(authored)
    assert len(total)==BASE+5
    updated = {p:gitblob(v) for p,v in sorted(total.items())}
    receipt={
        "id": FEATURE, "status":"SOURCE_COMPOSITE_PREP_NOT_OFFICIAL",
        "base_scripts":BASE, "private_candidate_scripts":BASE+5,
        "original66_all_bytes_identical":True, "no_new_authority":True,
        "one_existing_Game_Remote":True,
        "categories":[row[0] for row in PREPS],
        "features":[row[1] for row in PREPS],
        "preparation_sources":[{"category":cat,"feature":feat,"source":path,
                                "dest":dest,"blob":pin}
                               for cat,feat,path,dest,pin in PREPS],
        "owner_approved":False,
        "studio_single_player":"NOT_TESTED",
        "studio_two_clients":"NOT_TESTED",
        "android_fps":"NOT_TESTED",
        "castle_sea_world_overlap":"UNTESTED_STUDIO_REVIEW_REQUIRED",
        "solo_bots":"MISSING_NOT_IN_THIS_CANDIDATE",
        "lobby_dojos":"MISSING_NOT_IN_THIS_CANDIDATE",
        "rollback":"do not apply these five, or --enabled false does no writes",
    }
    sl["total_scripts"]=len(total)
    sl["blobs"]=updated
    sl["rc_five_art_composite"]=receipt
    fl["total_sources"]=len(total)
    fl["source_gitblobs"]=updated
    fl["feature_flags"][FEATURE]=True
    fl["rc_five_art_composite"]=receipt
    # All preflight/checks above must pass before writing ANYTHING.
    for dest,content in authored.items():
        target=dist/"src"/dest
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(content)
    project_path.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n","utf8")
    source_path.write_text(json.dumps(sl,ensure_ascii=False,indent=2)+"\n","utf8")
    feature_path.write_text(json.dumps(fl,ensure_ascii=False,indent=2)+"\n","utf8")
    after=source_map(dist)
    assert len(after)==71
    assert all(after[p]==v for p,v in old.items()), "FIVE_ART_ORIGINAL_SCRIPT_CHANGED"
    assert all(after[p]==v for p,v in authored.items()), "FIVE_ART_AUTHORED_SCRIPT_CHANGED"
    print("P0D_FIVE_ART_REAL_RICH66_TO_PRIVATE71_ALL66_EXACT_AND_FIVE_PINNED_PASS")
    return True


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--dist",type=Path,required=True)
    parser.add_argument("--enabled",choices=("true","false"),required=True)
    args=parser.parse_args()
    apply(args.dist,args.enabled=="true")


if __name__=="__main__":
    main()
