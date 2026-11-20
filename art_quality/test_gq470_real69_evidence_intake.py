#!/usr/bin/env python3
"""Synthetic negative QA only. No test fixture is a real Studio screenshot."""
from __future__ import annotations

import hashlib
import json
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gq470_real69_evidence_intake import audit, actual_png_count, REQUIRED

HEAD = "e80973c354f14a0d0088577f3cc1a875454f0f8f"
SCENES = ("lobby", "field_wide", "castle", "sea", "forest",
          "neutral", "beast", "combat")


def png_chunk(name: bytes, data: bytes) -> bytes:
    body = name + data
    return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body))


def synthetic_png(index: int, width: int = 1280, height: int = 720) -> bytes:
    """Deliberately synthetic PNG fixture; never claim Studio evidence."""
    hdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    row = bytes([0]) + (bytes([index % 256, 10, 30]) * width)
    image_data = zlib.compress(row * height)
    filler = ("UNIT_TEST_FIXTURE_NOT_STUDIO_%d" % index).encode() + b"z" * 1100
    return (bytes([137,80,78,71,13,10,26,10]) +
            png_chunk(b"IHDR", hdr) +
            png_chunk(b"tEXt", filler) +
            png_chunk(b"IDAT", image_data) + png_chunk(b"IEND", b""))


