#!/usr/bin/env python3
"""Independent source-only Real59/9-domain evidence gate.

Consumes the official SAME-HEAD Real59 artifact and the actual OFF55 Place.
Does not author gameplay, assert Studio quality, or grant purchase authority.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from xml.etree import ElementTree as ET

from verify_integrated_sources import ROUTES, SINGLE
import re

def contents(root):
    """Extract original Luau and script classes directly from Rojo's actual .rbxlx XML."""
    original = {}
    classes = {}
    def recurse(item, prefix):
        props = item.find("Properties")
        name = props.findtext("string[@name='Name']") if props is not None else None
        if not name or not re.fullmatch(r"[A-Za-z0-9_]+", name):
            raise ValueError("RED_INVALID_MODEL_ROUTE")
        route = prefix + (name,)
        if route in classes:
            raise ValueError("RED_DUPLICATE_MODEL_ROUTE")
        cls = item.get("class")
        classes[route] = cls
        if cls in ("Script", "LocalScript", "ModuleScript"):
            src = props.findtext("string[@name='Source']")
            if src is None:
                src = props.findtext("ProtectedString[@name='Source']")
            if src is None:
                raise ValueError("RED_MISSING_MODEL_SOURCE")
            original[route] = (cls, src.replace("\r\n", "\n"))
        for child in item.findall("Item"):
            recurse(child, route)
    for item in root.findall("Item"):
        recurse(item, ())
    return original, classes

ADDED = {
    "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy": "ModuleScript",
    "ServerScriptService/EGGRUMBLE_MapVisibilityPolicy": "ModuleScript",
    "ServerScriptService/EGGRUMBLE_MapIntelBridge": "Script",
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime": "LocalScript",
}
LANES = {name: list(routes) for name, routes in ROUTES.items()}
LANES["field"] += [
    "ServerScriptService/EGGRUMBLE_MapVisibilityPolicy",
    "ServerScriptService/EGGRUMBLE_MapIntelBridge",
]
LANES["ui"] += [
    "ReplicatedStorage/EGGRUMBLE_HudPresentationPolicy",
    "StarterPlayer/StarterPlayerScripts/EGGRUMBLE_HudIntelRuntime",
]

def require(ok, code):
    if not ok:
        raise ValueError("RED_" + code)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def verify(place59: Path, receipt: Path, off55: Path, expected_head: str):
    on_place, _ = contents(ET.parse(place59).getroot())
    files = {'/'.join(route): (cls, source.encode('utf8')) for route, (cls, source) in on_place.items()}
    data = json.loads(receipt.read_text(encoding="utf8"))
    require(len(expected_head) == 40 and all(c in "0123456789abcdef" for c in expected_head),
            "INVALID_EXPECTED_HEAD")
    require(len(files) == 59, "COUNT_59")
    require(data.get("baseline_real55_source_count") == 55 and
            data.get("candidate_real59_source_count") == 59 and
            data.get("baseline55_exact_sources_unchanged") is True, "PARENT55_CONTRACT")
    require(data.get("official_rc_adopted") is True and
            data.get("candidate_head") == expected_head and
            data.get("official_head") == expected_head, "FALSE_FORMAL_HEAD")
    require(data.get("roblox_published") is False and
            data.get("spending_enabled") is False and
            data.get("actual_native") == "PASS" and
            data.get("actual_rojo") == "PASS" and
            data.get("off55") == "PASS", "FALSE_PRODUCT_OR_NATIVE_GO")
    require(sha(off55.read_bytes()) == data.get("off55_place_sha256"),
            "OFF55_PLACE_SHA")
    selected = data.get("on_sources")
    baseline = data.get("off_sources")
    require(isinstance(selected, list) and len(selected) == 59 and
            isinstance(baseline, list) and len(baseline) == 55, "LEDGER_COUNTS")

    def index(rows):
        output = {}
        for item in rows:
            route = item.get("route")
            require(isinstance(route, str) and route not in output, "DUPLICATE_LEDGER_ROUTE")
            output[route] = item
        return output

    on, off = index(selected), index(baseline)
    require(set(on) == set(files) and set(on) - set(off) == set(ADDED),
            "LEDGER_OR_FOUR_ROUTE_DRIFT")
    require(len(off) == 55, "BASELINE_55_MISSING")
    original, _ = contents(ET.parse(off55).getroot())
    original_routes = {"/".join(key): value for key, value in original.items()}
    require(set(original_routes) == set(off), "OFF55_REAL_SOURCE_ROUTE_DRIFT")
    source_bytes_sum = 0
    for route, (actual_class, b) in files.items():
        item = on[route]
        require(item.get("sha256") == sha(b) and item.get("bytes") == len(b),
                "ON59_SOURCE_HASH_" + route.replace("/", "_"))
        require(item.get("class") == actual_class,
                "ON59_SOURCE_CLASS_" + route.replace("/", "_"))
        source_bytes_sum += len(b)
        if route in original_routes:
            original_class, original_text = original_routes[route]
            original_bytes = original_text.encode("utf8")
            require(item == off[route] and original_class == item["class"] and
                    b == original_bytes, "OFF55_SOURCE_CHANGED_" + route.replace("/", "_"))
    for route, required_class in ADDED.items():
        require(files[route][0] == required_class,
                "FOUR_ADDITIONS_CLASS_" + route.replace("/", "_"))
    for owner_route in SINGLE:
        require(sum(route == owner_route for route in files) == 1,
                "DUPLICATE_GAME_COMBAT_SWARM_HOST")
    pillars = {}
    for name, required in LANES.items():
        require(all(route in files for route in required), "MISSING_NINE_LANE_" + name)
        pillars[name] = {
            "source_selected": True, "source_routes": required,
            "studio_2client": "NOT_TESTED", "android_15min": "NOT_TESTED",
            "art_quality": "NOT_TESTED", "fun": "NOT_TESTED"
        }
    require(len(pillars) == 9, "NINE_PILLARS_DRIFT")
    return {
        "schema": "GQ8_FORMAL_REAL59_INDEPENDENT_NINE_DOMAIN_SOURCE_EVIDENCE_V1",
        "official_head": expected_head, "source_count": 59,
        "parent_exact_source_count": 55, "new_source_count": 4,
        "source_bytes_sum_not_place_size": source_bytes_sum,
        "official_private_source_selected": True,
        "native_rojo_off55_samehead": "PASS",
        "nine_source_domains_selected": 9, "nine_studio_domains_verified": 0,
        "studio_2client": "NOT_TESTED", "android_15min": "NOT_TESTED",
        "first_three_minute_fun": "NOT_TESTED", "product_go": False,
        "publish": False, "paid_trading": False,
        "lanes": pillars,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--place59", type=Path, required=True)
    ap.add_argument("--receipt", type=Path, required=True)
    ap.add_argument("--off55", type=Path, required=True)
    ap.add_argument("--expected-head", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    result = verify(args.place59, args.receipt, args.off55, args.expected_head)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf8")
    print("GQ8_FORMAL_REAL59_NINE_DOMAIN_SOURCE_EXACT_OFF55_PASS", result["source_count"])

if __name__ == "__main__":
    main()
