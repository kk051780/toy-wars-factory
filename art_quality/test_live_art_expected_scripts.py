#!/usr/bin/env python3
"""Regression: explicit authenticated RC81 source-count audit; old RC80 still default."""
from __future__ import annotations
import tempfile,unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from check_live_art_parity import inspect
from test_live_art_parity import create_place

def add_extra(place:Path,name:str)->None:
    root=ET.fromstring(place.read_bytes())
    it=ET.SubElement(root,"Item",{"class":"Script"})
    p=ET.SubElement(it,"Properties")
    ET.SubElement(p,"string",{"name":"Name"}).text=name
    ET.SubElement(p,"string",{"name":"Source"}).text="-- additional visual-only original"
    place.write_bytes(ET.tostring(root))

class ExplicitScriptCountTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.place=Path(self.temp.name)/"p.rbxlx"
        create_place(self.place)
    def test_default_retains_strict_80(self):
        self.assertEqual(inspect(self.place)["source_gate"],"PASS")
        self.assertEqual(inspect(self.place)["expected_script_count"],80)
    def test_canonical_81_is_accepted_only_with_explicit_optin(self):
        add_extra(self.place,"P0DLiveCastleArt")
        self.assertEqual(inspect(self.place)["source_gate"],"FAIL")
        report=inspect(self.place,expected_scripts=81)
        self.assertEqual(report["source_gate"],"PASS")
        self.assertEqual(report["script_count"],81)
        self.assertEqual(report["top_studio_only_count"],7)
        self.assertEqual(report["live_art_decision"],"LIVE_ART_NO_GO")
    def test_bad_expected_count_always_fails_closed(self):
        add_extra(self.place,"P0DLiveCastleArt")
        self.assertEqual(inspect(self.place,expected_scripts=82)["source_gate"],"FAIL")
    def test_duplicate_Game_cannot_be_hidden_by_expected_81(self):
        add_extra(self.place,"Game")
        report=inspect(self.place,expected_scripts=81)
        self.assertEqual(report["source_gate"],"FAIL")
        self.assertTrue(any("GAMEPLAY_AUTHORITY_CARDINALITY" in e for e in report["source_errors"]))
    def test_expected_source_range_protected(self):
        for n in (0,79,97,1000):
            with self.assertRaises(ValueError):
                inspect(self.place,expected_scripts=n)

if __name__=="__main__":unittest.main()
