#!/usr/bin/env python3
"""Measure the actual built Roblox Place (NOT its compressed artifact ZIP).

Source-exact, script count, and SHA are verified against the current build's
receipt. This is private build/QA only; it does not upload or publish anything.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

KNOWN_OFFICIAL57 = {
    "sha": "15521b7dadbd96c0ef1ed12367b5fcf2f3738c4428ebf2fb8c43532b39b8b1a8",
    "bytes": 507197,
    "head": "34d6d384d04ba1d4a394331a3e5c74f798e57a22",
    "source_count": 57,
}

def inspect(out_dir: Path) -> dict:
    found = list(out_dir.glob("*.rbxlx"))
    assert len(found) == 1, ("REQUIRE_ONE_ROBLOX_PLACE", [p.name for p in found])
    place = found[0]
    raw = place.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    receipt_path = out_dir / "RC_BUILD_RECEIPT.json"
    assert receipt_path.is_file(), "BUILD_RECEIPT_REQUIRED"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt.get("place_sha256") == sha, "PLACE_SHA_MISMATCH"
    assert receipt.get("exact_rojo_binary") is True, "SOURCE_EXACT_NOT_VERIFIED"
    count = 0
    names = []
    for elem in ET.fromstring(raw).iter("Item"):
        cls = elem.attrib.get("class")
        if cls not in {"Script", "LocalScript", "ModuleScript"}:
            continue
        if elem.find("./Properties/string[@name='Source']") is None:
            continue
        count += 1
        node = elem.find("./Properties/string[@name='Name']")
        names.append((cls, node.text if node is not None else None))
    assert count == receipt["source_count"], ("SOURCE_COUNT_DRIFT",count,receipt["source_count"])
    assert sum(cls == "Script" and name == "Game" for cls,name in names) == 1, "DUPLICATE_OR_MISSING_GAME"
    b = len(raw)
    delta = b-KNOWN_OFFICIAL57["bytes"]
    percentage = 100*delta/KNOWN_OFFICIAL57["bytes"]
    return {
        "schema": "P0D_RC_CAPACITY_V1",
        "status": "MEASURED_FROM_GENUINE_ROJO_PLACE_SOURCE_EXACT",
        "artifact_scope": ("Official RC source build" if receipt.get("canonical_rc_source_adopted") is True else ("Private candidate" if int(count)>57 else "Exact RC57 baseline or rebuilt source")),
        "place_file_name": place.name,
        "rbxlx_bytes": b,
        "rbxlx_kb_decimal": round(b/1000, 3),
        "rbxlx_mib": round(b/1048576, 4),
        "sha256": sha,
        "native_source_count": count,
        "git_head": receipt.get("rc_branch_commit"),
        "reference_official_rc57": KNOWN_OFFICIAL57,
        "delta_from_rc57_bytes": delta,
        "delta_from_rc57_pct": round(percentage, 3),
        "uncompressed": True,
        "zip_bytes": None,
        "zip_note": "GitHub artifact ZIP bytes are measured after upload via Actions metadata",
        "caveats": ["Not engine memory", "Not mobile download size", "Not Roblox runtime network usage"],
        "rc_adopted_by_this_report": False,
        "official_rc_source_adopted_in_build_receipt": receipt.get("canonical_rc_source_adopted") is True,
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    report = inspect(args.out_dir)
    out = args.out_dir
    (out/"RC_CAPACITY_REPORT.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    (out/"RC_CAPACITY_REPORT.md").write_text(
        "# RC容量実測（.rbxlx本体・ZIPではない）\n\n"
        +f"- 実測ゲーム本体: **{report['rbxlx_bytes']:,} bytes / {report['rbxlx_kb_decimal']:.3f} KB**\n"
        +f"- Script数: **{report['native_source_count']}**\n"
        +f"- source-exact SHA256: \`{report['sha256']}\`\n"
        +f"- 公式RC57本体との差: {report['delta_from_rc57_bytes']:+,} bytes"
        +f" ({report['delta_from_rc57_pct']:+.3f}%)\n"
        +"- GitHubの配布ZIP容量はActions成果物APIで別途確認\n"
        +"- Studio実メモリ・ネットワーク・Android必要容量を表すものではない\n",
        encoding="utf-8")
    print("P0D_RC_CAPACITY_VERIFIED",report["native_source_count"],
          report["rbxlx_bytes"],report["sha256"],
          "DELTA_FROM_OFFICIAL57",report["delta_from_rc57_bytes"])

if __name__ == "__main__":
    main()
