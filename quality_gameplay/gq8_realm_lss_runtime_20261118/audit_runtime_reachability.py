#!/usr/bin/env python3
"""GQ8: byte-pinned actual Realm34 x LSS32 production reachability audit.

This deliberately does NOT enable Studio-only vehicle creation in public worlds.
It prevents a green Native/Rojo build from being misreported as reachable live gameplay.
"""
import argparse
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

REPO = "kk051780/toy-wars-factory"
SOURCES = {
    "official_lss": {
        "head": "f77b4d4393d9e9b19b65566413432a7a9f13962b",
        "path": "handoffs/EGGRUMBLE-LAND-SEA-SKY-20261117/EGGRUMBLE_LandSeaSkyTraversal.server.luau",
        "blob": "c4ca82218d985914ad98dead565f9f79f5374dcb",
    },
    "realm": {
        "head": "c51de1ed4feb7a7500ada95d21282402053ef988",
        "path": "handoffs/EGGRUMBLE-REALM-CORE-20261118/EGGRUMBLE_RealmBattleCore.server.luau",
        "blob": "1ba20f2e6b1bf6ce7bab7c4d4abbedb663f0abf1",
    },
    "lss": {
        "head": "7b900dfbf4059529cbc3b75accdb3a683c3cdb87",
        "path": "handoffs/EGGRUMBLE-LAND-SEA-SKY-20261117/EGGRUMBLE_LandSeaSkyTraversal.server.luau",
        "blob": "f9ea61cc1ed4a4ec5edbc7078a619790b3181f61",
    },
}
KINDS = {
    "ship_cannon": ("_SEA_BOAT_", "SEA_BOAT"),
    "sea_beast_breath": ("_SEA_BEAST_", "SEA_BEAST"),
    "sky_beast_breath": ("_SKY_BEAST_", "SKY_BEAST"),
    "airship_gun": ("_AIRSHIP_", "AIRSHIP"),
}
STUDIO_GUARD = re.compile(
    r"(?m)^\s*if not RunService:IsStudio\(\) then return end\s*$"
)


def git_blob_sha(raw):
    prefix = ("blob %d\0" % len(raw)).encode("ascii")
    return hashlib.sha1(prefix + raw).hexdigest()


