"""Unit/negative tests for the exact two-author source patch; NOT Studio QA."""
import tempfile
import unittest
from pathlib import Path

import patch_sources as p

HOST = """local joined={}
local sessions={}
local function startSession(mode:string)
 local session={rules={phase="ACTIVE"}}
 sessions[mode]=session
  local actor=joined[p.UserId]
end
"""
ITEM = """local Items={}
local function canUse(player:Player,session:any):boolean
 local roster=session and session.rules and session.rules.castles
 local castle=roster and roster[tostring(player.UserId)]
 return castle~=nil and castle.alive==true and session.rules.phase=="ACTIVE"
end
return Items
"""


class CandidateTests(unittest.TestCase):
    def test_two_patch_sites_are_unique_and_guarded(self):
        host, item = p.patch_sources(HOST, ITEM)
        self.assertEqual(host.count(p.MARKER), 1)
        self.assertEqual(item.count(p.MARKER), 1)
        self.assertIn('sessions[mode]==session', host)
        self.assertIn('joined[actor.UserId]==mode', host)
        self.assertIn('actor.Parent~=nil', host)
        self.assertIn('session.rules.phase=="ACTIVE"', host)
        self.assertIn('type(authorize)~="function" then return false', item)
        self.assertIn('pcall(authorize,player)', item)
        self.assertIn('not ok or allowed~=true then return false', item)

    def test_keep_existing_game_and_item_authority(self):
        host, item = p.patch_sources(HOST, ITEM)
        self.assertEqual(host.replace(p.HOST_INSERT, ""), HOST)
        self.assertEqual(item.replace(p.ITEM_INSERT, ""), ITEM)
        self.assertNotIn("RemoteEvent", p.HOST_INSERT + p.ITEM_INSERT)
        self.assertNotIn("DataStore", p.HOST_INSERT + p.ITEM_INSERT)
        self.assertNotIn("TakeDamage", p.HOST_INSERT + p.ITEM_INSERT)

    def test_reapply_rejected(self):
        h, i = p.patch_sources(HOST, ITEM)
        with self.assertRaisesRegex(ValueError, "already exists"):
            p.patch_sources(h, i)

    def test_source_drift_and_duplicate_anchor_rejected(self):
        with self.assertRaisesRegex(ValueError, "anchor"):
            p.guarded_insert(ITEM.replace(p.ITEM_ANCHOR, ""),
                             p.ITEM_ANCHOR, p.ITEM_INSERT, "item")
        with self.assertRaisesRegex(ValueError, "duplicated"):
            p.guarded_insert(ITEM + p.ITEM_ANCHOR,
                             p.ITEM_ANCHOR, p.ITEM_INSERT, "item")

    def test_author_presence_required(self):
        with self.assertRaisesRegex(ValueError, "not the source-author"):
            p.patch_sources(HOST.replace("joined[p.UserId]", "joined[actor.UserId]"), ITEM)

    def test_exact_blob_lock_fails_before_output_created(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host, item, output = root / "h", root / "i", root / "out"
            host.write_text(HOST, encoding="utf-8")
            item.write_text(ITEM, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "SOURCE_LOCK mismatch"):
                p.generate(host, item, output)
            self.assertFalse(output.exists())

    def test_pinned_fixture_generates_immutable_manifest(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            host, item, output = root / "h", root / "i", root / "out"
            host.write_text(HOST, encoding="utf-8")
            item.write_text(ITEM, encoding="utf-8")
            receipt = p.generate(host, item, output,
                                 p.git_blob_sha(host.read_bytes()),
                                 p.git_blob_sha(item.read_bytes()))
            self.assertEqual(receipt["new_authorities"], 0)
            self.assertEqual(receipt["source_changes"], 2)
            self.assertEqual(receipt["studio_android_owner"], "NOT_TESTED")
            self.assertTrue((output / "candidate_manifest.json").is_file())
            with self.assertRaisesRegex(ValueError, "overwrite"):
                p.generate(host, item, output,
                           p.git_blob_sha(host.read_bytes()),
                           p.git_blob_sha(item.read_bytes()))

    def test_model_owner_mode_epoch_invariants(self):
        # Model contract only; real native/Studio mode transitions still required.
        def eligible(actor_present, actor_mode, session_mode, same_session, phase):
            return (actor_present and actor_mode == session_mode
                    and same_session and phase == "ACTIVE")
        self.assertTrue(eligible(True, "TEAM", "TEAM", True, "ACTIVE"))
        for case in (
            (False, "TEAM", "TEAM", True, "ACTIVE"),    # disconnect
            (True, "BATTLE_ROYALE", "TEAM", True, "ACTIVE"),  # stale owner
            (True, "TEAM", "TEAM", False, "ACTIVE"),    # retired round
            (True, "TEAM", "TEAM", True, "FINISHED"),   # result screen
        ):
            self.assertFalse(eligible(*case))


if __name__ == "__main__":
    unittest.main()
