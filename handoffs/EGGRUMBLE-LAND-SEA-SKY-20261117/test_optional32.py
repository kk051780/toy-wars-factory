#!/usr/bin/env python3
"""Regression tests for a real but optional 32nd V3 Studio traversal source."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

DIR = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("lss_compose", DIR / "compose_optional32.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SOURCE = (DIR / "EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text(encoding="utf-8")


class LandSeaSkySourceTests(unittest.TestCase):
    def test_studio_only_and_canonical_authority(self):
        self.assertIn("if not RunService:IsStudio() then return end", SOURCE)
        for forbidden in ["Instance.new(\"RemoteEvent\")", "DataStoreService",
                          "NeutralHorde=Instance", "Instance.new(\"BindableEvent\")",
                          "LastAttackerId", "TakeDamage(", "SetAttribute(\"EGGRUMBLE_Combo\""]:
            self.assertNotIn(forbidden, SOURCE)

    def test_roles_and_terrain_and_seat_controls(self):
        for value in ["BUILDER", "BEAST", "TRAPPER", "TEAM_Arena",
                      "BATTLE_ROYALE_Arena", "COASTAL_WATER_VISUAL_ONLY",
                      "SkyIsland_", "PublicCloudLift_", "PublicSeaDock",
                      "SEA_BOAT", "AIRSHIP", "SEA_BEAST", "SKY_BEAST",
                      "VehicleSeat", "ThrottleFloat", "SteerFloat",
                      "Workspace:Blockcast", "NeutralHordeCoastBeacon"]:
            with self.subTest(value=value):
                self.assertIn(value, SOURCE)

    def test_authorization_limits_and_reversibility(self):
        for value in ["MAX_CRAFT = 4", "MAX_PARTS_PER_WORLD = 95",
                      "TRAP_LIFETIME = 24", "VEHICLE_LIFETIME = 180",
                      'mode~="BATTLE_ROYALE"', "EGGRUMBLE_Eliminated",
                      "EGGRUMBLE_QueuedMode", "root.Position-part.Position",
                      "v.seat.Occupant", "world.Destroying:Connect",
                      "heartbeat:Disconnect()", "scenes[world]=nil"]:
            with self.subTest(value=value):
                self.assertIn(value, SOURCE)

    @staticmethod
    def fixture(root):
        server = {"$className": "ServerScriptService"}
        for i in range(31):
            name = ("EGGRUMBLE_LobbyCastleModesPreview" if i == 0 else
                    "EGGRUMBLE_SwarmCombat" if i == 1 else "CANONICAL_" + str(i))
            file = root / (name + ".server.luau")
            file.write_text("-- canonical source " + name + "\n")
            server[name] = {"$path": file.name}
        raw = {"name": "SOURCE_TEST_31", "tree": {"$className": "DataModel",
                                                  "ServerScriptService": server}}
        inp = root / "base31.project.json"
        inp.write_text(json.dumps(raw))
        return inp

    def test_off_and_on_is_exact(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = self.fixture(root)
            on = root / "sub" / "on32.project.json"
            off = root / "sub" / "off31.project.json"
            rec_on = mod.overlay(base, on, True)
            rec_off = mod.overlay(base, off, False)
            self.assertEqual(rec_on["source_count"], 32)
            self.assertEqual(rec_off["source_count"], 31)
            _, a = mod.flat(base)
            _, b = mod.flat(on)
            _, c = mod.flat(off)
            self.assertEqual(set(a), set(c))
            self.assertEqual(len(set(b) - set(a)), 1)
            self.assertEqual(
                {n: v.read_bytes() for n, v in a.items()},
                {n: b[n].read_bytes() for n in a})
            self.assertEqual(
                {n: v.read_bytes() for n, v in a.items()},
                {n: c[n].read_bytes() for n in a})

    def test_reject_duplicate_and_stale_base(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = self.fixture(root)
            bad = json.loads(base.read_text())
            del bad["tree"]["ServerScriptService"]["CANONICAL_30"]
            base.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError, "RED_NOT_CURRENT_31"):
                mod.overlay(base, root / "bad.project.json", True)

    def test_reject_overwrite_existing(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = self.fixture(root)
            with self.assertRaisesRegex(ValueError, "RED_OVERWRITE"):
                mod.overlay(base, base, True)


if __name__ == "__main__":
    unittest.main()
