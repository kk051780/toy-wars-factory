#!/usr/bin/env python3
"""Source + negative contract around the canonical server vehicle sweep."""
from pathlib import Path
import importlib.util
import tempfile
import unittest

HERE=Path(__file__).resolve().parent
SRC=(HERE/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text()
SPEC=importlib.util.spec_from_file_location(
 "lss_sweep_native",HERE/"make_pilot_sweep_native.py")
native=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(native)


class PilotSweepSourceGate(unittest.TestCase):
    def test_actual_server_owner_pilot_excluded_but_not_other_players(self):
        self.assertIn('elseif hum and driver==v.owner then',SRC)
        self.assertIn("local exclude=vehicleSweepExclusions(\n      craft,water,offshoreWater,hum.Parent)",SRC)
        self.assertIn("params.RespectCanCollide=true",SRC)
        self.assertIn("params.FilterDescendantsInstances=exclude",SRC)
        self.assertIn("allowed=Workspace:Blockcast(",SRC)
        self.assertEqual(SRC.count("local function vehicleSweepExclusions("),1)
        self.assertNotIn("params.FilterDescendantsInstances={craft,water,offshoreWater}",SRC)
        body=native.extract(SRC)
        self.assertIn("if pilotCharacter then table.insert(ignore,pilotCharacter) end",body)
        self.assertIn("local ignore={craft,water,offshoreWater}",body)

    def test_stale_unfiltered_source_is_red(self):
        mutated=SRC.replace(
            "table.insert(ignore,pilotCharacter)",
            "local dropped=pilotCharacter",1)
        with self.assertRaisesRegex(ValueError,"RED_SERVER_SEATED_PILOT_FILTER_MISSING"):
            native.extract(mutated)

    def test_native_helper_also_yields_runnable_negative_mutant(self):
        with tempfile.TemporaryDirectory() as d:
            good=Path(d)/"good.luau"
            bad=Path(d)/"bad.luau"
            native.generate(good,bad)
            self.assertIn("assert(#excluded==4",good.read_text())
            self.assertIn("table.insert(ignore,pilotCharacter)",good.read_text())
            self.assertIn("local dropped=pilotCharacter",bad.read_text())


if __name__=="__main__":
    unittest.main()
