"""The restored historical inputs must remain exact and fail closed on drift."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "quality_gameplay/gq8_real63_intake_20261119/restore_original_inputs.py"
INPUTS = ADAPTER.parent / "immutable_inputs"
SPEC = importlib.util.spec_from_file_location("gq8_original_input_restore", ADAPTER)
restore = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(restore)

ORIGINAL_ZIPS = {
    "base55": "a7a041d56ffe018b65f69c34cd3828c5031a3261ec84ca8b3888b48dc14c3da7",
    "trade62": "f1c65bdbed34d09f72ee787c270f4227c46d5eab2a281a9a58d23a0fc7d3397f",
    "formal62": "7ba68def135bdf1d985968a25bf12c99d5f5dbcdfc0f3efed37819e5fdeddd7b",
    "formal63": "003268ce1d310db060ed6ee39eecb3a9dba265175a292e8b75b10151a0ead0a3",
    "viral56": "0c3033647184adb5c6dd4aea27721f8719671f96d21291375e2e42662e59d619",
}


class OriginalInputs(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="gq8-original-inputs-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def clone_inputs(self):
        return Path(shutil.copytree(INPUTS, self.root / "inputs"))

    def test_exact_seven_packets_and_all316_files(self):
        before = restore.snapshot(INPUTS)
        out = self.root / "restored"
        result = restore.restore(out)
        expected = {}
        for packet in restore.PACKETS:
            with zipfile.ZipFile(INPUTS / (packet + ".zip")) as archive:
                for name in archive.namelist():
                    expected[packet + "/" + name] = archive.read(name)
        actual = {p.relative_to(out).as_posix(): p.read_bytes() for p in out.rglob("*") if p.is_file()}
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 316)
        self.assertEqual(before, restore.snapshot(INPUTS))
        self.assertEqual(result["status"], "PASS_IMMUTABLE_TRANSPORT_ONLY")
        self.assertEqual(result["packet_count"], 7)
        self.assertEqual(result["original_zip_packets"], 5)
        self.assertEqual(result["reconstructed_recipe_packets"], 2)
        self.assertFalse(result["canonical_ci_or_rc_adoption_proven"])
        self.assertFalse(result["native_or_studio_pass_claimed"])
        self.assertEqual(hashlib.sha256(actual["hud59/EGGRUMBLE_REAL59_HUD_MAP_PRIVATE.rbxlx"]).hexdigest(),
                         "bde044295bc286df9f42a98dd351ac09aac1389b063136cb08fe2fbcde7ca327")
        self.assertEqual(hashlib.sha256(actual["counter56/GQ822_REAL56.rbxlx"]).hexdigest(),
                         "323a80e6ed343eb006103bf241c1c348321a8d85c5027c148e371d88501597fd")

    def test_original_and_reconstructed_provenance_are_distinct(self):
        lock = restore.load_lock(INPUTS)
        for name, digest in ORIGINAL_ZIPS.items():
            with self.subTest(packet=name):
                self.assertEqual(hashlib.sha256((INPUTS / (name + ".zip")).read_bytes()).hexdigest(), digest)
                self.assertEqual(lock["packets"][name]["source_kind"], "DOWNLOADED_ORIGINAL_ARTIFACT")
        for name in ("hud59", "counter56"):
            row = lock["packets"][name]
            self.assertEqual(row["historical_receipt_raw_byte_hash"], "UNKNOWN")
            self.assertFalse(row["original_artifact_downloaded"])
            self.assertFalse(row["new_native_run_claimed"])
            self.assertNotEqual(row["archive"]["sha256"], row["original_zip"]["sha256"])
            self.assertFalse(row["reconstruction"]["historical_receipt_byte_equality_claimed"])
        workflow = (ROOT / ".github/workflows/gq8-real63-source-composite.yml").read_text()
        self.assertEqual(len(lock["required_live_origin_run_checks"]), 8)
        for original in lock["required_live_origin_run_checks"]:
            self.assertIn(str(original["run"]) + ":" + original["head"], workflow)

    def test_corrupt_archive_cannot_create_output(self):
        inputs = self.clone_inputs()
        path = inputs / "formal63.zip"
        data = bytearray(path.read_bytes())
        data[len(data) // 2] ^= 1
        path.write_bytes(data)
        output = self.root / "output"
        with self.assertRaisesRegex(ValueError, "ARCHIVE_IDENTITY"):
            restore.restore(output, inputs)
        self.assertFalse(output.exists())

    def test_rebinding_manifest_to_corrupt_archive_does_not_bypass_literal_lock(self):
        inputs = self.clone_inputs()
        archive = inputs / "hud59.zip"
        archive.write_bytes(b"substituted input")
        lock = json.loads((inputs / "LOCK.json").read_text())
        lock["packets"]["hud59"]["archive"].update(restore.identity(archive.read_bytes()))
        (inputs / "LOCK.json").write_text(json.dumps(lock))
        with self.assertRaisesRegex(ValueError, "LOCK_IDENTITY"):
            restore.restore(self.root / "output", inputs)
        self.assertFalse((self.root / "output").exists())

    def test_missing_or_extra_input_is_rejected(self):
        inputs = self.clone_inputs()
        missing = inputs / "counter56.zip"
        data = missing.read_bytes()
        missing.unlink()
        with self.assertRaisesRegex(ValueError, "INPUT_FILE_SET"):
            restore.restore(self.root / "out1", inputs)
        missing.write_bytes(data)
        (inputs / "unreviewed.zip").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "INPUT_FILE_SET"):
            restore.restore(self.root / "out2", inputs)
        self.assertFalse((self.root / "out1").exists())
        self.assertFalse((self.root / "out2").exists())

    def test_existing_output_and_symlinked_parent_are_preserved(self):
        output = self.root / "occupied"
        output.mkdir()
        sentinel = output / "keep.txt"
        sentinel.write_bytes(b"existing user data")
        with self.assertRaisesRegex(ValueError, "OUTPUT_MUST_BE_NEW"):
            restore.restore(output)
        self.assertEqual(sentinel.read_bytes(), b"existing user data")
        empty = self.root / "already-empty"
        empty.mkdir()
        with self.assertRaisesRegex(ValueError, "OUTPUT_MUST_BE_NEW"):
            restore.restore(empty)
        linked = self.root / "linked"
        linked.symlink_to(output, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "SYMLINK_PATH"):
            restore.restore(linked / "escape")
        self.assertEqual(sorted(p.name for p in output.iterdir()), ["keep.txt"])

    def test_decoder_rejects_unsafe_entries_even_with_matching_container_digest(self):
        # Decoder unit checks do not replace the public literal-lock boundary.
        for name, mode, duplicate, reason in (
            ("../escape", stat.S_IFREG | 0o644, False, "UNSAFE_MEMBER_NAME"),
            ("/escape", stat.S_IFREG | 0o644, False, "UNSAFE_MEMBER_NAME"),
            (".", stat.S_IFREG | 0o644, False, "UNSAFE_MEMBER_NAME"),
            ("link", stat.S_IFLNK | 0o777, False, "NON_REGULAR_MEMBER"),
            ("same", stat.S_IFREG | 0o644, True, "DUPLICATE_MEMBER"),
        ):
            with self.subTest(name=name, duplicate=duplicate):
                buffer = io.BytesIO()
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", UserWarning)
                    with zipfile.ZipFile(buffer, "w") as archive:
                        entry = zipfile.ZipInfo(name)
                        entry.create_system = 3
                        entry.external_attr = mode << 16
                        archive.writestr(entry, b"payload")
                        if duplicate:
                            archive.writestr(entry, b"payload")
                raw = buffer.getvalue()
                row = {"archive": restore.identity(raw), "members": {name: restore.identity(b"payload")},
                       "file_count": 1, "unpacked_bytes": 7}
                with self.assertRaisesRegex(ValueError, reason):
                    restore.decode_packet(raw, row)

    def test_member_content_and_inventory_are_checked_after_container_digest(self):
        raw = (INPUTS / "formal62.zip").read_bytes()
        original = restore.load_lock(INPUTS)["packets"]["formal62"]
        row = copy.deepcopy(original)
        first = next(iter(row["members"]))
        row["members"][first]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "MEMBER_IDENTITY"):
            restore.decode_packet(raw, row)
        row = copy.deepcopy(original)
        del row["members"][first]
        with self.assertRaisesRegex(ValueError, "MEMBER_SET"):
            restore.decode_packet(raw, row)

    def test_late_input_drift_rejects_and_removes_only_owned_output(self):
        inputs = self.clone_inputs()
        output = self.root / "output"
        real_snapshot = restore.snapshot
        calls = 0
        def changing_snapshot(path):
            nonlocal calls
            calls += 1
            if calls == 3:
                (output / "foreign.txt").write_bytes(b"intervening work")
                with (inputs / "formal63.zip").open("ab") as stream:
                    stream.write(b"drift")
            return real_snapshot(path)
        with mock.patch.object(restore, "snapshot", side_effect=changing_snapshot):
            with self.assertRaisesRegex(ValueError, "INPUTS_OR_RESTORER_CHANGED"):
                restore.restore(output, inputs)
        self.assertEqual([p.relative_to(output).as_posix() for p in output.rglob("*") if p.is_file()],
                         ["foreign.txt"])
        self.assertEqual((output / "foreign.txt").read_bytes(), b"intervening work")

    def test_cli_failure_has_nonzero_exit_and_no_success_claim(self):
        output = self.root / "occupied"
        output.mkdir()
        result = subprocess.run([sys.executable, "-B", str(ADAPTER), "--out", str(output)], capture_output=True)
        self.assertEqual(result.returncode, 1)
        message = json.loads(result.stdout)
        self.assertEqual(message["status"], "FAIL_NO_INPUT_ADMISSION")
        self.assertNotIn("PASS", result.stdout.decode())


if __name__ == "__main__":
    unittest.main()
