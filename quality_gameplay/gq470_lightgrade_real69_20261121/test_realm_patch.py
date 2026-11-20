#!/usr/bin/env python3
"""REAL69 native-art-source candidate negative tests; source not engine proof."""
import hashlib
import json
import os
import pathlib
import tempfile
import unittest
import zipfile

from patch_realm_color69 import (
    BASE_HEAD, BEFORE_SHA, AFTER_SHA, MARK, TARGET, TARGET_FILE,
    build, patch, sha, unpatch,
)

ARTIFACT = os.environ.get("REAL69_ARTIFACT")


class SourcePatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not ARTIFACT:
            raise unittest.SkipTest("Official REAL69 artifact not provided")
        cls.artifact = pathlib.Path(ARTIFACT).resolve()
        with zipfile.ZipFile(cls.artifact) as z:
            cls.original = z.read(TARGET_FILE)

    def test_actual_original_and_reversible_patch(self):
        self.assertEqual(sha(self.original), BEFORE_SHA)
        original = self.original.decode("utf-8")
        candidate = patch(original)
        self.assertIn(MARK, candidate)
        self.assertEqual(unpatch(candidate), original)
        self.assertEqual(candidate.count("RunService.RenderStepped:Connect"), 1)
        self.assertEqual(candidate.count('Instance.new("ColorCorrectionEffect")'), 1)
        self.assertNotIn('Instance.new("Part")', candidate)
        self.assertIn('remote:FireServer("FLIGHT"', candidate)

    def test_actual_69_route_build_and_source_lock(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = pathlib.Path(tmp) / "candidate69"
            report = build(self.artifact, dest)
            self.assertEqual(report["formal_base_sha"], BASE_HEAD)
            self.assertEqual(report["selected_source_count"], 69)
            self.assertEqual(report["changed_selected_routes"], [TARGET])
            self.assertEqual(report["unaltered_selected_routes"], 68)
            self.assertTrue(report["rollback_source_byte_exact"])
            self.assertEqual(report["new_renderstep_connections"], 0)
            self.assertEqual(report["new_part_count"], 0)
            self.assertEqual(report["new_color_correction_effects_max"], 1)
            self.assertEqual((dest / "OFF69_REALM_GRADE_ORIGINAL.client.luau").read_bytes(),
                             self.original)
            self.assertEqual(sha((dest / TARGET_FILE).read_bytes()),
                             report["candidate_source_sha256"])
            with self.assertRaisesRegex(ValueError, "RED_REALM_GRADE_OUT_ALREADY_EXISTS"):
                build(self.artifact, dest)

    def test_manifest_pins_exact_candidate_and_cannot_relabel_formal(self):
        manifest = json.loads(pathlib.Path(__file__).with_name("SOURCE_SELECT_MANIFEST.json").read_text())
        self.assertEqual(manifest["selected_existing_route"], TARGET)
        self.assertEqual(manifest["selected_source_sha256"], AFTER_SHA)
        self.assertEqual(manifest["original_source_sha256"], BEFORE_SHA)
        self.assertEqual(manifest["formal_base_head"], BASE_HEAD)
        self.assertEqual(manifest["untouched_selected_source_count"], 68)
        self.assertEqual(manifest["additional_renderstep_connections"], 0)
        self.assertEqual(manifest["additional_parts"], 0)
        self.assertFalse(manifest["approved_for_formal_rc_write"])
        self.assertTrue(manifest["no_whole_pr_merge"])

    def test_negative_source_mutations_fail_closed(self):
        old = self.original.decode("utf-8")
        for label, changed in (
            ("remote", old.replace("EGGRUMBLE_RealmBattleIntent_V1",
                                   "FAKE_Intent", 1)),
            ("weather", old.replace('core:GetAttribute("RealmWeather")',
                                    'core:GetAttribute("FakeWeather")', 1)),
            ("subsea", old.replace('currentKind=="SUBSEA"',
                                   'currentKind=="SKY_ONLY"', 1)),
            ("already_applied", patch(old)),
            ("script_drift", old.replace(" local isDiver=", "local isDiver=", 1)),
            ("renderloop", old.replace("RunService.RenderStepped:Connect",
                                       "RunService.Heartbeat:Connect", 1)),
        ):
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, "RED_REALM_GRADE_"):
                    patch(changed)

    def test_reject_wrong_selected_sha_even_if_zip_decodes(self):
        with tempfile.TemporaryDirectory() as tmp:
            corrupted = pathlib.Path(tmp) / "corrupt.zip"
            with zipfile.ZipFile(self.artifact) as original, zipfile.ZipFile(corrupted, "w") as out:
                for name in original.namelist():
                    contents = original.read(name)
                    if name == TARGET_FILE:
                        contents += b"\n-- unauthorized edit\n"
                    out.writestr(name, contents)
            with self.assertRaisesRegex(ValueError, "RED_REALM_GRADE_SOURCE_MISMATCH_"):
                build(corrupted, pathlib.Path(tmp) / "bad-output")


if __name__ == "__main__":
    unittest.main()
