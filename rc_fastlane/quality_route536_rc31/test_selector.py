"""Pin existing original #536 author; prove only original AI route one-hunk in current31."""
import os
from pathlib import Path
import sys
import tempfile
import json
import unittest

sys.path.insert(0, str(Path(__file__).parent))
from select_original536_route import (
    blob,digest,flat,author_module,select,verify,ORIGINAL_ROUTER_BLOB,SOURCE_AUTHOR_BLOB,KEY
)


class Original536Intake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=Path(os.environ["GQ_ROUTE536_AUTHOR"]) if os.environ.get("GQ_ROUTE536_AUTHOR") else None
        cls.router=Path(os.environ["GQ_ROUTE536_ORIGINAL"]) if os.environ.get("GQ_ROUTE536_ORIGINAL") else None
        cls.base=Path(os.environ["GQ_ROUTE536_BASE31"]) if os.environ.get("GQ_ROUTE536_BASE31") else None

    def test_known_git_blob_vector(self):
        self.assertEqual(blob(b"hello\n"),"ce013625030ba8dba906f756967f9e9ca394464a")

    def test_author_blob_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/"source_patch.py";f.write_text("pass")
            with self.assertRaisesRegex(ValueError,"PATCH_AUTHOR_BLOB_DRIFT"):
                author_module(f)

    def test_non31_map_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"x.json";p.write_text(json.dumps({"tree":{"ServerScriptService":{}}}))
            with self.assertRaisesRegex(ValueError,"NOT_CANONICAL31"):
                flat(p)

    def test_pinned_author_source_matches(self):
        if not self.author or not self.router:
            self.skipTest("CI passes immutable original sources")
        self.assertEqual(blob(self.author.read_bytes()),SOURCE_AUTHOR_BLOB)
        self.assertEqual(blob(self.router.read_bytes()),ORIGINAL_ROUTER_BLOB)
        author=author_module(self.author)
        original=self.router.read_bytes()
        patched=author.overlay(original)
        self.assertEqual(patched.replace(author.AFTER.encode(),author.BEFORE.encode(),1),original)
        self.assertNotEqual(patched,original)

    def test_original_negative_mutant_is_rejected(self):
        if not self.author or not self.router:
            self.skipTest("CI passes immutable original sources")
        author=author_module(self.author)
        raw=self.router.read_bytes().replace(author.BEFORE.encode(),b"local ray=nil",1)
        with self.assertRaises(Exception):
            author.overlay(raw)

    def test_on31_other30_exact_source_and_off_rollback(self):
        if not self.author or not self.base:
            self.skipTest("CI provides actual official built31")
        _,original=flat(self.base)
        self.assertEqual(blob(original[KEY].read_bytes()),ORIGINAL_ROUTER_BLOB)
        out=self.base.parent/"UNIT_GQ536_ROUTE_ON.project.json"
        select(self.base,self.author,out)
        _,selected=flat(out)
        self.assertEqual(set(selected),set(original))
        changed=[k for k in original if original[k].read_bytes()!=selected[k].read_bytes()]
        self.assertEqual(changed,[KEY])
        self.assertEqual(len(selected),31)
        self.assertEqual(blob(original[KEY].read_bytes()),ORIGINAL_ROUTER_BLOB)

    def test_reselect_is_idempotent_same_source(self):
        if not self.author or not self.base:
            self.skipTest("CI provides actual official built31")
        out=self.base.parent/"UNIT_GQ536_ROUTE_ON.project.json"
        select(self.base,self.author,out)
        before=out.read_bytes()
        select(self.base,self.author,out)
        self.assertEqual(out.read_bytes(),before)

    def test_refuse_mutating_base_project(self):
        if not self.author or not self.base:
            self.skipTest("CI provides actual official built31")
        with self.assertRaisesRegex(ValueError,"NONDESTRUCTIVE"):
            select(self.base,self.author,self.base)


if __name__=="__main__":
    unittest.main()
