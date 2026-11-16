"""One-source original #583 RC31 integration tests. No second admission authority."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import select_original_roster583 as s


class OriginalRoster16RC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author, cls.original, cls.chosen = s.load_author()

    def test_exact_two_guard_source_reuse(self):
        self.assertEqual(s.git_blob(self.original.encode("utf-8")),s.ORIGINAL_RULES_BLOB)
        self.assertEqual(self.chosen.count("<=M.MAX_HERO_SLOTS"),2)
        self.assertNotIn("<=32",self.chosen)

    def test_original_author_unchanged_native_harness(self):
        a=self.author
        self.assertIn("canMake17==true",a.native_harness(self.original,True))
        self.assertIn("canMake17==false",a.native_harness(self.chosen,False))
        self.assertIn("canStart17==false",a.native_harness(self.chosen,False))

    def test_rollback_byte_exact_and_no_extra_module(self):
        self.assertEqual(s.undo(self.chosen,self.author),self.original)
        self.assertEqual(self.chosen.count("local M={}"),1)
        self.assertEqual(self.chosen.count("return M"),1)
        self.assertEqual(self.chosen.count("function M."),self.original.count("function M."))

    def test_mutant_old_guard_denied(self):
        mutant=self.original.replace("limit<=32","limit<=31",1)
        with self.assertRaisesRegex(ValueError,"two-hunk"):
            self.author.patch_source(mutant)

    def test_mutant_duplicate_new_guard_denied(self):
        with self.assertRaisesRegex(ValueError,"duplicate exact"):
            s.undo(self.chosen+self.author.NEW[0],self.author)

    def test_source_blob_mismatch_denied(self):
        with self.assertRaisesRegex(ValueError,"source-lock"):
            s.patch_current(self.original,self.author,self.original,"0000000000000000000000000000000000000000")

    def test_synthetic_selected31_changes_only_same_rules_module(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            src=root/"source"
            src.mkdir()
            (src/"OldRules.luau").write_text(self.original,encoding="utf-8")
            tree={"ReplicatedStorage":{s.RULES:{"$path":"source/OldRules.luau"}}}
            for k in range(30):
                name=f"Unchanged{k}"
                (src/f"{name}.luau").write_text(f"-- untouched {k}\n",encoding="utf-8")
                tree["ReplicatedStorage"][name]={"$path":f"source/{name}.luau"}
            manifest=root/"original.project.json"
            manifest.write_text(json.dumps({"name":"synthetic","tree":tree}),encoding="utf-8")
            out=root/"out"
            report=s.select(manifest,out,s.ORIGINAL_RULES_BLOB)
            self.assertEqual(report["script_count"],31)
            self.assertEqual(report["changed_script_count"],1)
            self.assertTrue(report["other_30_byte_exact"])
            self.assertTrue(report["rollback_byte_exact"])
            _,original=s.map_sources(manifest)
            _,selected=s.map_sources(out/"GQ583_SELECTED31.project.json")
            modified=[key for key in original if original[key].read_bytes()!=selected[key].read_bytes()]
            self.assertEqual([key[-1] for key in modified],[s.RULES])

    def test_reject_missing_or_duplicate_rules_slot(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"bad.project.json"
            p.write_text('{"tree":{}}',encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"31 unique"):
                s.map_sources(p)


if __name__=="__main__":
    unittest.main()
