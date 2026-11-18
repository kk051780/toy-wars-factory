#!/usr/bin/env python3
"""Actual #764 source identity tests plus synthetic Core36 source-set negative tests.
Native compile and full same-HEAD Core36 must be independently checked.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path
from apply import (ROUTE, SOURCE_BLOB, ORIGINAL_TRANSITION, PATCHED_TRANSITION,
                   ORIGINAL_STRIKE, PATCHED_STRIKE, blob_sha, patch_source, compose36, flatten)

SOURCE = Path(os.environ.get(
    "GQ8_REALM_ORIGIN",
    "_realm764/handoffs/EGGRUMBLE-REALM-CORE-20261118/EGGRUMBLE_RealmBattleCore.server.luau"
))

class StormPhaseFenceTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = SOURCE.read_bytes()

    def test_actual_source_pinned(self):
        self.assertEqual(blob_sha(self.original), SOURCE_BLOB)

    def test_true_storm_end_cancels_warning(self):
        result = patch_source(self.original).decode()
        self.assertEqual(result.count(PATCHED_TRANSITION), 1)
        self.assertEqual(result.count(PATCHED_STRIKE), 1)
        self.assertLess(result.index(PATCHED_TRANSITION), result.index(PATCHED_STRIKE))
        self.assertIn('if weather~="THUNDER" then\n    state.pendingLightning=nil', result)
        self.assertIn('core:SetAttribute("LightningWarning",false)', result)
        self.assertNotIn(ORIGINAL_TRANSITION, result)
        self.assertNotIn(ORIGINAL_STRIKE, result)

    def test_mutation_refused(self):
        changed = self.original.replace(b'WEATHER_PHASE_SECONDS = 35', b'WEATHER_PHASE_SECONDS = 34')
        with self.assertRaisesRegex(ValueError, "RED_REALM_AUTHOR_SOURCE_BLOB_CHANGED"):
            patch_source(changed)

    def test_anchor_mutation_refused_even_when_blob_check_off(self):
        changed = self.original.replace(ORIGINAL_STRIKE.encode(), b'  if false then\n')
        with self.assertRaisesRegex(ValueError, "RED_REALM_STORM_ANCHOR_CHANGED"):
            patch_source(changed, verify_blob=False)

    def make36(self, folder):
        paths = [
            ("ServerScriptService", "EGGRUMBLE_RealmBattleCore"),
            ("ServerScriptService", "EGGRUMBLE_SevenRoleCombat"),
            ("ServerScriptService", "EGGRUMBLE_SwarmCombat"),
            ("ServerScriptService", "EGGRUMBLE_NaturalRegen")
        ] + [("ServerScriptService", "Base%02d" % i) for i in range(32)]
        server = {}
        for i, route in enumerate(paths):
            file = folder / ("source%02d.server.luau" % i)
            file.write_bytes(self.original if route == ROUTE else b'print("safebase")\n')
            server[route[-1]] = {"$path": file.name}
        project = folder / "original36.project.json"
        project.write_text(json.dumps({"name":"original36","tree":{"ServerScriptService":server}}))
        return project

    def test_real36_output_same_35_and_reversible(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = self.make36(root)
            dest = root / "generated" / "storm36.project.json"
            compose36(original, dest)
            _, before = flatten(original)
            _, after = flatten(dest)
            self.assertEqual((len(before), len(after)), (36,36))
            for route in before:
                if route == ROUTE:
                    self.assertNotEqual(before[route].read_bytes(), after[route].read_bytes())
                else:
                    self.assertEqual(before[route].read_bytes(), after[route].read_bytes())
            self.assertEqual(json.loads(dest.with_suffix(".receipt.json").read_text())["preserved_other_sources"],35)
            with self.assertRaisesRegex(ValueError, "RED_REFUSE_OVERWRITE"):
                compose36(original, dest)

    def test_invalid_source_set_is_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = self.make36(root)
            model = json.loads(original.read_text())
            del model["tree"]["ServerScriptService"]["EGGRUMBLE_SwarmCombat"]
            original.write_text(json.dumps(model))
            with self.assertRaisesRegex(ValueError,"RED_NOT_REAL_CORE36"):
                compose36(original, root / "bad" / "storm36.project.json")

if __name__ == "__main__":
    unittest.main()
