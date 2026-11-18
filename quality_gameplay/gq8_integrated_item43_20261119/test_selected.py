from __future__ import annotations
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = Path(__file__).with_name("compose_item43.py")
spec = importlib.util.spec_from_file_location("gq8_integrator", SRC)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class LatestOwnerLineageRealSourceGate(unittest.TestCase):
    def test_exact_unchanged_42_routes_and_unique_item(self):
        baseline = ROOT / "artifacts/neutral43/REAL43.project.json"
        selected = ROOT / "artifacts/item43/ITEM43.project.json"
        _, before = mod.flatten(baseline)
        _, after = mod.flatten(selected)
        self.assertEqual(len(before), 43)
        self.assertEqual(len(after), 43)
        self.assertEqual(set(before), set(after))
        self.assertEqual([k for k in before if before[k].read_bytes() != after[k].read_bytes()], [mod.ITEM])
        self.assertEqual(before[mod.SWARM].read_bytes(), after[mod.SWARM].read_bytes())
        self.assertEqual(before[mod.NEUTRAL_POLICY].read_bytes(), after[mod.NEUTRAL_POLICY].read_bytes())

    def test_real_item_rollback_and_three_shape_kinds(self):
        before = mod.flatten(ROOT / "artifacts/neutral43/REAL43.project.json")[1][mod.ITEM].read_bytes()
        after = mod.flatten(ROOT / "artifacts/item43/ITEM43.project.json")[1][mod.ITEM].read_bytes()
        patch = mod.load_python(ROOT / "artifacts/upstream/patch_item812.py", "tested_item_patch")
        self.assertEqual(patch.inverse(after), before)
        self.assertEqual(after.count(b"GQ802_ITEM_EXISTING_3D_IDENTITY_20261118"), 1)
        for name in (b"ReliefCrossV", b"FeatherLeft", b"Crest"):
            self.assertIn(name, after)
        for anchor in patch.GAMEPLAY_ANCHORS:
            self.assertIn(anchor.encode(), before)
            self.assertIn(anchor.encode(), after)

    def test_portable_source_exact_and_no_duplicate_authority(self):
        selected = mod.flatten(ROOT / "artifacts/item43/ITEM43.project.json")[1]
        packed = mod.flatten(ROOT / "artifacts/portable43/EGGRUMBLE_SOURCE43_ITEM.project.json")[1]
        self.assertEqual(set(selected), set(packed))
        self.assertTrue(all(selected[k].read_bytes() == packed[k].read_bytes() for k in selected))
        self.assertEqual(len([k for k in packed if k[-1] == "EGGRUMBLE_SwarmCombat"]), 1)
        self.assertEqual(len([k for k in packed if k[-1] == "EGGRUMBLE_FieldItemPickups"]), 1)
        receipt = json.loads((ROOT / "artifacts/item43/INTEGRATED_ITEM43_RECEIPT.json").read_text())
        self.assertFalse(receipt["official_rc_adopted"])
        self.assertEqual(receipt["unchanged_existing"], 42)
        self.assertEqual(receipt["additional_remote_store_hp_score_authority"], 0)


if __name__ == "__main__":
    unittest.main()
