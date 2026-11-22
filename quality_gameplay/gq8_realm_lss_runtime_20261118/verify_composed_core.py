#!/usr/bin/env python3
"""Test the ACTUAL Core34 composer, not just its Studio-only input LSS file.

This is a source-path acceptance probe, NOT a Roblox runtime/Android/FUN proof.
Only a synthetic 31-source fixture is assembled here; canonical Core36 CI is
separately responsible for the real same-HEAD Native/Rojo/Source/Class build.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path

EXPECTED_COMPOSER_BLOB = "4aa360c084c58aede0853323ea96f33ea7be6667"
EXPECTED_LSS_BLOB = "c4ca82218d985914ad98dead565f9f79f5374dcb"
GUARD = "if not RunService:IsStudio() then return end"
VEHICLES = {
    "SEA_BOAT": 'makeRide(p,"BUILDER","SEA_BOAT"',
    "SEA_BEAST": 'makeRide(p,"BEAST","SEA_BEAST"',
    "AIRSHIP": 'makeRide(p,"BUILDER","AIRSHIP"',
    "SKY_BEAST": 'makeRide(p,"BEAST","SKY_BEAST"',
}


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def require(condition: bool, reason: str):
    if not condition:
        raise ValueError("RED_COMPOSED_REALM_REACHABILITY_" + reason)


def factory_paths(body: str) -> dict[str, bool]:
    # Exact producer call sites are required; kind names in comments are insufficient.
    return {name: marker in body for name, marker in VEHICLES.items()}


def load_composer(path: Path):
    spec = importlib.util.spec_from_file_location("p0d_real_core34_composer", path)
    require(spec is not None and spec.loader is not None, "COMPOSER_IMPORT")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def synthetic31(directory: Path) -> Path:
    # Minimal Rojo layout allows execution of the REAL composer with zero
    # extra game authority and no reliance on static prose or regex alone.
    server = {}
    for n in range(31):
        name = ("EGGRUMBLE_LobbyCastleModesPreview" if n == 0 else
                "EGGRUMBLE_SwarmCombat" if n == 1 else
                f"EGGRUMBLE_TestSource{n:02d}")
        file = directory / f"{name}.server.luau"
        file.write_text("-- baseline byte-exact fixture\n", encoding="utf-8")
        server[name] = {"$path": file.name}
    project = directory / "fixture31.project.json"
    project.write_text(json.dumps({
        "name": "GQ8_TEST_ONLY_NOT_REAL_GAME",
        "tree": {"ServerScriptService": server},
    }), encoding="utf-8")
    return project


def check(composer: Path, lss: Path, out: Path):
    require(git_blob(composer.read_bytes()) == EXPECTED_COMPOSER_BLOB, "COMPOSER_SOURCE_LOCK")
    require(git_blob(lss.read_bytes()) == EXPECTED_LSS_BLOB, "LSS_SOURCE_LOCK")
    original = lss.read_text(encoding="utf-8")
    require(original.count(GUARD) == 1, "ORIGINAL_GUARD")
    require(all(factory_paths(original).values()), "ORIGINAL_PRODUCERS")

    real_composer = load_composer(composer)
    with tempfile.TemporaryDirectory(prefix="gq8_core34_composer_") as tmp:
        root = Path(tmp)
        baseline = synthetic31(root)
        combined = root / "on" / "core34.project.json"
        rollback = root / "off" / "original31.project.json"
        real_composer.compose(baseline, combined, lss_source=lss)
        _, selected = real_composer.get_files(combined)
        require(len(selected) == 34, "ON_SCRIPT_COUNT")
        key = ("ServerScriptService", "EGGRUMBLE_LandSeaSkyTraversal")
        require(key in selected, "ON_LSS_ROUTE")
        promoted = selected[key].read_text(encoding="utf-8")
        require(GUARD not in promoted, "GENERATED_STUDIO_GUARD")
        require(all(factory_paths(promoted).values()), "GENERATED_FOUR_FACTORIES")
        require(promoted.count("Promoted REALM34 core") == 1, "PROMOTION_MARKER")
        # No stealth source rewrite other than this ONE explicit guard replacement.
        require(promoted == original.replace(
            GUARD, "-- Promoted REALM34 core: same V3 session guards on all servers; no Studio gate."
        ), "UNREVIEWED_LSS_MUTATION")

        real_composer.compose(baseline, rollback, off=True)
        _, restored = real_composer.get_files(rollback)
        _, initial = real_composer.get_files(baseline)
        require(len(restored) == len(initial) == 31, "OFF_SCRIPT_COUNT")
        require(all(restored[k].read_bytes() == f.read_bytes()
                    for k, f in initial.items()), "OFF31_CHANGED")

        # Required negatives: an unpromoted raw file and any lost producer
        # must NOT be classified as having all four runtime code paths.
        require(GUARD in original, "NEGATIVE_STUDIO_GUARD_NOT_DETECTED")
        for kind, marker in VEHICLES.items():
            mutant = promoted.replace(marker, "-- removed factory", 1)
            require(not factory_paths(mutant)[kind], f"NEGATIVE_{kind}_NOT_DETECTED")

    result = {
        "feature_id": "GQ8_REALM_LSS_COMPOSED_SOURCE_REACHABILITY_20261118",
        "input_lss_raw_studio_only": True,
        "core34_generated_lss_studio_guard_removed": True,
        "core34_generated_vehicle_factories": list(VEHICLES),
        "original_31_inverse": "BYTE_EXACT_FIXTURE",
        "canonical_core36_real_build": "SEPARATE_OFFICIAL_CI_REQUIRED",
        "network_live_or_roblox_studio_test": "NOT_TESTED",
        "android_15m": "NOT_TESTED",
        "public_release": False,
        "status": "COMPOSED_STATIC_PATHS_PRESENT_ENGINE_UNVERIFIED",
        "negative_mutations": 5,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("GQ8_COMPOSED_CORE_RUNTIME_SOURCE_PASS_4_FACTORIES_OFF31_5_NEGATIVES")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--composer", type=Path, required=True)
    parser.add_argument("--lss", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    check(args.composer, args.lss, args.out)
