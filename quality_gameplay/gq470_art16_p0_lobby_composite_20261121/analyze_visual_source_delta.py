#!/usr/bin/env python3
"""ART420 source-budget delta for the actual 17 selected Real69 Luaus.

Counts lexical *call-site differences*, never instantiated Part count, GPU load,
FPS, image quality, or fun. Keeps human ART / Android / Studio gate NO_GO.
"""
from __future__ import annotations

import argparse
from collections import Counter
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import re

from compose_art16_p0 import (
    OFF, NOTE, RECEIPT, sha, snapshot, verify, need, HOST
)

CREATES = re.compile(r'Instance\s*\.\s*new\s*\(\s*["\x27]([A-Za-z0-9_]+)["\x27]')
SUSPECT = {
    "remote_creation": re.compile(r'Instance\s*\.\s*new\s*\(\s*["\x27]Remote(Event|Function)["\x27]'),
    "datastore": re.compile(r'DataStoreService|GetDataStore|(?:Get|Set|Update|Remove)Async\s*\('),
    "paid_feature": re.compile(r'MarketplaceService|Prompt(GamePass|Product)Purchase|ProcessReceipt'),
    "server_event_binding": re.compile(r'\.OnServerEvent\s*:\s*Connect\s*\('),
    "http_post": re.compile(r'HttpService\s*:\s*(PostAsync|RequestAsync)'),
}
VISUAL_TOKENS = {
    "neon_material": re.compile(r'Enum\s*\.\s*Material\s*\.\s*Neon'),
    "neon_string": re.compile(r'["\x27]Neon["\x27]'),
    "heartbeat_handler": re.compile(r'(Heartbeat|RenderStepped|Stepped)\s*:\s*Connect\s*\('),
    "endless_loop": re.compile(r'while\s+true\s+do'),
    "collision_enabled": re.compile(r'CanCollide\s*=\s*true'),
    "shadow_enabled": re.compile(r'CastShadow\s*=\s*true'),
    "high_emitter_rate": re.compile(r'\.Rate\s*=\s*(\d{3,})'),
}
SKIN_PARTS = {
    "Part", "WedgePart", "CornerWedgePart", "MeshPart", "UnionOperation",
    "TrussPart", "SpecialMesh", "ParticleEmitter", "Trail", "Beam", "PointLight",
    "SurfaceLight", "SpotLight", "Highlight", "BillboardGui", "SurfaceGui",
    "UIGradient", "UICorner", "TextLabel", "Frame",
}


def lexical_delta(old: str, new: str) -> dict:
    a = old.splitlines(keepends=True)
    b = new.splitlines(keepends=True)
    sm = SequenceMatcher(a=a, b=b, autojunk=False)
    added: list[str] = []
    removed: list[str] = []
    for operation, i1, i2, j1, j2 in sm.get_opcodes():
        if operation in ("insert", "replace"):
            added.extend(b[j1:j2])
        if operation in ("delete", "replace"):
            removed.extend(a[i1:i2])
    newlines = "".join(added)
    oldlines = "".join(removed)
    all_new = Counter(CREATES.findall(new))
    all_old = Counter(CREATES.findall(old))
    classes = sorted((all_new | all_old).keys())
    all_created = {key: {
        "old_call_sites": all_old[key], "new_call_sites": all_new[key],
        "net_new_call_sites": all_new[key] - all_old[key],
    } for key in classes}
    added_creation = Counter(CREATES.findall(newlines))
    removed_creation = Counter(CREATES.findall(oldlines))
    risk = {name: {"added_line_matches": len(rx.findall(newlines)),
                   "removed_line_matches": len(rx.findall(oldlines))}
            for name, rx in SUSPECT.items()}
    visuals = {name: {"old_full_source": len(rx.findall(old)),
                      "new_full_source": len(rx.findall(new)),
                      "new_added_lines": len(rx.findall(newlines))}
               for name, rx in VISUAL_TOKENS.items()}
    return {
        "added_line_count": len(added),
        "removed_line_count": len(removed),
        "old_bytes": len(old.encode("utf-8")),
        "new_bytes": len(new.encode("utf-8")),
        "old_sha256": sha(old.encode("utf-8")),
        "new_sha256": sha(new.encode("utf-8")),
        "creation_callsites_by_class": all_created,
        "creation_callsites_added_line_only": dict(sorted(added_creation.items())),
        "creation_callsites_removed_line_only": dict(sorted(removed_creation.items())),
        "authority_risk_lexical_scan": risk,
        "visual_static_heuristics": visuals,
    }