def fetch_locked(name):
    item = SOURCES[name]
    url = "https://raw.githubusercontent.com/%s/%s/%s" % (
        REPO, item["head"], item["path"]
    )
    request = urllib.request.Request(
        url, headers={"User-Agent": "GQ8-pinned-reachability-audit"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        raw = response.read()
    got = git_blob_sha(raw)
    if got != item["blob"]:
        raise ValueError(
            "%s SOURCE_LOCK_RED blob expected=%s actual=%s"
            % (name, item["blob"], got)
        )
    return raw.decode("utf-8")


def analyze(realm, lss):
    # Validate the actual producers and consumer -- not keyword-only claims.
    anchors = {
        "realm_live_boot": 'local function install(world)' in realm
        and 'local lobby=Workspace:WaitForChild(LOBBY_NAME,20)' in realm,
        "realm_fighter_factory": 'm.Name="GQ8_Fighter_"' in realm
        and 'm:SetAttribute("RealmKind","FIGHTER")' in realm,
        "realm_dive_factory": '"PublicDiveStation"' in realm
        and 'state.divers[p]=true' in realm,
        "realm_lss_dependency": 'local lss=world:FindFirstChild(LSS_NAME)' in realm
        and 'model:IsDescendantOf(lss)' in realm,
        "lss_factory": 'local function makeRide(player,role,kind,at)' in lss
        and 'craft.Name=role.."_"..kind.."_"..tostring(player.UserId)' in lss,
        "realm_no_studio_guard": not STUDIO_GUARD.search(realm[:1500]),
        "lss_studio_guard": bool(STUDIO_GUARD.search(lss[:1500])),
    }
    for feature, (realm_token, lss_token) in KINDS.items():
        anchors[feature] = realm_token in realm and (
            '"%s"' % lss_token
        ) in lss
    missing = sorted(k for k, valid in anchors.items() if not valid)
    # A missing declared anchor may be a refactor. Fail closed: never infer GO.
    studio_only = bool(STUDIO_GUARD.search(lss[:1500]))
    source_confident = not missing
    on_live = {
        "fighter_gun_bomb": source_confident and anchors["realm_fighter_factory"]
        and anchors["realm_live_boot"] and anchors["realm_no_studio_guard"],
        "subsea_hydro": source_confident and anchors["realm_dive_factory"]
        and anchors["realm_live_boot"] and anchors["realm_no_studio_guard"],
    }
    for feature in KINDS:
        on_live[feature] = bool(
            source_confident and anchors["realm_lss_dependency"]
            and anchors[feature] and not studio_only
        )
    status = (
        "SOURCE_DRIFT_RED" if missing else
        "LIVE_VEHICLE_REACHABILITY_BLOCKED" if not all(on_live.values()) else
        "STATIC_PATHS_PRESENT_ENGINE_UNVERIFIED"
    )
    return {
        "feature_id": "GQ8_REALM_LSS_RUNTIME_REACHABILITY_20261118",
        "source_sha": {k: v["head"] for k, v in SOURCES.items()},
        "source_blob": {k: v["blob"] for k, v in SOURCES.items()},
        "status": status,
        "source_anchor_errors": missing,
        "live_non_studio_static_paths": on_live,
        "studio_only_vehicle_factory": studio_only,
        "public_studio_engine_tested": False,
        "android_15m_tested": False,
        "art_fun_owner_accepted": False,
        "rc_sole_writer_adopted": False,
        "recovery": "Keep LSS32 optional/OFF, do not advertise live ships/beast mounts. "
        "Future authenticated B writer must select an independently tested "
        "non-Studio vehicle producer with ownership/cleanup/same-session guards, "
        "then re-audit latest exact SHA and run Native/Rojo/OFF31/Studio/Android.",
    }


def self_test():
    # Synthetic negative checks exercise the actual analyzer, not gameplay.
    realm = (
        'local function install(world)\n'
        'local lobby=Workspace:WaitForChild(LOBBY_NAME,20)\n'
        'm.Name="GQ8_Fighter_"\n'
        'm:SetAttribute("RealmKind","FIGHTER")\n'
        '"PublicDiveStation"\nstate.divers[p]=true\n'
        'local lss=world:FindFirstChild(LSS_NAME)\n'
        'model:IsDescendantOf(lss)\n'
        + "\n".join(k[0] for k in KINDS.values())
    )
    lss = (
        'local RunService = game:GetService("RunService")\n'
        'if not RunService:IsStudio() then return end\n'
        'local function makeRide(player,role,kind,at)\n'
        'craft.Name=role.."_"..kind.."_"..tostring(player.UserId)\n'
        + "\n".join('"%s"' % k[1] for k in KINDS.values())
    )
    blocked = analyze(realm, lss)
    assert blocked["status"] == "LIVE_VEHICLE_REACHABILITY_BLOCKED", blocked
    assert all(not blocked["live_non_studio_static_paths"][k] for k in KINDS)
    assert blocked["live_non_studio_static_paths"]["fighter_gun_bomb"]
    assert blocked["live_non_studio_static_paths"]["subsea_hydro"]
    # Removing the Studio fence should flip exactly the 4 LSS-mediated paths.
    unfenced = analyze(realm, lss.replace(
        "if not RunService:IsStudio() then return end", "-- candidate runtime"
    ))
    assert unfenced["status"] == "SOURCE_DRIFT_RED", unfenced
    assert "lss_studio_guard" in unfenced["source_anchor_errors"]
    # Mutating an actual integration dependency must fail closed.
    broken = analyze(realm.replace("model:IsDescendantOf(lss)", "false"), lss)
    assert broken["status"] == "SOURCE_DRIFT_RED", broken
    assert "realm_lss_dependency" in broken["source_anchor_errors"]
    # Fake fighter announcement must never pass for a removed producer.
    broken_fighter = analyze(realm.replace('m.Name="GQ8_Fighter_"', '-- gone'), lss)
    assert "realm_fighter_factory" in broken_fighter["source_anchor_errors"]
    print("GQ8_RUNTIME_REACHABILITY_SELFTEST_PASS: 4 modes + 3 negative mutations")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--online", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    if args.self_test:
        self_test()
    if args.online:
        realm = fetch_locked("realm")
        candidate = fetch_locked("lss")
        official = fetch_locked("official_lss")
        result = analyze(realm, candidate)
        official_analysis = analyze(realm, official)
        # Core36 selects this original raw LSS as an INPUT, not as final emitted
        # source: compose_core34.py promotes the raw Studio guard in the OUTPUT.
        # The companion COMPOSED_REPORT tests the real composer independently.
        # It is still correct that #772's 25-second idle lease is NOT selected.
        if official_analysis["status"] != "LIVE_VEHICLE_REACHABILITY_BLOCKED":
            raise ValueError("OFFICIAL_CORE36_LSS_REACHABILITY_UNEXPECTED_DRIFT_RED")
        result["official_core36_raw_lss_input"] = {
            "official_rc_head": SOURCES["official_lss"]["head"],
            "selected_lss_blob": SOURCES["official_lss"]["blob"],
            "uses_candidate_772_blob": official == candidate,
            "raw_input_studio_guard": official_analysis["studio_only_vehicle_factory"],
            "selected_25s_idle_lease": "EMPTY_CRAFT_GRACE_SECONDS" in official,
            "candidate_772_25s_idle_lease": "EMPTY_CRAFT_GRACE_SECONDS" in candidate,
            "raw_input_paths_without_composition": official_analysis["live_non_studio_static_paths"],
            "caution": "RAW input is not Core36 emitted runtime. See COMPOSED_REPORT.json; #772 idle lease not adopted.",
        }
        result["scope"] = "RAW_OPTIONAL32_AND_RAW_CORE36_INPUT_ONLY_NOT_EMITTED_SOURCE"
        encoded = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True)
        if args.out:
            p = Path(args.out)
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(encoded + "\n", encoding="utf-8")
        print(encoded)
        # Known unsafe live reachability is documented YELLOW/BLOCKED FOR FEATURE,
        # not a deceptive "gameplay PASS" or a global CI crash.
        if result["source_anchor_errors"]:
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
