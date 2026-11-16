"""Original #547 two-board patch: independent fail-closed selective acceptance tests."""
import json
from pathlib import Path
import tempfile
import unittest

import select_original_castle_boards as s


class CastleAndEggBoardRC31(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = s.SOURCE_FILE.read_text(encoding="utf-8")
        cls.changes = s.original_author_changes()
        cls.immediate_host = cls.original.replace(
            "local function prompt(",
            '''local function nearbyBoard(at:BasePart,label:string,maxDistance:number):()
 gui.MaxDistance=math.clamp(maxDistance,16,52)
end
local function prompt(''',
            1,
        )

    def test_pinned_original_author_only_two_insertions(self):
        self.assertEqual(set(self.changes), {"core", "vault"})
        self.assertEqual(s.blob(self.original.encode()), s.ORIGINAL_HOST_BLOB)

    def test_original_author_patch_reconstructed_exactly(self):
        mod = s.importlib.machinery.SourceFileLoader("test_gq547", str(s.AUTHOR_FILE)).load_module()
        reconstructed = self.original
        for line, chunk in self.changes.values():
            reconstructed = reconstructed.replace(line, line + chunk, 1)
        self.assertEqual(reconstructed, mod.patch(self.original))

    def test_only_existing_castle_and_egg_gui_reused(self):
        source = s.patch(self.immediate_host, self.changes)
        self.assertEqual(source.count('Instance.new("BillboardGui")'),
                         self.immediate_host.count('Instance.new("BillboardGui")'))
        self.assertIn("coreBoard.MaxDistance=65", source)
        self.assertIn("vaultBoard.MaxDistance=40", source)
        self.assertIn("coreBoard.AlwaysOnTop=false", source)
        self.assertIn("vaultBoard.AlwaysOnTop=false", source)

    def test_byte_exact_off_after_two_target_changes(self):
        source = s.patch(self.immediate_host, self.changes)
        self.assertEqual(s.undo(source, self.changes), self.immediate_host)

    def test_never_doubles_existing_castle_and_egg_overlay(self):
        with self.assertRaisesRegex(ValueError, "duplicate"):
            s.patch(s.patch(self.immediate_host, self.changes), self.changes)

    def test_broken_original_core_call_rejected(self):
        mutated = self.immediate_host.replace('board(core,(entry.isAI and "AI " or "")',
                                              'board(core,(entry.isAI and "BOT " or "")', 1)
        with self.assertRaisesRegex(ValueError, "core board call drift"):
            s.patch(mutated, self.changes)

    def test_legacy_lobby_visibility_is_required(self):
        with self.assertRaisesRegex(ValueError, "539"):
            s.patch(self.original, self.changes)

    def test_original_castle_refresh_and_egg_reused(self):
        original, after = self.immediate_host, s.patch(self.immediate_host, self.changes)
        for x in ("session.refresh=function()", "c.vaultEggs", "Rules.depositEggs(", "Rules.takeEggs("):
            self.assertEqual(original.count(x), after.count(x))

    def test_synthetic_real31_mapping_changes_only_one_original_host(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            src=root/"source"
            src.mkdir()
            tree={"ServerScriptService":{s.HOST:{"$path":"source/Host.server.luau"}}}
            (src/"Host.server.luau").write_text(self.immediate_host, encoding="utf-8")
            for i in range(30):
                name=f"Other{i}"
                tree["ServerScriptService"][name]={"$path":f"source/{name}.server.luau"}
                (src/f"{name}.server.luau").write_text(f"-- preserved source {i}\n")
            project=root/"initial.project.json"
            project.write_text(json.dumps({"name":"GQ547_Synthetic31","tree":tree}))
            out=root/"output"
            result=s.select(project,out,s.blob(self.immediate_host.encode()))
            self.assertEqual(result["source_count"],31)
            self.assertEqual(result["modified_existing_scripts"],1)
            self.assertEqual(result["unchanged_existing_scripts"],30)
            self.assertTrue(result["roll_back_to_previous_canonical_host_exact"])
            _, previous=s.source_mapping(project)
            _, chosen=s.source_mapping(out/"GQ547_SELECTED31.project.json")
            changed=[k for k in previous if previous[k].read_bytes()!=chosen[k].read_bytes()]
            self.assertEqual(len(changed),1)
            self.assertEqual(changed[0][-1],s.HOST)

    def test_rejects_mismatched_input_host_blob(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/"project.json"
            p.write_text('{"tree":{}}')
            with self.assertRaisesRegex(ValueError, "31-script"):
                s.select(p,Path(tmp)/"out",s.ORIGINAL_HOST_BLOB)


if __name__ == "__main__":
    unittest.main()
