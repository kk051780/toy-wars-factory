"""Original author #523 field-egg geometry source-check and latest RC31 selection QA."""
import os
from pathlib import Path
import sys
import tempfile
import unittest
import json

sys.path.insert(0,str(Path(__file__).resolve().parent))
from select_original523_field_eggs import (
    git_blob,mapping,original_author,prepare,HOST,OWNER523_PATCH_GIT_BLOB
)


class ExistingOriginalFieldEggIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.author=Path(os.environ["GQ523_AUTHOR"]) if os.environ.get("GQ523_AUTHOR") else None
        cls.base=Path(os.environ["GQ523_CANONICAL31"]) if os.environ.get("GQ523_CANONICAL31") else None
        cls.original482=Path(os.environ["GQ523_ORIGINAL482"]) if os.environ.get("GQ523_ORIGINAL482") else None

    def test_git_blob_known_vector(self):
        self.assertEqual(git_blob(b"hello\n"),"ce013625030ba8dba906f756967f9e9ca394464a")

    def test_reject_wrong_original_author_blob(self):
        with tempfile.TemporaryDirectory() as d:
            author=Path(d)/"bad.py";author.write_text("def patch(x):return x")
            with self.assertRaisesRegex(ValueError,"ORIGINAL523_AUTHOR_BLOB_DRIFT"):
                original_author(author)

    def test_noncanonical_script_project_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            project=Path(d)/"p.json";project.write_text(json.dumps({"tree":{"ServerScriptService":{}}}))
            with self.assertRaisesRegex(ValueError,"NOT_ONE_CANONICAL_HOST_IN31"):
                mapping(project)

    def test_reject_inplace_author_base_overwrite(self):
        if not self.author or not self.base:self.skipTest("CI provides pinned original and real V3 31")
        with self.assertRaisesRegex(ValueError,"NONDESTRUCTIVE"):
            prepare(self.base,self.author,self.base)

    def test_original523_pinned_reversible_two_anchors(self):
        if not self.author or not self.original482:self.skipTest("CI provides #523 and #482")
        p=original_author(self.author)
        raw=self.original482.read_text(encoding="utf-8")
        newer=p.patch(raw)
        self.assertEqual(newer.replace(p.ROWS_LINE,"",1).replace(p.REPLACEMENT_LINE,p.ORIGINAL_LINE,1),raw)
        self.assertEqual(newer.count('local eggId="FIELD_"..i'),1)
        self.assertEqual(newer.count("for i=1,24 do"),1)

    def test_patch_fails_closed_if_already_selected(self):
        if not self.author or not self.original482:self.skipTest("CI original pinned")
        p=original_author(self.author)
        once=p.patch(self.original482.read_text(encoding="utf-8"))
        with self.assertRaises(AssertionError):
            p.patch(once)

    def test_preserve_exact_current_host_castle_and_lobby(self):
        if not self.author or not self.base:self.skipTest("CI current exact 31")
        _,original=mapping(self.base)
        before=original[HOST].read_text(encoding="utf-8")
        self.assertIn("coreBoard.MaxDistance=",before)
        self.assertIn("vaultBoard.MaxDistance=",before)
        self.assertIn("local function nearbyBoard(",before)
        self.assertIn("session.refresh=function()",before)
        dest=self.base.parent/"UNIT_GQ523_SELECTED31.project.json"
        prepare(self.base,self.author,dest)
        _,after=mapping(dest)
        chosen=after[HOST].read_text(encoding="utf-8")
        patch=original_author(self.author)
        self.assertEqual(chosen.replace(patch.ROWS_LINE,"",1).replace(patch.REPLACEMENT_LINE,patch.ORIGINAL_LINE,1),before)
        self.assertEqual([k for k in original if original[k].read_bytes()!=after[k].read_bytes()],[HOST])

    def test_idempotent_against_same_original_current31(self):
        if not self.author or not self.base:self.skipTest("CI current exact 31")
        dest=self.base.parent/"UNIT_GQ523_SELECTED31.project.json"
        prepare(self.base,self.author,dest)
        previous=dest.read_bytes()
        prepare(self.base,self.author,dest)
        self.assertEqual(dest.read_bytes(),previous)


if __name__=="__main__":unittest.main()
