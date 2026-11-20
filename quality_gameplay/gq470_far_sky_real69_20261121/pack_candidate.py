"""Source-only B220 intake packet. Never changes the canonical RC itself."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "EGGRUMBLE_FarSkyFacets.client.luau"
ROUTE = Path("selected_sources/StarterPlayer/StarterPlayerScripts/EGGRUMBLE_FarSkyFacets.luau")
BASE = "e80973c354f14a0d0088577f3cc1a875454f0f8f"

def package(destination: Path) -> dict:
    destination = destination.resolve()
    target = destination / ROUTE
    target.parent.mkdir(parents=True, exist_ok=True)
    raw = SOURCE.read_bytes()
    target.write_bytes(raw)
    report = {
        "feature_id": "GQ470_FB015_FAR_SKY_MATTE_CLOUD_BANKS_20261121",
        "stage": "A_PREP_SOURCE_ONLY",
        "canonical_branch": "rc/p0d-s1-kids-rc01",
        "parent_rc_head": BASE,
        "new_candidate_route": str(ROUTE),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "source_bytes": len(raw),
        "extra_candidate_scripts": 1,
        "official_unchanged_source_count": 69,
        "possible_selected_source_count": 70,
        "touch_part_budget": 12,
        "desktop_part_budget": 18,
        "native_luau": "NOT_TESTED",
        "rojo": "NOT_TESTED",
        "studio": "NOT_TESTED",
        "android_15min": "NOT_TESTED",
        "old_new_screenshots": "0/32",
        "art_owner": "NO_GO",
        "formal_rc_integrated": False,
        "requires": "B220 authenticated fresh-SHA CAS, candidate Native/Rojo and same-head official tests",
    }
    (destination / "ART_SOURCE_RECEIPT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(package(args.out), ensure_ascii=False, indent=2))
