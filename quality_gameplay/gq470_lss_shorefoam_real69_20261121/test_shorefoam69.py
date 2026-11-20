#!/usr/bin/env python3
"""Mutation and source-selection QA. A PASS is NOT a Studio visual approval."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from patch_shorefoam69 import (
    BASE_HEAD, MARK, NEW, OLD, ORIGINAL_PATH, TARGET, TARGET_FILE,
    build, digest, patch, unpatch,
)

ROOT = Path(__file__).resolve().parents[2]


class ShoreFoamSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.committed = (ROOT / ORIGINAL_PATH).read_text(encoding="utf-8")
        cls.original = unpatch(cls.committed)

    def test_real_original_luau_is_modified_and_byte_reversible(self):
        self.assertEqual(patch(self.original), self.committed)
        self.assertEqual(unpatch(self.committed), self.original)
        self.assertEqual(self.committed.count(MARK), 1)
        self.assertEqual(self.committed.count("ShoreFoam_"), 1)
        self.assertEqual(self.committed.count("foam.Shape=Enum.PartType.Cylinder"), 1)

    def test_visual_and_world_security_contract(self):
        self.assertIn("foam.CanQuery=false", NEW)
        self.assertIn("foam.CastShadow=false", NEW)
        self.assertIn("Enum.Material.SmoothPlastic,false,.33", NEW)
        self.assertNotIn('Instance.new(', NEW)
        self.assertNotIn('TweenService', NEW)
        self.assertNotIn('RemoteEvent', NEW)
        self.assertNotIn('MarketplaceService', NEW)
        self.assertEqual(OLD.count("foam=put("), 1)
        self.assertEqual(NEW.count("foam=put("), 1)
        for frozen in (
            "MAX_PARTS_PER_WORLD = 95",
            "PublicOffshoreShuttle",
            "PublicCloudLift_",
            "local function makeRide",
            "local function musouConfirmedMilestone",
            "COASTAL_WATER_VISUAL_ONLY",
            "OFFSHORE_NAVIGABLE_SEA_LANE",
        ):
            self.assertIn(frozen, self.committed)
            self.assertIn(frozen, self.original)

    def test_fail_closed_when_anchor_or_owner_drift(self):
        mutations = {
            "already applied": self.committed,
            "removed sea": self.original.replace("COASTAL_WATER_VISUAL_ONLY", "BAD_SEA"),
            "removed dock": self.original.replace("PublicOffshoreShuttle", "BAD_DOCK"),
            "removed craft": self.original.replace("local function makeRide", "BAD_CRAFT"),
            "changed foam": self.original.replace("Vector3.new(55,.10,2.3)", "Vector3.new(55,1,2.3)"),
            "double foam": self.original.replace(OLD, OLD + "\n" + OLD, 1),
            "missing cloud": self.original.replace("PublicCloudLift_", "BAD_CLOUD_LIFT"),
        }
        for label, raw in mutations.items():
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, "RED_GQ470_SHOREFOAM_"):
                    patch(raw)

    def test_foam_sightline_and_route_geometry_static_budget(self):
        # A source-level geometry bound, NOT a claim of real camera visibility.
        import math
        self.assertIn("local xi=x-265+(i-1)*106", NEW)
        self.assertIn("math.sin(i*1.73)*1.55", NEW)
        self.assertIn("local width=47+(i%3)*5", NEW)
        self.assertIn("local surfAngle=math.rad(sideways*(7+(i%3)*4))", NEW)
        self.assertIn("foam.Shape=Enum.PartType.Cylinder", NEW)
        self.assertIn("foam.CanQuery=false", NEW)
        self.assertIn("foam.CastShadow=false", NEW)
        self.assertIn("Enum.Material.SmoothPlastic,false,.33", NEW)
        self.assertIn("p.CanCollide=collide; p.CanTouch=collide", self.committed)
        bounds = []
        for i in range(1, 7):
            cx = -265 + (i-1)*106
            cz = -63 + math.sin(i*1.73)*1.55
            angle = math.radians((1 if i%2 == 0 else -1)*(7+(i%3)*4))
            width = 47 + (i%3)*5
            depth = 2.0 + (i%2)*.45
            # Conservative projected bounding box for the shallow surf patch.
            hx = abs(math.cos(angle))*width/2 + abs(math.sin(angle))*depth/2
            hz = abs(math.sin(angle))*width/2 + abs(math.cos(angle))*depth/2
            bounds.append((cx-hx,cx+hx,cz-hz,cz+hz))
            # Public land dock is centered at shoreZ-92 with 18-stud depth.
            # Surf near shoreZ-63 must not invade its public passage.
            self.assertGreater(cz-hz, -83)
            self.assertLess(cz+hz, -45)
            self.assertLessEqual(width, 57)
            self.assertLessEqual(depth, 2.45)
        self.assertEqual(len(bounds), 6)
        for current, following in zip(bounds, bounds[1:]):
            self.assertGreater(following[0]-current[1], 35)

    def test_visual_palette_is_less_glary_without_extra_surface(self):
        old_brightness = sum((225,247,248))/3
        variants = ((190,225,228), (207,235,237))
        for tint in variants:
            self.assertLess(sum(tint)/3, old_brightness)
        self.assertEqual(NEW.count("foam=put("), OLD.count("foam=put("))
        self.assertNotIn("local extraFoam=", NEW)
        self.assertNotIn("Instance.new", NEW)

    def _archive(self, path: Path, *, corrupt: bool = False):
        # Fake inputs ONLY test verifier behaviour. Real CI must separately
        # download the pinned official 69-source workflow artifact.
        target = self.original.encode()
        tree = {"ServerScriptService": {
            "EGGRUMBLE_LandSeaSkyTraversal": {
                "$path": TARGET_FILE, "$className": "Script"}}}
        hashes = {TARGET: digest(target)}
        bodies = {TARGET_FILE: target}
        for i in range(68):
            name = "FakeSource%02d" % i
            route = "ServerScriptService/" + name
            f = "sources/" + route + ".server.luau"
            data = ("--!nonstrict\nreturn " + str(i) + "\n").encode()
            tree["ServerScriptService"][name] = {"$path": f, "$className": "Script"}
            hashes[route] = digest(data)
            bodies[f] = data
        receipt = {
            "build_head": BASE_HEAD, "selected_source_count": 69,
            "source_hashes": hashes,
        }
        if corrupt:
            bodies[TARGET_FILE] += b"--mutated"
        with ZipFile(path, "w") as z:
            z.writestr("EGGRUMBLE_REAL69.project.json", json.dumps({"tree": tree}))
            z.writestr("REAL69_LEGACY_INTAKE_RECEIPT.json", json.dumps(receipt))
            for name, data in bodies.items():
                z.writestr(name, data)
        return bodies

    def test_real69_one_route_inverse_and_receipt(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            source_zip = root / "fake_fixture_not_engine.zip"
            original = self._archive(source_zip)
            dst = root / "candidate"
            report = build(source_zip, dst)
            self.assertEqual(report["selected_source_count"], 69)
            self.assertEqual(report["changed_selected_routes"], [TARGET])
            self.assertEqual(report["unchanged_selected_routes"], 68)
            self.assertEqual(report["new_parts"], 0)
            self.assertTrue(report["rollback_byte_exact"])
            self.assertFalse(report["formal_rc_changed"])
            for name, expected in original.items():
                found = (dst / name).read_bytes()
                if name == TARGET_FILE:
                    self.assertEqual(found.decode(), patch(expected.decode()))
                    self.assertEqual(unpatch(found.decode()).encode(), expected)
                else:
                    self.assertEqual(found, expected)
            receipt = json.loads((dst / "REAL69_LEGACY_INTAKE_RECEIPT.json").read_text())
            self.assertEqual(receipt["source_hashes"][TARGET],
                             digest((dst / TARGET_FILE).read_bytes()))
            self.assertFalse(receipt["candidate_only_gq470_shorefoam"]["official_rc_adopted"])
            self.assertEqual(receipt["candidate_only_gq470_shorefoam"]["art_gate"], "NO_GO")
            with self.assertRaisesRegex(ValueError, "RED_GQ470_SHOREFOAM_DEST_EXISTS"):
                build(source_zip, dst)

    def test_reject_corrupt_zip_and_wrong_build_head(self):
        with tempfile.TemporaryDirectory() as dirname:
            root = Path(dirname)
            zip_path = root / "bad_hash.zip"
            self._archive(zip_path, corrupt=True)
            with self.assertRaisesRegex(ValueError, "RED_GQ470_SHOREFOAM_BEFORE_SHA_"):
                build(zip_path, root / "bad_output")
            good = root / "good.zip"
            self._archive(good)
            wrong = root / "bad_head.zip"
            with ZipFile(good) as z, ZipFile(wrong, "w") as out:
                for name in z.namelist():
                    data = z.read(name)
                    if name == "REAL69_LEGACY_INTAKE_RECEIPT.json":
                        receipt = json.loads(data)
                        receipt["build_head"] = "0"*40
                        data = json.dumps(receipt).encode()
                    out.writestr(name, data)
            with self.assertRaisesRegex(ValueError, "RED_GQ470_SHOREFOAM_BASE_RC_HEAD"):
                build(wrong, root / "bad_head_out")


if __name__ == "__main__":
    unittest.main()
