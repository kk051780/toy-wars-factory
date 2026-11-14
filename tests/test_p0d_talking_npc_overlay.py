"""Execute transactional PREP overlay behavior on a fabricated 65-file source-locked RC.

This is file-system policy verification, NOT Studio engine or Rojo QA.
"""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "rc_fastlane" / "apply_talking_npc.py"
spec = importlib.util.spec_from_file_location("p0d_talking_npc_overlay", SOURCE)
overlay = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(overlay)


def pin(b: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(b)).encode() + b"\0" + b).hexdigest()


class TalkingNPCOverlayTransactions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.dist = self.root / "original65"
        sources = self.dist / "src"
        (sources / "server").mkdir(parents=True)
        names = [
            "Game.server.luau",
            "TwinBiomes.server.luau",
            "RealmHunt.server.luau",
        ] + [f"Fixed_{i:02}.luau" for i in range(62)]
        self.assertEqual(len(names), 65)
        self.original = {}
        for n in names:
            path = sources / "server" / n
            body = f"-- original release policy {n}\nreturn nil\n".encode("utf8")
            path.write_bytes(body)
            self.original[path.relative_to(sources).as_posix()] = body
        pins = {k: pin(v) for k, v in sorted(self.original.items())}
        (self.dist / "SOURCE_LOCK.json").write_text(
            json.dumps({"total_scripts": 65, "blobs": pins}), encoding="utf8")
        (self.dist / "RC_FEATURE_LOCK.json").write_text(json.dumps({
            "total_sources": 65,
            "source_gitblobs": pins,
            "feature_flags": {"REALM_HUNT_V1": True},
        }), encoding="utf8")
        self.project = {
            "tree": {
                "ServerScriptService": {
                    "TrapRaidersS1": {"$path": "src/server"}
                },
                "StarterPlayer": {"StarterPlayerScripts": {}},
                "ServerStorage": {"$attributes": {"P0D_RC_ENABLE_STAR_SHARDS_V1": True}},
                "ReplicatedStorage": {},
            }
        }
        (self.dist / "default.project.json").write_text(
            json.dumps(self.project), encoding="utf8")
        self.output = self.root / "preview68"

    def test_enabled_produces_exact_68_and_preserves_all_65(self):
        self.assertTrue(overlay.apply(self.dist, True, self.output))
        self.assertTrue(self.output.is_dir())
        src = overlay.source_bytes(self.output)
        self.assertEqual(len(src), 68)
        for k, data in self.original.items():
            self.assertEqual(src[k], data)
        self.assertEqual(overlay.source_bytes(self.dist), self.original)
        self.assertTrue(json.loads(
            (self.output / "default.project.json").read_text("utf8")
        )["tree"]["ServerStorage"]["$attributes"][overlay.FLAG])
        self.assertFalse(
            "P0DTalkingNPCClient" in self.project["tree"]["StarterPlayer"]["StarterPlayerScripts"]
        )
        with self.assertRaises(ValueError):
            overlay.apply(self.dist, True, self.output)
        self.assertEqual(len(overlay.source_bytes(self.output)), 68)

    def test_disabled_is_strict_noop(self):
        self.assertFalse(overlay.apply(self.dist, False, self.output))
        self.assertFalse(self.output.exists())
        self.assertEqual(overlay.source_bytes(self.dist), self.original)

    def test_missing_enabled_realm_hunt_fails_without_any_publish(self):
        lockfile = self.dist / "RC_FEATURE_LOCK.json"
        lock = json.loads(lockfile.read_text("utf8"))
        lock["feature_flags"]["REALM_HUNT_V1"] = False
        lockfile.write_text(json.dumps(lock), encoding="utf8")
        with self.assertRaises(AssertionError):
            overlay.apply(self.dist, True, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(overlay.source_bytes(self.dist), self.original)

    def test_interrupted_copy_discards_candidate_and_original_is_intact(self):
        with patch.object(overlay, "_apply_inplace", side_effect=OSError("power cut")):
            with self.assertRaisesRegex(OSError, "power cut"):
                overlay.apply(self.dist, True, self.output)
        self.assertFalse(self.output.exists())
        self.assertEqual(overlay.source_bytes(self.dist), self.original)
        self.assertEqual(set(self.root.iterdir()), {self.dist})

    def test_path_nested_in_input_rejected_before_copy(self):
        with self.assertRaises(ValueError):
            overlay.apply(self.dist, True, self.dist / "nested-preview")
        self.assertFalse((self.dist / "nested-preview").exists())
        self.assertEqual(overlay.source_bytes(self.dist), self.original)


if __name__ == "__main__":
    unittest.main()
