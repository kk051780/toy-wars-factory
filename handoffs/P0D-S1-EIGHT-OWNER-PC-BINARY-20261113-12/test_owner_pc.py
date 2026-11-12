#!/usr/bin/env python3
"""Actual downloaded 8-safe binary + no-overwrite PC transport negative tests."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
import zipfile
import owner_pc as qa

class RealEightOwnerBinaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        target=os.environ.get("P0D_OWNER_ZIP")
        if not target:
            raise AssertionError("MISSING_REAL_EIGHT_OWNER_BINARY_ZIP_ENV")
        cls.archive=Path(target)
        cls.contents=qa.verify_zip(cls.archive)

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.files=dict(self.contents)
        self.dest=self.root/"pc"
        self.dest.mkdir()

    def modify(self,name,contents,reflect_hash=True):
        self.files[name]=contents
        if reflect_hash and name!=qa.MANIFEST:
            m=json.loads(self.files[qa.MANIFEST])
            m["files"][name]={"sha256":qa.sha(contents),"size":len(contents)}
            self.files[qa.MANIFEST]=(json.dumps(m,sort_keys=True)+"\n").encode()

    def mutate_json(self,name,patch):
        d=json.loads(self.files[name])
        patch(d)
        self.modify(name,(json.dumps(d,ensure_ascii=False,sort_keys=True)+"\n").encode())

    def blocked(self,keyword,callback):
        with self.assertRaises(qa.Blocked) as e:
            callback()
        self.assertIn(keyword,str(e.exception))

    def zippath(self,other=None):
        p=self.root/"mutant.zip"
        with zipfile.ZipFile(p,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for name,data in (other or self.files).items():
                z.writestr(name,data)
        return p

    def test_01_original_unpublished_binary_zip_is_exact(self):
        good=qa.verify_zip(self.archive)
        self.assertEqual(good[qa.PLACE],self.contents[qa.PLACE])
        self.assertEqual(qa.sha(good[qa.PLACE]),qa.ORIGINAL_SHA256)
        self.assertEqual(len(good[qa.PLACE]),159080)

    def test_02_30_studio_checks_remain_not_tested(self):
        d=json.loads(self.files[qa.CASES])
        self.assertEqual(len(d["scenarios"]),30)
        self.assertTrue(all(x["status"]=="NOT_TESTED" for x in d["scenarios"]))
        self.assertFalse(qa.verify_files(self.files)["studio_tested"])

    def test_03_optional_new_isolated_copy_preserves_binary(self):
        receipt=qa.prepare(self.files,self.dest)
        self.assertEqual(receipt["real_roblox_studio"],"NOT_TESTED")
        self.assertEqual((Path(receipt["path"])/qa.PLACE).read_bytes(),self.files[qa.PLACE])

    def test_04_existing_folder_must_never_be_overwritten(self):
        qa.prepare(self.files,self.dest)
        self.blocked("NO_OVERWRITE_TARGET_ALREADY_EXISTS",lambda:qa.prepare(self.files,self.dest))

    def test_05_bad_game_binary_with_forged_manifest_is_blocked(self):
        raw=self.files[qa.PLACE]
        self.modify(qa.PLACE,raw[:100]+b"X"+raw[101:])
        self.blocked("WRONG_GAME_BINARY_SOURCE",lambda:qa.verify_files(self.files))

    def test_06_old_six_game_binary_is_not_accepted(self):
        raw=self.files[qa.PLACE]
        self.modify(qa.PLACE,raw[:200])
        self.blocked("WRONG_GAME_BINARY_SOURCE",lambda:qa.verify_files(self.files))

    def test_07_mismatch_manifest_digest_fails_closed(self):
        self.modify("README.md",self.files["README.md"]+b"\nF",reflect_hash=False)
        self.blocked("BUNDLE_FILE_HASH_MISMATCH",lambda:qa.verify_files(self.files))

    def test_08_fake_studio_pass_in_source_lock_fails(self):
        self.mutate_json(qa.LOCK,lambda x:x.__setitem__("studio_actual_2client_tested",True))
        self.blocked("SOURCE_LOCK_INVALID_OR_FALSE_STUDIO_RESULT",lambda:qa.verify_files(self.files))

    def test_09_wrong_immutable_source_commit_fails(self):
        self.mutate_json(qa.LOCK,lambda x:x.__setitem__("preview_commit","0"*40))
        self.blocked("SOURCE_LOCK_INVALID_OR_FALSE_STUDIO_RESULT",lambda:qa.verify_files(self.files))

    def test_10_forged_studio_pass_in_original_receipt_fails(self):
        self.mutate_json(qa.RECEIPT,lambda x:x.__setitem__("studio_tested",True))
        self.blocked("ORIGINAL_RECEIPT_FALSE_OR_UNPINNED",lambda:qa.verify_files(self.files))

    def test_11_fake_approved_public_release_fails(self):
        self.mutate_json(qa.RECEIPT,lambda x:x.__setitem__("owner_approved_public_release",True))
        self.blocked("ORIGINAL_RECEIPT_FALSE_OR_UNPINNED",lambda:qa.verify_files(self.files))

    def test_12_scenario_spoofed_pass_fails(self):
        self.mutate_json(qa.CASES,lambda x:x["scenarios"][1].__setitem__("status","PASS"))
        self.blocked("FORGED_OR_DUPLICATE_STUDIO_EVIDENCE",lambda:qa.verify_files(self.files))

    def test_13_duplicate_scenario_fails(self):
        self.mutate_json(qa.CASES,lambda x:x["scenarios"][1].__setitem__("id",x["scenarios"][0]["id"]))
        self.blocked("FORGED_OR_DUPLICATE_STUDIO_EVIDENCE",lambda:qa.verify_files(self.files))

    def test_14_evidence_in_pretest_template_forbidden(self):
        self.mutate_json(qa.CASES,lambda x:x["scenarios"][0]["evidence"].append("faked.png"))
        self.blocked("FORGED_OR_DUPLICATE_STUDIO_EVIDENCE",lambda:qa.verify_files(self.files))

    def test_15_missing_one_of_real_30_scenarios_fails(self):
        self.mutate_json(qa.CASES,lambda x:x["scenarios"].pop())
        self.blocked("NOT_EXACTLY_30_STUDIO_CASES",lambda:qa.verify_files(self.files))

    def test_16_relative_parent_path_refused(self):
        self.blocked("EXISTING_ABSOLUTE_DESTINATION_REQUIRED",lambda:qa.prepare(self.files,Path("relative")))

    def test_17_missing_parent_path_refused(self):
        self.blocked("EXISTING_ABSOLUTE_DESTINATION_REQUIRED",lambda:qa.prepare(self.files,self.root/"does-not-exist"))

    def test_18_zip_traversal_extra_entry_rejected(self):
        bad=dict(self.files)
        bad["../escape.txt"]=b"bad"
        self.blocked("ZIP_EXTRA_DUPLICATE_OR_TRAVERSAL_NAME",lambda:qa.verify_zip(self.zippath(bad)))

    def test_19_zip_missing_expected_entry_rejected(self):
        bad=dict(self.files)
        del bad[qa.RECEIPT]
        self.blocked("ZIP_EXTRA_DUPLICATE_OR_TRAVERSAL_NAME",lambda:qa.verify_zip(self.zippath(bad)))

    def test_20_zip_duplicate_member_rejected(self):
        path=self.root/"dupe.zip"
        import warnings
        with zipfile.ZipFile(path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore",UserWarning)
                for key,val in self.files.items():
                    z.writestr(key,val)
                z.writestr(qa.PLACE,self.files[qa.PLACE])
        self.blocked("ZIP_EXTRA_DUPLICATE_OR_TRAVERSAL_NAME",lambda:qa.verify_zip(path))

    def test_21_source_folder_symlink_blocked(self):
        if not hasattr(Path,"symlink_to"): self.skipTest("Symlinks unavailable")
        stage=self.root/"unsafe"
        stage.mkdir()
        for key,raw in self.files.items():
            (stage/key).write_bytes(raw)
        (stage/"README.md").unlink()
        try:
            (stage/"README.md").symlink_to(self.archive)
        except OSError:
            self.skipTest("OS denied symlink")
        self.blocked("BUNDLE_SYMLINK_OR_NOT_FILE",lambda:qa.verify_folder(stage))

    def test_22_destination_symlink_blocked(self):
        if not hasattr(Path,"symlink_to"): self.skipTest("Symlinks unavailable")
        alias=self.root/"alias"
        try:alias.symlink_to(self.dest,target_is_directory=True)
        except OSError:self.skipTest("OS denied symlink")
        self.blocked("DESTINATION_SYMLINK_FORBIDDEN",lambda:qa.prepare(self.files,alias))

    def test_23_default_inspection_is_readonly(self):
        before=set(self.root.rglob("*"))
        self.assertEqual(qa.verify_files(self.files)["status"],"SOURCE_BINARY_VERIFIED_NOT_STUDIO")
        self.assertEqual(set(self.root.rglob("*")),before)

    def test_24_actual_archive_and_flat_copied_bundle_both_verify(self):
        bundle=self.root/"bundle"
        bundle.mkdir()
        for key,value in self.files.items():
            (bundle/key).write_bytes(value)
        self.assertEqual(qa.verify_files(qa.verify_folder(bundle))["files"],len(qa.FILES))
        self.assertEqual(qa.verify_zip(self.archive),self.files)

if __name__=="__main__":
    unittest.main(verbosity=2)
