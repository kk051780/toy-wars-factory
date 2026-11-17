#!/usr/bin/env python3
"""LSS active-parts cap must count live Roblox Instance parts, not lifetime sum."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parent
SRC=(ROOT/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("live_parts",ROOT/"make_live_budget_native.py")
native=importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class LivePartLifecycle(unittest.TestCase):
    def test_budget_counts_actual_live_objects_not_ever_created(self):
        self.assertEqual(SRC.count("local liveParts=0"),1)
        self.assertNotIn("local totalParts=0",SRC)
        self.assertIn("assert(liveParts<MAX_PARTS_PER_WORLD",SRC)
        self.assertIn("part.Destroying:Connect(function()",SRC)
        self.assertIn("liveParts=math.max(0,liveParts-1)",SRC)
        self.assertIn("local craftPartCost=if flying then 6 else 4",SRC)
        self.assertIn("if liveParts+craftPartCost>MAX_PARTS_PER_WORLD then return end",SRC)
        self.assertIn("if not canReserveTrapSlot(owner.UserId) or liveParts>=MAX_PARTS_PER_WORLD then return end",SRC)
        self.assertIn("t.Destroying:Connect(function() traps[t]=nil end)",SRC)
        self.assertNotIn("assert(totalParts<=",SRC)

    def test_native_harness_extracts_actual_source_and_mutant(self):
        with tempfile.TemporaryDirectory() as tmp:
            on=Path(tmp)/"current.luau"
            mutant=Path(tmp)/"mutant.luau"
            native.write(on,mutant)
            s=on.read_text()
            t=mutant.read_text()
            self.assertIn("LSS_ACTUAL_LIVE_PART_BUDGET_NATIVE_120_RECYCLES_PASS",s)
            self.assertIn("liveParts=math.max(0,liveParts-1)",s)
            self.assertIn("liveParts=liveParts",t)
            self.assertNotIn("liveParts=math.max(0,liveParts-1)",t)


if __name__=="__main__":
    unittest.main()
