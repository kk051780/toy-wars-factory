"""GQ539 selector tests; synthetic 31-file manifest is NOT a real Rojo/Studio proof."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import select_original_host as select

SRC = (HERE.parents[2] / "handoffs/P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
       / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")


class TestOriginalSourceSelection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = select.undo(SRC)

    def test_original_blob_exact_and_reversible(self):
        self.assertEqual(select.git_blob(self.original.encode("utf-8")), select.ORIGINAL_HOST_BLOB)
        self.assertEqual(select.patch(self.original), SRC)

    def test_original_board_and_core_vault_still_owned_by_547(self):
        self.assertEqual(self.original.count(select.BOARD_FACTORY), 1)
        self.assertEqual(SRC.count(select.BOARD_FACTORY), 1)
        self.assertIn('board(vault,"卵倉庫")', SRC)
        self.assertIn('board(core,(entry.isAI and "AI " or "")', SRC)

    def test_injection_is_idempotence_red_not_silent_duplicate(self):
        with self.assertRaisesRegex(ValueError, "duplicate GQ539"):
            select.patch(SRC)

    def test_original_anchor_mutation_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "anchor changed"):
            select.patch(self.original.replace('board(stand,data.name..', 'board(stand,"changed"..', 1))

    def test_cannot_overwrite_original_board_factory(self):
        with self.assertRaisesRegex(ValueError, "board factory changed"):
            select.patch(self.original.replace('b.AlwaysOnTop=true', 'b.AlwaysOnTop=false', 1))

    def test_allows_author_owned_castle_patch_after_existing_call(self):
        castle_patch = '\n local coreBoard=core:FindFirstChildOfClass("BillboardGui")\n if coreBoard then coreBoard.MaxDistance=65 end'
        anchor = 'session.castleModels[entry.id]'
        overlaid = self.original.replace(' '+anchor, castle_patch+'\n '+anchor, 1)
        self.assertEqual(select.undo(select.patch(overlaid)), overlaid)
        self.assertIn("coreBoard.MaxDistance=65", select.patch(overlaid))

    def test_synthetic_31_source_manifest_overlay_only_host(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sources = root / "sources"
            sources.mkdir()
            (sources / "Host.server.luau").write_text(self.original, encoding="utf-8")
            tree = {"ServerScriptService": {
                select.HOST: {"$path": "sources/Host.server.luau"}
            }}
            for i in range(30):
                p = sources / f"Other{i}.server.luau"
                p.write_text(f"-- original test author {i}\n", encoding="utf-8")
                tree["ServerScriptService"][f"Author{i}"] = {"$path": f"sources/Other{i}.server.luau"}
            project = root / "source.project.json"
            project.write_text(json.dumps({"name":"GQ539 synthetic", "tree":tree}), encoding="utf-8")
            output = root / "out"
            receipt = select.generate(project, output, select.ORIGINAL_HOST_BLOB, 31)
            self.assertEqual(receipt["script_count"],31)
            self.assertEqual(receipt["modified_source_count"],1)
            self.assertEqual(receipt["untouched_source_count"],30)
            self.assertTrue(receipt["rollback_byte_exact"])
            produced = json.loads((output / "GQ539_SELECTED31.project.json").read_text())
            actual_map = select.mapped(produced)
            self.assertEqual(len(actual_map),31)
            for key, entry in actual_map.items():
                p = (output / entry["$path"]).resolve()
                self.assertTrue(p.is_file())
                if key[-1] != select.HOST:
                    self.assertEqual(p.read_text(), (sources / f"{key[-1].replace('Author','Other')}.server.luau").read_text())

    def test_rejects_unexpected_script_count(self):
        with self.assertRaisesRegex(ValueError, "31-source"):
            select.generate(Path("/dev/null"),Path("/tmp/nowhere"),select.ORIGINAL_HOST_BLOB,30)


if __name__ == "__main__":
    unittest.main()