def report(root: Path) -> dict:
    root = root.resolve()
    verify(root)
    old, old_classes = snapshot(root / OFF)
    new, new_classes = snapshot(root)
    receipt = json.loads((root / RECEIPT).read_text())
    author = receipt[NOTE]["authors"]
    chosen = set(author["art16_970"]) | set(author["early_lobby_980"])
    need(len(chosen) == 17 and set(old) == set(new) and old_classes == new_classes,
         "ART_BUDGET_ROUTE_CLASS_CLAIM")
    rows = []
    totals_old = Counter()
    totals_new = Counter()
    totals_added = Counter()
    totals_removed = Counter()
    hazards = []
    for route in sorted(chosen):
        d = lexical_delta(old[route].decode("utf-8"), new[route].decode("utf-8"))
        need(old[route] != new[route] and
             d["old_sha256"] == sha(old[route]) and
             d["new_sha256"] == receipt["source_hashes"][route],
             "ART_BUDGET_NONEMPTY_SOURCE_LOCK_DELTA")
        for cls, counts in d["creation_callsites_by_class"].items():
            totals_old[cls] += counts["old_call_sites"]
            totals_new[cls] += counts["new_call_sites"]
        totals_added.update(d["creation_callsites_added_line_only"])
        totals_removed.update(d["creation_callsites_removed_line_only"])
        new_risks = {name: counts["added_line_matches"] for name, counts
                     in d["authority_risk_lexical_scan"].items()
                     if counts["added_line_matches"]}
        if new_risks:
            hazards.append({"route": route, "lexical_candidates_only": new_risks})
        rows.append({"route": route, "original_class": old_classes[route],
                     "author_pr": 980 if route == HOST else 970, **d})
    return {
        "schema": "GQ470_ART16_P0_ACTUAL_VISUAL_SOURCE_BUDGET_V1",
        "source_count": 69, "actual_changed_selected_routes": 17,
        "unchanged_original_routes": 52,
        "new_runtime_script_count": 0,
        "changed_routes": rows,
        "call_sites_original": dict(sorted(totals_old.items())),
        "call_sites_candidate": dict(sorted(totals_new.items())),
        "call_sites_added_lines_only": dict(sorted(totals_added.items())),
        "call_sites_removed_lines_only": dict(sorted(totals_removed.items())),
        "authority_suspicious_added_line_patterns": hazards,
        "studio_measured_part_count": None,
        "android_measured_fps": None, "android_15min": "NOT_TESTED",
        "old_new_screen_shots": "0/32", "source_art_not_visual_grade": True,
        "human_pc_art_score": None, "human_android_art_score": None,
        "visual_art_gate": "ART_NO_GO", "kid_fun": "NOT_TESTED",
        "owner_accepted": False,
        "limitations": [
            "A loop may create many instances from a single Instance.new call site",
            "Lexical scanning does not prove runtime code execution or that a pattern is dangerous",
            "Native/Rojo source success is not Studio or Android FPS/visual/art success",
            "No gameplay authority or P0 player-visible correctness is proved by this report"
        ]
    }


def self_test() -> None:
    cases = [
        ("local x=Instance.new('Part')", "local x=Instance.new('WedgePart')", 1, -1),
        ("local x=1", "local x=1\nlocal p=Instance.new('ParticleEmitter')", 1, 0),
        ("local n=Enum.Material.Neon", "local n=Enum.Material.SmoothPlastic", 0, 0),
        ("local x=1", "local x=1\nlocal ev=Instance.new('RemoteEvent')", 1, 0),
        ("local x=1", "local x=1\nlocal ds=game:GetService('DataStoreService')", 0, 0),
        ("local x=1", "local x=1\nlocal m=game:GetService('MarketplaceService')", 0, 0),
    ]
    for old, new, added, removed_part in cases:
        d = lexical_delta(old, new)
        assert sum(d["creation_callsites_added_line_only"].values()) == added
        if removed_part != 0:
            assert d["creation_callsites_by_class"]["Part"]["net_new_call_sites"] == removed_part
        if "RemoteEvent" in new:
            assert d["authority_risk_lexical_scan"]["remote_creation"]["added_line_matches"] == 1
        if "DataStoreService" in new:
            assert d["authority_risk_lexical_scan"]["datastore"]["added_line_matches"] == 1
        if "MarketplaceService" in new:
            assert d["authority_risk_lexical_scan"]["paid_feature"]["added_line_matches"] == 1
        if "Neon" in old:
            assert d["visual_static_heuristics"]["neon_material"]["old_full_source"] == 1
            assert d["visual_static_heuristics"]["neon_material"]["new_full_source"] == 0
    print("GQ470_ART16_P0_VISUAL_SOURCE_BUDGET_6_STATIC_TESTS_PASS")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--root", type=Path)
    p.add_argument("--report", type=Path)
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()
    if args.self_test:
        self_test()
    else:
        need(args.root is not None and args.report is not None, "ART_BUDGET_NEEDS_INPUT")
        data = report(args.root)
        args.report.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)+"\n")
        print("GQ470_ART16_P0_ART420_SOURCE_BUDGET_REPORT_REAL17",
              len(data["changed_routes"]),
              len(data["authority_suspicious_added_line_patterns"]),
              "ART_NO_GO")
