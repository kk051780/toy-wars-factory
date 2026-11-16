#!/usr/bin/env python3
"""Offline negative tests; CI also runs this against pinned real #482 source."""
import os
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compose import (
    BOT, BOT_AFTER, BOT_BEFORE, HOST, HOST_AFTER, HOST_BEFORE,
    OWNER_BLOBS, compose, git_blob_sha, replace_exact, run
)

HOST_FIXTURE = "--!strict\nlocal session={}\n sessions[mode]=session\n -- Clean up only this finished match;\n"
BOT_FIXTURE = "--!strict\nlocal BotActors={}\n" + BOT_BEFORE + "\n"


class MembershipOverlayQA(unittest.TestCase):
    def test_author_original_change_is_selective_and_reversible(self):
        host, bot = compose(HOST_FIXTURE, BOT_FIXTURE)
        self.assertEqual(host.replace(HOST_AFTER, HOST_BEFORE), HOST_FIXTURE)
        self.assertEqual(bot.replace(BOT_AFTER, BOT_BEFORE), BOT_FIXTURE)
        self.assertIn("joined[player.UserId]==mode", host)
        self.assertIn(".isAI~=true", host)
        self.assertIn("sessions[mode]==session", host)
        self.assertIn('session.rules.phase=="ACTIVE"', host)
        self.assertIn("player.Parent==Players", host)
        self.assertIn("session.isCurrentHuman(player)", bot)

    def test_neither_parent_can_be_patched_twice(self):
        host, bot = compose(HOST_FIXTURE, BOT_FIXTURE)
        with self.assertRaises(ValueError):
            compose(host, BOT_FIXTURE)
        with self.assertRaises(ValueError):
            compose(HOST_FIXTURE, bot)

    def test_reject_missing_or_duplicate_insertion_point(self):
        with self.assertRaises(ValueError):
            replace_exact("--!strict\n", HOST_BEFORE, HOST_AFTER, HOST)
        with self.assertRaises(ValueError):
            replace_exact(HOST_FIXTURE + HOST_FIXTURE, HOST_BEFORE, HOST_AFTER, HOST)

    def test_reject_non_strict_source(self):
        with self.assertRaises(ValueError):
            compose(HOST_FIXTURE.replace("--!strict\n", ""), BOT_FIXTURE)

    def test_blob_hash_is_git_blob_not_raw_sha(self):
        self.assertEqual(git_blob_sha(b"test\n"), "9daeafb9864cf43055ae93beb0afd6c7d144bfa4")

    def test_pinned_real_author_sources_when_supplied(self):
        root = os.getenv("GQ_OWNER_SOURCE_DIR")
        if not root:
            self.skipTest("Real pinned author source provided on GitHub Actions only")
        with tempfile.TemporaryDirectory() as tmp:
            report = run(Path(root), Path(tmp))
            self.assertEqual(set(report["source_files"]), set(OWNER_BLOBS))
            self.assertFalse(report["official_rc_changed"])
            self.assertFalse(report["new_runtime_authority"])
            self.assertEqual(report["source_files"][HOST]["owner_blob"], OWNER_BLOBS[HOST])
            self.assertEqual(report["source_files"][BOT]["owner_blob"], OWNER_BLOBS[BOT])
            self.assertNotEqual(report["source_files"][BOT]["overlay_blob"], OWNER_BLOBS[BOT])
            self.assertNotEqual(report["source_files"][HOST]["overlay_blob"], OWNER_BLOBS[HOST])
            h = (Path(tmp) / HOST).read_text()
            b = (Path(tmp) / BOT).read_text()
            self.assertEqual(h.count("session.isCurrentHuman=function"), 1)
            self.assertEqual(b.count("session.isCurrentHuman(player)"), 1)


if __name__ == "__main__":
    unittest.main()
