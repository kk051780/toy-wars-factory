#!/usr/bin/env python3
"""Executable negative/positive tests for the read-only ART gate."""
from __future__ import annotations
import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
import check_art_quality as art

def studio_place(path: Path, missing: str = "", duplicate_game: bool = False,
                 activated: bool = True) -> None:
    root = ET.Element("roblox")
    names = {"Game": "Script", "TrapRaidersHUD": "LocalScript",
             "BattleHUDGovernor": "LocalScript"}
    for required in art.CATEGORIES.values():
        for name in required:
            names.setdefault(name, "ModuleScript")
    if missing:
        names.pop(missing)
    for name, kind in names.items():
        item = ET.SubElement(root, "Item", {"class": kind})
        props = ET.SubElement(item, "Properties")
        ET.SubElement(props, "string", {"name": "Name"}).text = name
        ET.SubElement(props, "string", {"name": "Source"}).text = (
            "attack.Activated:Connect" if name == "TrapRaidersHUD" and activated
            else "-- stub source for " + name)
    if duplicate_game:
        item = ET.SubElement(root, "Item", {"class": "Script"})
        p = ET.SubElement(item, "Properties")
        ET.SubElement(p, "string", {"name": "Name"}).text = "Game"
        ET.SubElement(p, "string", {"name": "Source"}).text = "-- duplicate"
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

class TestArtGate(unittest.TestCase):
    def test_real_xml_inventory_all_ten_categories(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path)
            result = art.scene_inventory(path)
            self.assertEqual(result["source_gate"], "PASS")
            self.assertEqual(set(result["source_coverage"]), set(art.CATEGORIES))
            self.assertTrue(all(v["present_count"] == len(v["required"]) for v in
                                result["source_coverage"].values()))
            self.assertGreater(result["script_count"], 10)

    def test_duplicate_game_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path, duplicate_game=True)
            result = art.scene_inventory(path)
            self.assertEqual(result["source_gate"], "FAIL")
            self.assertIn("AUTHORITY_OR_HUD_COUNT:Game", result["source_violations"])

    def test_missing_art_category_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path, missing="H1SeaGroundRepair")
            result = art.scene_inventory(path)
            self.assertEqual(result["source_gate"], "FAIL")
            self.assertTrue(any("ART_SOURCE_COVERAGE:sea" in t for t in
                                result["source_violations"]))

    def test_non_activated_attack_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path, activated=False)
            self.assertIn("ATTACK_INPUT_NOT_ACTIVATED",
                          art.scene_inventory(path)["source_violations"])

    def test_missing_evidence_is_art_no_go_even_when_source_green(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "place.rbxlx"
            studio_place(path)
            result = art.audit(path)
            self.assertEqual(result["gate_level"], "SOURCE_READY_EVIDENCE_MISSING")
            self.assertEqual(result["art_decision"], "ART_NO_GO")
            self.assertFalse(result["owner_accepted"])
            self.assertEqual(result["evidence"]["shots_required"], 32)

    def test_strict_rejects_missing_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            place = root / "place.rbxlx"
            report = root / "report.json"
            studio_place(place)
            self.assertEqual(art.main(["--place", str(place), "--out", str(report)]), 0)
            self.assertEqual(art.main(["--place", str(place), "--out", str(report),
                                       "--strict"]), 2)
            self.assertEqual(json.loads(report.read_text())["art_decision"], "ART_NO_GO")

    def test_manifest_spoofed_place_sha_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            place = root / "place.rbxlx"
            studio_place(place)
            evidence = root / "evidence.json"
            evidence.write_text(json.dumps({"schema": "P0D_ART_STUDIO_EVIDENCE_V1",
                "after_place_sha256": "0"*64, "shots": [],
                "before_head": "a"*40, "after_head": "b"*40,
                "ratings": {}, "performance": {},
                "critical_visual_blockers": [], "human_reviewer": "tester"}))
            result = art.audit(place, evidence)
            self.assertEqual(result["evidence"]["gate"], "FAIL")
            self.assertIn("STUDIO_PLACE_SHA_MISMATCH",
                          result["evidence"]["violations"])
            self.assertEqual(result["art_decision"], "ART_NO_GO")

    def test_artifact_without_place_denied(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.assertEqual(art.main(["--place", str(root/"notfound.rbxlx"),
                                       "--out", str(root/"report.json")]), 2)
            self.assertEqual(json.loads((root/"report.json").read_text())["art_decision"], "ART_NO_GO")

if __name__ == "__main__":
    unittest.main()
