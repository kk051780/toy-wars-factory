"""No duplicate gameplay implementation; immutable source selector regression tests."""
import os
from pathlib import Path
import sys
import tempfile
import json
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from select_original_item489 import (
    ITEM_NAME, ITEM_KEY, N, ORIGINAL_ITEM_BLOB, AUTHOR489_ITEM_BLOB,
    author_guard, flatten, git_blob, prepare,
)


class OriginalItem489Selection(unittest.TestCase):
    def test_blob_alg_known_vector(self):
        self.assertEqual(git_blob(b"hello\n"), "ce013625030ba8dba906f756967f9e9ca394464a")

    def test_author_guard_fails_on_unrelated_source(self):
        with self.assertRaisesRegex(ValueError, "blob drift"):
            author_guard(b"-- fake item source\n")

    def test_detects_non_31_scripts(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"project.json"
            p.write_text(json.dumps({"tree":{"ServerScriptService":{}}}))
            with self.assertRaisesRegex(ValueError, "exactly one"):
                flatten(p)

    def test_duplicate_authority_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)
            for i in range(31):
                (base/f"{i}.luau").write_text("return true\n")
            scripts={f"S{i}":{"$path":f"{i}.luau"} for i in range(30)}
            scripts[ITEM_NAME]={"$path":"30.luau"}
            project={"tree":{"ServerScriptService":scripts}}
            p=base/"project.json";p.write_text(json.dumps(project))
            with self.assertRaisesRegex(ValueError, "Duplicate authority"):
                flatten(p)

    def test_only_expected_author_can_replace_original(self):
        root=os.environ.get("GQ_AUTHOR489_ITEM")
        if not root:
            self.skipTest("CI supplies real pinned original author")
        author=Path(root).read_bytes()
        self.assertEqual(git_blob(author), AUTHOR489_ITEM_BLOB)
        author_guard(author)

    def test_actual_original_item_is_obsolete(self):
        root=os.environ.get("GQ_AUTHOR482_ITEM")
        if not root:
            self.skipTest("CI supplies real pinned original author")
        self.assertEqual(git_blob(Path(root).read_bytes()), ORIGINAL_ITEM_BLOB)

    def test_pinned_base31_changes_only_one_item(self):
        base=os.environ.get("GQ_BASE31_PROJECT")
        author=os.environ.get("GQ_AUTHOR489_ITEM")
        if not base or not author:
            self.skipTest("Full canonical V3 composer builds original31 before this test")
        base=Path(base)
        _,existing=flatten(base)
        self.assertEqual(git_blob(existing[ITEM_KEY].read_bytes()), ORIGINAL_ITEM_BLOB)
        out=base.parent/"UNIT_GQ_ITEM489_ON.project.json"
        prepare(base,Path(author),out)
        _,selected=flatten(out)
        self.assertEqual(set(existing),set(selected))
        different=[name for name in existing if existing[name].read_bytes()!=selected[name].read_bytes()]
        self.assertEqual(different,[ITEM_KEY])
        self.assertEqual(len(selected),N)
        self.assertEqual(git_blob(selected[ITEM_KEY].read_bytes()), AUTHOR489_ITEM_BLOB)


if __name__=="__main__":
    unittest.main()
