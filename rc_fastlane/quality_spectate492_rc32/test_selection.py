import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[0]
ROOT = Path(__file__).resolve().parents[2]
AUTHOR = (ROOT / "_gq492_original" / "handoffs" /
          "P0D-PQG-SPECTATE-20261116-01" / "EGGRUMBLE_Spectate.client.luau")
spec = importlib.util.spec_from_file_location("gq492_admission", HERE / "admit_spectator.py")
admit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admit)


class ImmutableSpectate32Intake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not AUTHOR.exists():
            raise RuntimeError("RED: pinned #492 checkout missing; cannot replace with mock source")
        assert admit.git_blob(AUTHOR.read_bytes()) == admit.AUTHOR_BLOB

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        original_dir = self.root / "original"
        original_dir.mkdir()
        server = {
            "$className": "ServerScriptService",
            "EGGRUMBLE_LobbyCastleModesPreview": {
                "$path": "EGGRUMBLE_LobbyCastleModesPreview.server.luau"
            },
            "EGGRUMBLE_CastleMatchRules": {"$path": "EGGRUMBLE_CastleMatchRules.luau"},
        }
        (original_dir / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").write_text("-- host\n")
        (original_dir / "EGGRUMBLE_CastleMatchRules.luau").write_text("-- rules\n")
        for i in range(29):
            n = "ORIGINAL_SOURCE_" + str(i)
            server[n] = {"$path": n + ".luau"}
            (original_dir / (n + ".luau")).write_text("-- " + n + "\n")
        project = {"name": "SINGLE_CANONICAL_SOURCE_31",
                   "tree": {"ServerScriptService": server,
                            "StarterPlayer": {"$className":"StarterPlayer",
                                "StarterPlayerScripts":{"$className":"StarterPlayerScripts"}}}}
        self.base = original_dir / "base.project.json"
        self.base.write_text(json.dumps(project))
        self.out = self.root / "candidate" / "spectate32.project.json"
        self.receipt = self.root / "candidate" / "receipt.json"

    def test_adds_one_pinned_spectator_without_modifying_31(self):
        before = admit.source_map(json.loads(self.base.read_text()), self.base)
        original_sha = {k: admit.git_blob(p.read_bytes()) for k,(p,_) in before.items()}
        admit.prepare(self.base, AUTHOR, self.out, self.receipt)
        result = admit.source_map(json.loads(self.out.read_text()), self.out)
        self.assertEqual(len(result), 32)
        self.assertEqual(result[admit.NAME], (AUTHOR.resolve(), "LocalScript"))
        self.assertEqual(original_sha, {k: admit.git_blob(result[k][0].read_bytes())
                                         for k in before})
        self.assertFalse(json.loads(self.receipt.read_text())["formal_rc_adopted"])

    def test_duplicate_spectator_is_red(self):
        p = json.loads(self.base.read_text())
        p["tree"]["ServerScriptService"][admit.NAME] = {
            "$path": "EGGRUMBLE_CastleMatchRules.luau"}
        # Duplicate -> count32 or spectator collision, fail safely either way.
        self.base.write_text(json.dumps(p))
        with self.assertRaises(ValueError):
            admit.prepare(self.base, AUTHOR, self.out, self.receipt)

    def test_missing_game_host_is_red(self):
        p = json.loads(self.base.read_text())
        p["tree"]["ServerScriptService"]["NOT_HOST"] = p["tree"]["ServerScriptService"].pop(
            "EGGRUMBLE_LobbyCastleModesPreview")
        self.base.write_text(json.dumps(p))
        with self.assertRaisesRegex(ValueError, "canonical 31-source"):
            admit.prepare(self.base, AUTHOR, self.out, self.receipt)

    def test_modified_original_author_source_is_red(self):
        changed = self.root / "EGGRUMBLE_Spectate.client.luau"
        changed.write_bytes(AUTHOR.read_bytes() + b"\n-- mutation")
        with self.assertRaisesRegex(ValueError, "immutable spectator source drift"):
            admit.prepare(self.base, changed, self.out, self.receipt)

    def test_refuses_in_place_project_overwrite(self):
        with self.assertRaisesRegex(ValueError, "cannot overwrite"):
            admit.prepare(self.base, AUTHOR, self.base, self.receipt)


    def test_exact_official_base_sha_is_in_receipt(self):
        sha="89cbeb03d74ddbe3408ef805fed6683ff6abc508"
        admit.prepare(self.base, AUTHOR, self.out, self.receipt, rc_head=sha)
        self.assertEqual(json.loads(self.receipt.read_text())["base_rc_head"], sha)

    def test_invalid_official_base_sha_is_red(self):
        with self.assertRaisesRegex(ValueError, "current official RC HEAD"):
            admit.prepare(self.base, AUTHOR, self.out, self.receipt, rc_head="not-fixed")

if __name__ == "__main__":
    unittest.main()
