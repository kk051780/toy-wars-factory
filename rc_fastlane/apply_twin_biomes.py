#!/usr/bin/env python3
"""OFFICIAL63 -> PRIVATE64: append one new Twin Biomes + 4-species world script.

Never mutate the official RC branch: only authorized #220 writer can admit.
This composer's only destination is a temporary source-exact Rojo dist.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FEATURE = "TWIN_BIOMES_4NPC_V1"
ORIGINAL = ROOT / "features/twin_biomes/TwinBiomes.server.luau"
PIN = "ff48273db7c7f0e240e45fba8b997cad669a5143"
DEST = "server/TwinBiomes.server.luau"
FLAG = "P0D_ENABLE_TWIN_BIOMES_V1"
PARENT_COUNT = 63

def blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def sources(dist: Path) -> dict[str, bytes]:
    root = dist / "src"
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in sorted(root.rglob("*.luau"))}

def apply(dist: Path, profile: str, override: bool | None = None) -> bool:
    if profile != "rich51":
        print("P0D_TWIN_BIOMES_OTHER_PROFILE_OFF")
        return False
    flags = json.loads((ROOT / "FEATURE_SWITCHES.json").read_text("utf8"))["features"]
    enabled = flags[FEATURE]["enabled"] if override is None else override
    assert type(enabled) is bool, "ENABLED_BOOLEAN_REQUIRED"
    if not enabled:
        print("P0D_TWIN_BIOMES_OFF_ZERO_WRITES_OFFICIAL63_PASS")
        return False

    prerequisites = ("WCS_F01_C01", "SEVEN_JOBS_PVE_V1",
                     "EGG_RELAY_CLASSIC_V1", "STARRY_PATH_V1", "METEOR_FOURTH_V1", "STAR_SHARDS_V1")
    assert all(flags[k]["enabled"] for k in prerequisites), "PARENT_FEATURE_DEPENDENCY_OFF"
    before = sources(dist)
    assert len(before) == PARENT_COUNT, ("EXACT_OFFICIAL63_REQUIRED", len(before))
    for key in ("server/Game.server.luau", "server/WCS_CrystalCanyon.server.luau",
                "server/SevenJobsRules.luau", "server/EggRelayPolicy.luau",
                "server/StarfallPath.server.luau", "server/MeteorFourth.server.luau"):
        assert key in before, ("MISSING_REQUIRED_PARENT_SOURCE", key)
    assert DEST not in before, "DUPLICATE_BIOME_SOURCE"
    assert "server/StarShardHunt.server.luau" in before, "MISSING_OFFICIAL63_SHARDS"
    assert before["server/StarShardHunt.server.luau"].count(b"local TOTAL=6") == 1, "SHARDS_PARENT_DRIFT"
    assert before["server/Game.server.luau"].count(b"remote.OnServerEvent:Connect(") == 1
    assert before["server/SevenJobsRules.luau"] != b""
    assert before["server/WCS_CrystalCanyon.server.luau"].count(b'anchor.Name="P0D_CrystalCanyonAnchor"') == 1
    assert before["server/MeteorFourth.server.luau"].count(b'local QUIET_SECONDS = 55') == 1

    lockpath = dist / "SOURCE_LOCK.json"
    lock_raw = lockpath.read_bytes()
    lock = json.loads(lock_raw)
    pins = {p:blob(v) for p,v in sorted(before.items())}
    assert lock["total_scripts"] == PARENT_COUNT and lock["blobs"] == pins, "SOURCE62_LOCK_DRIFT"
    assert lock.get("rc_meteor_fourth_overlay", {}).get("id") == "METEOR_FOURTH_V1"
    assert lock.get("rc_star_shards_overlay", {}).get("id") == "STAR_SHARDS_V1"

    receiptpath = dist / "RC_FEATURE_LOCK.json"
    receipt = None
    if receiptpath.is_file():
        receipt = json.loads(receiptpath.read_text("utf8"))
        assert receipt["total_sources"] == PARENT_COUNT
        assert receipt["source_gitblobs"] == pins, "FEATURE62_LOCK_DRIFT"
        assert FEATURE not in receipt.get("feature_flags", {}), "BIOME_ALREADY_ENABLED"

    cfgpath = dist / "default.project.json"
    cfg = json.loads(cfgpath.read_text("utf8"))
    assert cfg["tree"]["ServerScriptService"]["TrapRaidersS1"]["$path"] == "src/server"
    storage = cfg["tree"]["ServerStorage"]
    attrs = storage["$attributes"]
    assert attrs["P0D_RC_ENABLE_WCS_F01_C01"] is True
    assert attrs["P0D_RC_ENABLE_STARRY_PATH_V1"] is True
    assert attrs["P0D_RC_ENABLE_STAR_SHARDS_V1"] is True
    assert storage["P0D_ENABLE_METEOR_SHORTCUT_V1"]["$properties"]["Value"] is True
    assert storage["P0D_RC_ENABLE_EGG_RELAY_CLASSIC"]["$properties"]["Value"] is True
    assert FLAG not in storage, "BOOT_FLAG_DUPLICATE"

    raw = ORIGINAL.read_bytes()
    assert blob(raw) == PIN, "ORIGINAL_SOURCE_BLOB_DRIFT"
    script = raw.decode("utf8")
    for marker in (
        "if not RunService:IsStudio() then",
        'if not value or not value:IsA("BoolValue") or value.Value ~= true then',
        'Workspace:WaitForChild("P0D_WCS_CrystalCanyon", 145)',
        'canyon:WaitForChild("AlwaysOpenSafeRoute", 12)',
        '"CoralGarden_" .. spec.side', '"ThunderLookout_" .. spec.side',
        'world:SetAttribute("Biomes", 2)',
        'world:SetAttribute("Species", 4)',
        'world:SetAttribute("CharacterInstances", 8)',
        'world:SetAttribute("PersistedCollection", false)',
        'for _, info in ipairs(species) do',
        'if (root.Position - body.Position).Magnitude > 12 then',
        'task.wait(0.25)',
        'markDiscovery(player,info)',
        'npc.PrimaryPart=body',
        'entry.model:PivotTo(entry.base*CFrame.new(0,bob,0)*CFrame.Angles(0,turn,0))',
        'player:SetAttribute("P0D_TwinCodexCount",count)',
        'npc:SetAttribute("CapturableOrOwned", false)',
        'deck:SetAttribute("AlwaysOpen", true)',
        'world:SetAttribute("BothTeamsAccess", true)',
    ):
        assert marker in script, ("SOURCE_SAFETY_ANCHOR_MISSING", marker)
    for forbidden in ("DataStoreService", "UpdateAsync(", "MarketplaceService",
                      'Instance.new("RemoteEvent")', "OnServerEvent:Connect(",
                      "FireServer(", "TakeDamage(", "PromptProductPurchase(",
                      "Humanoid.Health =", "leaderstats"):
        assert forbidden not in script, ("FORBIDDEN_GAME_AUTHORITY", forbidden)

    after = dict(before)
    after[DEST] = raw
    assert len(after) == 64
    assert all(after[k] == original for k,original in before.items()), "PARENT_CHANGED"
    locks = {p:blob(v) for p,v in sorted(after.items())}
    lock["total_scripts"] = 64
    lock["blobs"] = locks
    lock["rc_twin_biomes_overlay"] = {
        "id":FEATURE,
        "source_gitblob":PIN,
        "source_count_parent_exact":PARENT_COUNT,
        "canonical_parent_head":"389c7484354cf5f9bf8d1731c327483059d6ffbb",
        "species_unique_visual_shapes":4,
        "idle_animated_models":8,
        "session_only_species_discovery":"0/4_TO_4/4",
        "worlds":["TIDAL_CORAL_GARDEN","STORM_CLOUD_LOOKOUT"],
        "new_species":["AWARIN","SANGORU","RAIKO","KUMONON"],
        "new_features":["unique_silhouettes","model_idle","session_bestiary_4_4"],
        "characters_mirrored_each_team":8,
        "new_sole_script":DEST,
        "single_original_game_remote_store":True,
        "default_off_if_missing_runtime_flag":True,
        "runtime_scope":"STUDIO_ONLY_EXPLICIT_TRUE_BOOLVALUE",
        "rollback":"Build flag false reverts to same exact official63 source",
        "studio_engine":"NOT_TESTED",
        "official_rc_adopted":False,
    }
    storage[FLAG] = {"$className":"BoolValue","$properties":{"Value":True}}
    if receipt is not None:
        receipt["total_sources"] = 64
        receipt["source_gitblobs"] = locks
        receipt["feature_flags"][FEATURE] = True
        receipt["new_biomes_and_npcs"] = "PRIVATE_SOURCE64_NOT_CANONICAL"

    # Entire preflight above runs BEFORE any scratch-distro mutation.
    (dist/"src"/DEST).write_bytes(raw)
    cfgpath.write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    lockpath.write_text(json.dumps(lock,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    if receipt is not None:
        receiptpath.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    assert sources(dist) == after, "SOURCE_BODIES_CHANGED_AFTER_INSTALL"
    print("P0D_TWIN_BIOMES_2_FIELDS_4_SPECIES_8_NPCS_SOURCE64_PASS")
    return True

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--profile",default="rich51",choices=("rich51","rich47","legacy21"))
    p.add_argument("--dist",type=Path,required=True)
    p.add_argument("--enabled",choices=("true","false"),default="true")
    a=p.parse_args()
    apply(a.dist,a.profile,a.enabled=="true")
