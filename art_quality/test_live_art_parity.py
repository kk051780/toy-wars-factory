#!/usr/bin/env python3
"""#431 negative and classifier tests; NEVER simulate runtime ART_GO."""
from __future__ import annotations
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from check_live_art_parity import ART_INSTANCES, classify, inspect

GUARD = 'local RunService = game:GetService("RunService")\nif not RunService:IsStudio() then return end\nprint("art")'
def create_place(path: Path, missing: str | None = None):
    root = ET.Element("roblox")
    entries = [(name, kind, GUARD) for name, (kind, _) in ART_INSTANCES.items() if name != missing]
    entries += [("Game", "Script", "-- original one Game"), ("TrapRaidersHUD", "LocalScript", "-- original one HUD")]
    entries += [(f"Other_{i}", "Script", "-- original") for i in range(80 - len(entries))]
    for name, kind, source in entries:
        item = ET.SubElement(root, "Item", {"class": kind})
        props = ET.SubElement(item, "Properties")
        ET.SubElement(props, "string", {"name": "Name"}).text = name
        ET.SubElement(props, "string", {"name": "Source"}).text = source
    path.write_bytes(ET.tostring(root))

class LiveArtParityTests(unittest.TestCase):
    def test_actual_early_return_is_studio_only(self):
        self.assertEqual(classify(GUARD), "TOP_STUDIO_ONLY")
    def test_comment_cannot_fool_guard(self):
        s = "-- if not RunService:IsStudio() then return end\nprint('actual')"
        self.assertNotEqual(classify(s), "TOP_STUDIO_ONLY")
    def test_nested_guard_not_top_level_class(self):
        s = "local function f()\n if not RunService:IsStudio() then return end\nend"
        self.assertNotEqual(classify(s), "TOP_STUDIO_ONLY")
    def test_real_source_contract_even_with_all_guards(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t)/"test.rbxlx"
            create_place(path)
            report = inspect(path)
            self.assertEqual(report["script_count"], 80)
            self.assertEqual(report["source_gate"], "PASS")
            self.assertEqual(report["top_studio_only_count"], 7)
            self.assertEqual(report["live_art_decision"], "LIVE_ART_NO_GO")
            self.assertFalse(report["owner_accepted"])
    def test_missing_visual_script_never_passes_source_gate(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t)/"test.rbxlx"
            create_place(path, missing="H1SeaGroundRepair")
            report = inspect(path)
            self.assertEqual(report["source_gate"], "FAIL")
            self.assertEqual(report["live_art_decision"], "LIVE_ART_NO_GO")
    def test_unsafe_xml_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            path = Path(t)/"test.rbxlx"
            path.write_bytes(b'<!DOCTYPE foo><roblox />')
            with self.assertRaises(ValueError):
                inspect(path)

if __name__ == "__main__":
    unittest.main()
