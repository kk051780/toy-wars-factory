#!/usr/bin/env python3
"""P0D first real EIGHT-feature cumulative Studio candidate from canonical RC66.

Sources from original contributor PRs #366 #377 #370 #374 #373 stay pinned
by exact Gitblob. The official RC66 distribution remains byte identical.
This script creates only a PRIVATE candidate for technical/visual inspection.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent
ART = ROOT / "features/art_composite_sources"
SPECS = (
    ("CASTLE", "47ebb70057d56df106bdd30745aa0c1c5d7748aa", "server/CastleBattlefield.server.luau", "CastleBattlefield.server.luau", "OWNER361_CASTLE_WORLD_ADDON_V1"),
    ("CASTLE_DETAIL", "da2bf0544682f72ee02280374a27ce2f4fadb5c2", "server/CastleDetailArt.server.luau", "CastleDetailArt.server.luau", "FB015_FORTRESS_DETAIL_ART_V2"),
    ("WORLD", "dc741ec6d0506cfebf82631cf3583dd4037fbea9", "server/FantasyWorldArt.server.luau", "FantasyWorldArt.server.luau", "FB015_ART_WORLD_LIGHT_FOLIAGE_V1"),
    ("SEA", "44b39c3d8b0df9290c86a139318ca1bf68356814", "server/H1CoastalSeascape.server.luau", "H1CoastalSeascape.server.luau", "FB011_H1_COASTAL_SEASCAPE_V1"),
    ("COAST_CHANNEL", "652bbcb31d91810a8d5d65d25e769c18ddd1f20f", "server/H1SeaGroundRepair.server.luau", "H1SeaGroundRepair.server.luau", "FB015_REAL_SEA_GROUND_V2"),
    ("MINION", "44b411c84b724a09d4b64dcf0b727c7296b17775", "server/ArtMinionSilhouette.server.luau", "MinionArtSilhouette.server.luau", "ART_MINION_THREE_SILHOUETTES_V1"),
    ("BEAST", "bae36c1a22ea649acfed069f5f3ebbc403c3b456", "client/FB015CharacterArt.client.luau", "FB015CharacterArt.client.luau", "FB015_GOROGAN_BEAST_VISUAL_V2"),
    ("HUD", "20536bc52b108edf94564013e2900aa25bd3aaf3", "client/BattleHUDGovernor.client.luau", "BattleHUDGovernor.client.luau", "P0D_HUD_CLEAR_COMBAT_V1"),
)


def gitblob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def source_files(dist: Path) -> dict[str, bytes]:
    src = dist / "src"
    assert src.is_dir(), ("DISTRIBUTION_MISSING", src)
    return {p.relative_to(src).as_posix(): p.read_bytes()
            for p in sorted(src.rglob("*.luau"))}


def pinned_art() -> dict[str, bytes]:
    sources = {}
    for category, pin, path, basename, flag in SPECS:
        content = (ART / basename).read_bytes()
        assert gitblob(content) == pin, ("UPSTREAM_ART_SOURCE_DRIFT", category)
        assert b"RunService:IsStudio()" in content, ("NOT_STUDIO_SCOPED", category)
        for banned in ("MarketplaceService", "PromptProductPurchase(", "DataStoreService",
                       "UpdateAsync(", "FireServer(", "OnServerEvent:Connect("):
            assert banned.encode("utf8") not in content, ("ART_UNSAFE_AUTHORITY", category, banned)
        sources[path] = content
    assert len(sources) == 8
    assert b"MUSOU_MINION_" not in sources["client/FB015CharacterArt.client.luau"]
    assert b"Gorogan_ServerRig" not in sources["server/ArtMinionSilhouette.server.luau"]
    castle = sources["server/CastleBattlefield.server.luau"]
    assert b"local pz = -94 - math.floor((j - 1) / 3) * 35" in castle
    assert b"local pz = -80" not in castle
    # This is a second *independent* set of trees, distinct from the
    # FantasyWorldArt/forest race fixed on the previous commit.

    world = sources["server/FantasyWorldArt.server.luau"]
    assert b'OWNER361_CASTLE_WORLD_V1' in world
    assert b'ForestPlacedAfterCastleExpanded' in world
    assert b'FB015_FOREST_CASTLE_GEOMETRY_NOT_READY_FAIL_CLOSED' in world
    assert b'ground.Size.Z - 294' in world
    assert b'FindFirstChild("GRAND_KEEP")' in world
    # This prevents a successful 73-source build from silently planting the
    # original 142-depth trees into the new -83..-31 ocean channel.

    return sources


def compose(dist: Path, work: Path) -> tuple[dict[str, bytes], dict, dict]:
    authored = pinned_art()
    before = source_files(dist)
    assert len(before) == 66, ("REQUIRES_LIVE_RC66", len(before))
    assert not authored.keys() & before.keys(), "ART_DUPLICATE_DEST"
    assert "server/Game.server.luau" in before
    assert "server/MusouHorde.luau" in before
    assert "server/GoroganRigDriver.luau" in before
    locks = json.loads((dist / "SOURCE_LOCK.json").read_text("utf8"))
    features = json.loads((dist / "RC_FEATURE_LOCK.json").read_text("utf8"))
    pins = {k:gitblob(v) for k,v in sorted(before.items())}
    assert locks["total_scripts"] == 66 and locks["blobs"] == pins
    assert features["total_sources"] == 66 and features["source_gitblobs"] == pins
    assert features["feature_flags"].get("TWIN_BOND_PVE_COMPANION_V1") is True
    assert before["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1
    assert work != dist and not work.exists()
    shutil.copytree(dist, work)
    for path, content in authored.items():
        target = work / "src" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    after = source_files(work)
    assert len(after) == 74
    assert all(after[k] == v for k,v in before.items()), "CANONICAL66_MUTATED"
    project_path = work / "default.project.json"
    project = json.loads(project_path.read_text("utf8"))
    assert project["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    client = project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
    assert "FB015GoroganVisual" not in client
    assert any(isinstance(x,dict) and x.get("$path")=="src/client/HUD.client.luau" for x in client.values())
    client["FB015GoroganVisual"]={"$path":"src/client/FB015CharacterArt.client.luau"}
    assert "BattleHUDGovernor" not in client, "DUPLICATE_HUD_GOVERNOR"
    client["BattleHUDGovernor"]={"$path":"src/client/BattleHUDGovernor.client.luau"}
    project_path.write_text(json.dumps(project,ensure_ascii=False,indent=2)+"\n","utf8")
    receipt={
        "status":"PRIVATE_PREP_NO_OFFICIAL_RC",
        "owner_art": "FB-015",
        "branch_base":"43543378f976374e2cac2d68b3136ac355d3191b",
        "source_count":74,
        "original_source_count":66,
        "original_66_source_bytes_identical":True,
        "categories":[row[0] for row in SPECS],
        "source_prs":{"CASTLE":366,"CASTLE_DETAIL":382,"WORLD":377,"SEA":370,"MINION":374,"BEAST":373,"HUD":367},
        "source_blobs":{row[2]:row[1] for row in SPECS},
        "single_Game_Remote_Store":True,
        "stages":{"native":"PENDING","rojo":"PENDING","studio_solo":"NOT_TESTED",
                  "studio_2client":"NOT_TESTED","android_fps":"NOT_TESTED",
                  "owner_art":"ART_NO_GO","physics_water":"NOT_TESTED"},
        "known_collision_risk":"castle gate geometry, new noncolliding fortress ornament, coastal Terrain water and forestry routes; Studio physical verification required",
        "rollback":"omit all 8 additive sources; original distribution bytes untouched",
    }
    updated_blobs={k:gitblob(v) for k,v in sorted(after.items())}
    locks["total_scripts"]=74
    locks["blobs"]=updated_blobs
    locks["rc_fb015_eight_feature_composite"]=receipt
    features["total_sources"]=74
    features["source_gitblobs"]=updated_blobs
    for category,pin,path,base,flag in SPECS:
        assert flag not in features["feature_flags"], ("ALREADY_ADOPTED",flag)
        features["feature_flags"][flag]=True
    features["rc_fb015_eight_feature_composite"]=receipt
    (work/"SOURCE_LOCK.json").write_text(json.dumps(locks,ensure_ascii=False,indent=2)+"\n","utf8")
    (work/"RC_FEATURE_LOCK.json").write_text(json.dumps(features,ensure_ascii=False,indent=2)+"\n","utf8")
    assert locks["total_scripts"] == len(after) == features["total_sources"], "LOCK_TOTAL_MUST_MATCH_REAL_SCRIPT_COUNT"
    assert locks["blobs"] == updated_blobs == features["source_gitblobs"], "LOCK_BLOBS_MUST_MATCH_ACTUAL"
    assert source_files(work) == after, "GENERATED_ART_SOURCES_MUST_MATCH_LOCK"
    assert source_files(dist)==before
    return after, receipt, project


def verify_rbxlx(place: Path, actual: dict[str, bytes]) -> None:
    expected=collections.Counter(value.decode("utf8") for value in actual.values())
    included=collections.Counter()
    kinds=collections.Counter()
    for item in ET.fromstring(place.read_bytes()).iter("Item"):
        klass=item.get("class")
        if klass not in ("Script","ModuleScript","LocalScript"):
            continue
        source=item.find("./Properties/string[@name='Source']")
        if source is None:
            continue
        included[source.text or ""] += 1
        n=item.find("./Properties/string[@name='Name']")
        if n is not None:
            kinds[(klass,n.text)] += 1
    assert included == expected, ("PRIVATE74_ROJO_BINARY_SOURCE_MISMATCH",sum(included.values()),len(actual))
    assert kinds[("Script","Game")] == 1, ("GAME_DUPLICATED",kinds)
    for name in ("CastleBattlefield","CastleDetailArt","FantasyWorldArt","H1CoastalSeascape","H1SeaGroundRepair","ArtMinionSilhouette"):
        assert kinds[("Script",name)]==1, ("MISSING_SERVER_ART",name,kinds[("Script",name)])
    assert kinds[("LocalScript","FB015GoroganVisual")]==1
    assert kinds[("LocalScript","BattleHUDGovernor")]==1
    assert sum(included.values())==74
    print("FB015_EIGHT_FEATURE_ROJO_74_74_SOURCE_EXACT_SINGLE_GAME_PASS")


def main() -> None:
    p=argparse.ArgumentParser()
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--rojo",type=Path,required=True)
    p.add_argument("--luau",type=Path,required=True)
    p.add_argument("--enabled",choices=["true","false"],required=True)
    args=p.parse_args()
    if args.enabled=="false":
        print("FB015_EIGHT_FEATURE_OFF_EXACT_ZERO_WRITES")
        return
    assert args.rojo.is_file() and args.luau.is_file(), "PINNED_BUILD_TOOLS_MISSING"
    assert not args.out.exists()
    args.out.mkdir(parents=True)
    work=args.out/"workspace"
    after,receipt,project=compose(args.dist,work)
    for name in sorted(after):
        with (args.out/"luau-native-compile.log").open("a",encoding="utf8") as log:
            subprocess.run([str(args.luau),str(work/"src"/name)],stdout=log,check=True)
    print("FB015_EIGHT_FEATURE_LUAU_NATIVE_74_74_PASS")
    place=args.out/"P0D_PRIVATE74_EIGHT_FEATURE_STUDIO.rbxlx"
    subprocess.run([str(args.rojo),"build",str(work/"default.project.json"),"-o",str(place)],check=True)
    verify_rbxlx(place,after)
    receipt["stages"]["native"]="PASS"
    receipt["stages"]["rojo"]="PASS"
    receipt["place_bytes"]=place.stat().st_size
    receipt["place_sha256"]=hashlib.sha256(place.read_bytes()).hexdigest()
    receipt["source_count_actual"]=len(after)
    receipt["source_lock_total"]=len(after)  # compose() already asserts both lock totals equal actual 73
    receipt["source_lock_verified"]=True
    assert receipt["source_count_actual"] == 74
    receipt["studio_visual_and_fun"]="NOT_TESTED"
    (args.out/"P0D_PRIVATE74_RECEIPT.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n","utf8")
    print("FB015_EIGHT_FEATURE_PRIVATE74_BYTES",receipt["place_bytes"],"SHA256",receipt["place_sha256"])
    # Keep source workspace out of uploaded artifact; the authored sources are
    # reproducible from pinned PR Git blobs and original canonical source build.
    shutil.rmtree(work)


if __name__=="__main__":
    main()