class Real69EvidenceIntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.place = self.root / "EGGRUMBLE_REAL69_PRIVATE.rbxlx"
        # Synthetic receipt fixture; this test does not assess real Luau.
        self.place.write_bytes(b"<roblox>UNIT_TEST_FIXTURE</roblox>")
        self.sha = hashlib.sha256(self.place.read_bytes()).hexdigest()
        self.report = self.root / "ART_CHECK_REPORT.json"
        self.data = {
            "schema": "P0D_REAL69_GQ470_ART_CHECK_REPORT_V1",
            "only_formal_branch": "rc/p0d-s1-kids-rc01",
            "selected_profile": "REAL69_PRIVATE_COMPANION",
            "official_build_head": HEAD,
            "private_place_sha256": self.sha,
            "private_place_bytes": self.place.stat().st_size,
            "source_gate": {
                "status": "PASS_SOURCE_ONLY",
                "actual_place_scripts": 69,
                "selected_routes_source_class_hash_exact": 69,
                "verified_visual_feature_sources": 3,
            },
            "owner_accepted": False,
            "art_gate": "ART_NO_GO",
        }
        self.save()

    def save(self):
        self.report.write_text(json.dumps(self.data), encoding="utf-8")

    def check(self, manifest=None, screenshots=None):
        return audit(self.report, self.place, HEAD, manifest, screenshots)

    def test_missing_real_evidence_stays_no_go(self):
        result = self.check()
        self.assertEqual(result["image_evidence"]["required"], 32)
        self.assertEqual(result["image_evidence"]["actual_distinct_valid_png_files"], 0)
        self.assertEqual(result["image_evidence"]["status"], "BLOCKED")
        self.assertEqual(result["art_gate"], "ART_NO_GO")
        self.assertIs(result["owner_accepted"], False)

    def test_current_head_source_and_place_are_mandatory(self):
        self.data["official_build_head"] = "0" * 40
        self.save()
        with self.assertRaisesRegex(ValueError, "STALE_OR_WRONG"):
            self.check()
        self.data["official_build_head"] = HEAD
        self.data["private_place_sha256"] = "f" * 64
        self.save()
        with self.assertRaisesRegex(ValueError, "PLACE_BYTES_OR_SHA"):
            self.check()

    def test_forged_manifest_keys_are_not_actual_images(self):
        manifest = self.root / "manifest.json"
        fake = {"schema": "P0D_ART_STUDIO_EVIDENCE_V1",
                "before_head": "f" * 40,
                "after_head": HEAD,
                "after_place_sha256": self.sha,
                "shots": [{"scene": sc, "device": device, "version": version,
                           "file": "missing/" + sc + "-" + device + "-" + version + ".png"}
                          for sc in SCENES for device in ("pc", "android")
                          for version in ("before", "after")],
                "ratings": {}, "performance": {}, "critical_visual_blockers": [],
                "human_reviewer": ""}
        manifest.write_text(json.dumps(fake), encoding="utf-8")
        result = self.check(manifest, self.root)
        self.assertEqual(result["image_evidence"]["declared_shot_keys"], 32)
        self.assertEqual(result["image_evidence"]["actual_distinct_valid_png_files"], 0)
        self.assertEqual(result["image_evidence"]["status"], "BLOCKED")
        self.assertEqual(result["art_gate"], "ART_NO_GO")

    def test_real_file_counter_rejects_same_image_and_missing(self):
        one = self.root / "one.png"
        two = self.root / "two.png"
        one.write_bytes(synthetic_png(1))
        two.write_bytes(one.read_bytes())
        manifest = self.root / "manifest.json"
        shots = [
            {"scene": "forest", "device": "pc", "version": "before", "file": "one.png"},
            {"scene": "forest", "device": "pc", "version": "after", "file": "two.png"},
            {"scene": "forest", "device": "android", "version": "before", "file": "missing.png"},
        ]
        manifest.write_text(json.dumps({"shots": shots}), encoding="utf-8")
        self.assertEqual(actual_png_count(manifest, self.root), 1)
        two.write_bytes(synthetic_png(2))
        self.assertEqual(actual_png_count(manifest, self.root), 2)

    def test_invalid_first_duplicate_does_not_hide_valid_png(self):
        # A broken first capture must not consume the sole camera slot.
        # The shared manifest validator still flags duplicate rows as NO_GO.
        good = self.root / "good.png"
        good.write_bytes(synthetic_png(87))
        manifest = self.root / "invalid_first_duplicate.json"
        manifest.write_text(json.dumps({
            "schema": "P0D_ART_STUDIO_EVIDENCE_V1",
            "before_head": "f" * 40, "after_head": HEAD,
            "after_place_sha256": self.sha,
            "shots": [
                {"scene": "forest", "device": "pc", "version": "after",
                 "file": "missing.png"},
                {"scene": "forest", "device": "pc", "version": "after",
                 "file": "good.png"},
            ],
            "ratings": {}, "performance": {},
        }), encoding="utf-8")
        self.assertEqual(actual_png_count(manifest, self.root), 1)
        result = self.check(manifest, self.root)
        self.assertEqual(result["image_evidence"]["actual_distinct_valid_png_files"], 1)
        self.assertEqual(result["image_evidence"]["status"], "BLOCKED")
        self.assertEqual(result["art_gate"], "ART_NO_GO")

    def test_untrusted_manifest_shapes_fail_closed_with_report(self):
        # Malformed JSON structures must not crash the evidence intake CLI.
        # They cannot become visual proof, even with a valid source Place.
        m = self.root / "malformed_manifest.json"
        examples = [
            [],
            {"shots": [{"scene": [], "device": "pc", "version": "before",
                        "file": "fake.png"}]},
            {"shots": [], "ratings": {}, "performance": []},
        ]
        for invalid in examples:
            with self.subTest(manifest=invalid):
                m.write_text(json.dumps(invalid), encoding="utf-8")
                self.assertEqual(actual_png_count(m, self.root), 0)
                result = self.check(m, self.root)
                self.assertEqual(result["image_evidence"]["status"], "BLOCKED")
                self.assertEqual(result["art_gate"], "ART_NO_GO")
                self.assertIs(result["owner_accepted"], False)
                self.assertIn("INVALID_MANIFEST_STRUCTURE",
                              result["image_evidence"]["violations"])

    def test_stale_pngs_do_not_count_toward_current_rc_progress(self):
        # A genuine file path is not current-HEAD / current-Place proof.
        # A stale manifest must count ZERO valid files for this RC.
        png = self.root / "capture.png"
        png.write_bytes(synthetic_png(73))
        manifest = self.root / "stale_evidence.json"
        data = {
            "schema": "P0D_ART_STUDIO_EVIDENCE_V1",
            "before_head": "f" * 40, "after_head": HEAD,
            "after_place_sha256": self.sha,
            "shots": [{"scene": "castle", "device": "pc",
                       "version": "after", "file": "capture.png"}],
            "ratings": {}, "performance": {},
        }
        manifest.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(actual_png_count(manifest, self.root, HEAD, self.sha), 1)
        self.assertEqual(self.check(manifest, self.root)
                         ["image_evidence"]["actual_distinct_valid_png_files"], 1)

        data["after_head"] = "0" * 40
        manifest.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual(actual_png_count(manifest, self.root, HEAD, self.sha), 0)
        result = self.check(manifest, self.root)
        self.assertEqual(result["image_evidence"]["actual_distinct_valid_png_files"], 0)
        self.assertIn("AFTER_HEAD_NOT_CURRENT_REAL69",
                      result["image_evidence"]["violations"])
        self.assertEqual(result["art_gate"], "ART_NO_GO")

        data["after_head"] = HEAD
        data["after_place_sha256"] = "f" * 64
        manifest.write_text(json.dumps(data), encoding="utf-8")
        result = self.check(manifest, self.root)
        self.assertEqual(result["image_evidence"]["actual_distinct_valid_png_files"], 0)
        self.assertIn("STUDIO_PLACE_SHA_MISMATCH",
                      result["image_evidence"]["violations"])
        self.assertEqual(result["art_gate"], "ART_NO_GO")

    def test_pc_rating_4_does_not_meet_4_point_5_target(self):
        # No real captures: the synthetic manifest can only produce BLOCKED.
        m = self.root / "manifest.json"
        m.write_text(json.dumps({
            "schema": "P0D_ART_STUDIO_EVIDENCE_V1",
            "before_head": "f" * 40, "after_head": HEAD,
            "after_place_sha256": self.sha, "shots": [],
            "ratings": {"castle": {"pc": 4, "android": 4}},
            "performance": {}, "critical_visual_blockers": [],
        }), encoding="utf-8")
        result = self.check(m, self.root)
        self.assertIn("PC_ART_TARGET_4_5_NOT_MET:castle",
                      result["image_evidence"]["violations"])

if __name__ == "__main__":
    unittest.main()
