#!/usr/bin/env python3
"""#388 66->67->68->69 real builder fixture and fail-closed OFF tests."""
from __future__ import annotations
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
ROOT = Path(__file__).resolve().parent

def load(key, path):
    spec=importlib.util.spec_from_file_location(key, ROOT / path)
    assert spec and spec.loader
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

prior = load("fb015_composite_tests_for_motion69","test_fb015_composite.py")
motion = load("fb015_motion69_builder","compose_fb015_art_motion.py")

class Motion69Tests(unittest.TestCase):
    def make_chain(self, root):
        d=prior.fixture(root)
        original=prior.snapshot(d)
        self.assertTrue(prior.slash.apply(d,True))
        scratch68=root/"private68"
        self.assertTrue(prior.combo.compose(d,scratch68,True))
        return d,scratch68,original,prior.snapshot(d),prior.snapshot(scratch68)

    def test_exact_chain_and_compiler_inputs_and_off(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            d,p68,original,real67,real68=self.make_chain(root)
            p69=root/"private69"
            self.assertTrue(motion.compose(p68,p69,True))
            scripts=motion.source_map(p69)
            self.assertEqual(len(scripts),69)
            self.assertEqual(motion.blob(scripts[motion.DEST]),motion.PIN)
            self.assertEqual(prior.snapshot(d),real67)
            self.assertEqual(prior.snapshot(p68),real68)
            original68=motion.source_map(p68)
            for name,raw in original68.items():
                self.assertEqual(scripts[name],raw)
            project=json.loads((p69/"default.project.json").read_text("utf8"))
            self.assertEqual(project["tree"]["StarterPlayer"]["StarterPlayerScripts"]["P0DNeutralMotion"]["$path"],
                             "src/client/P0DNeutralMotion.client.luau")
            lock=json.loads((p69/"SOURCE_LOCK.json").read_text("utf8"))
            feature=json.loads((p69/"RC_FEATURE_LOCK.json").read_text("utf8"))
            self.assertEqual(lock["total_scripts"],69)
            self.assertEqual(feature["total_sources"],69)
            self.assertEqual(lock["blobs"],{p:motion.blob(v) for p,v in scripts.items()})
            self.assertEqual(feature["source_gitblobs"],lock["blobs"])
            self.assertTrue(feature["feature_flags"][motion.FLAG])
            self.assertTrue(motion.compose(p68,p69,False))
            self.assertFalse(p69.exists())
            self.assertEqual(prior.snapshot(p68),real68)
            self.assertTrue(prior.combo.compose(d,p68,False))
            self.assertTrue(prior.slash.apply(d,False))
            self.assertEqual(prior.snapshot(d),original)

    def test_parent_drift_rejected_before_write(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            d,p68,_,_,_=self.make_chain(root)
            (p68/"src/server/ArtMinionSilhouette.server.luau").write_bytes(b"DRIFT")
            p69=root/"private69"
            with self.assertRaisesRegex(RuntimeError,"PRIVATE68_TREE_DRIFT"):
                motion.compose(p68,p69,True)
            self.assertFalse(p69.exists())

    def test_extra_file_does_not_get_deleted_by_off(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            p69=root/"private69"
            motion.compose(p68,p69,True)
            unrelated=p69/"SAVED_NOT_OURS.txt"
            unrelated.write_text("must survive","utf8")
            with self.assertRaisesRegex(RuntimeError,"MOTION69_TREE_DRIFT_NO_REMOVAL"):
                motion.compose(p68,p69,False)
            self.assertEqual(unrelated.read_text("utf8"),"must survive")
            unrelated.unlink()
            self.assertTrue(motion.compose(p68,p69,False))
            self.assertFalse(p69.exists())

    def test_rewritten_self_manifest_cannot_authorize_unrelated_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            import hashlib
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            p69=root/"private69"
            motion.compose(p68,p69,True)
            added=p69/"NOT_OURS.txt"
            added.write_text("owner content","utf8")
            mf=p69/motion.MANIFEST
            record=json.loads(mf.read_text("utf8"))
            record["files"]["NOT_OURS.txt"]=hashlib.sha256(added.read_bytes()).hexdigest()
            mf.write_text(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+"\n","utf8")
            with self.assertRaisesRegex(RuntimeError,"MOTION69_INDEPENDENT_EXPECTED_TREE_DRIFT"):
                motion.compose(p68,p69,False)
            self.assertEqual(added.read_text("utf8"),"owner content")
            self.assertTrue(p69.exists())

    def test_nested_manifest_filename_is_not_ignored(self):
        with tempfile.TemporaryDirectory() as temporary:
            import hashlib
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            p69=root/"private69"
            motion.compose(p68,p69,True)
            nested=p69/"src"/"client"/motion.MANIFEST
            nested.write_text("nested data","utf8")
            mf=p69/motion.MANIFEST
            record=json.loads(mf.read_text("utf8"))
            record["files"][nested.relative_to(p69).as_posix()] = hashlib.sha256(
                nested.read_bytes()).hexdigest()
            mf.write_text(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+"\n","utf8")
            with self.assertRaisesRegex(RuntimeError,"MOTION69_INDEPENDENT_EXPECTED_TREE_DRIFT"):
                motion.compose(p68,p69,False)
            self.assertEqual(nested.read_text("utf8"),"nested data")

    def test_off_no_output_writes_zero_and_parent_stays(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,original68=self.make_chain(root)
            p69=root/"private69"
            self.assertFalse(motion.compose(p68,p69,False))
            self.assertFalse(p69.exists())
            self.assertFalse((root/".private69.motion69_lock").exists(),
                             "No-op OFF must not write a persistent sidecar")
            self.assertEqual(original68,prior.snapshot(p68))

    def test_off_recovery_after_journal_before_rename(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            p69=root/"private69"
            motion.compose(p68,p69,True)
            ticket={"input":str(p68),"output":str(p69),"id":motion.MANIFEST_ID}
            journal=root/"private69.motion69_journal.json"
            journal.write_text(json.dumps(ticket)+"\n","utf8")
            self.assertTrue(motion.compose(p68,p69,False))
            self.assertFalse(p69.exists())
            self.assertFalse(journal.exists())

    def test_off_recovery_after_rename_verifies_tombstone(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            p69=root/"private69"
            motion.compose(p68,p69,True)
            tomb=root/"private69.motion69_removing"
            journal=root/"private69.motion69_journal.json"
            journal.write_text(json.dumps({
                "input":str(p68),"output":str(p69),"id":motion.MANIFEST_ID
            })+"\n","utf8")
            os.rename(p69,tomb)
            unrelated=tomb/"DO_NOT_DELETE.txt"
            unrelated.write_text("user data","utf8")
            with self.assertRaisesRegex(RuntimeError,"MOTION69_PARTIAL_TOMBSTONE_UNRELATED_FILE_REFUSED"):
                motion.compose(p68,p69,False)
            self.assertTrue(tomb.is_dir())
            self.assertEqual(unrelated.read_text("utf8"),"user data")
            unrelated.unlink()
            self.assertTrue(motion.compose(p68,p69,False))
            self.assertFalse(tomb.exists())
            self.assertFalse(journal.exists())

    def test_off_recovery_after_deletion_before_journal_cleanup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,original68=self.make_chain(root)
            p69=root/"private69"
            motion.compose(p68,p69,True)
            journal=root/"private69.motion69_journal.json"
            journal.write_text(json.dumps({
                "input":str(p68),"output":str(p69),"id":motion.MANIFEST_ID
            })+"\n","utf8")
            # Simulate completed verified removal followed by a crash before
            # clearing the journal. OFF must finish without touching parent.
            import shutil
            shutil.rmtree(p69)
            self.assertTrue(motion.compose(p68,p69,False))
            self.assertFalse(journal.exists())
            self.assertEqual(original68,prior.snapshot(p68))

    def test_partial_tombstone_recovery_with_missing_original_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,original68=self.make_chain(root)
            p69=root/"private69"
            motion.compose(p68,p69,True)
            tomb=root/"private69.motion69_removing"
            journal=root/"private69.motion69_journal.json"
            motion.atomic_ticket(journal,{
                "input":str(p68),"output":str(p69),"id":motion.MANIFEST_ID
            })
            os.rename(p69,tomb)
            # Simulate interrupted shutil.rmtree after deleting part of tree.
            (tomb/"src/client/P0DNeutralMotion.client.luau").unlink()
            (tomb/"SOURCE_LOCK.json").unlink()
            self.assertTrue(motion.compose(p68,p69,False))
            self.assertFalse(tomb.exists())
            self.assertFalse(journal.exists())
            self.assertEqual(original68,prior.snapshot(p68))

    def test_partial_tombstone_with_extra_empty_directory_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            p69=root/"private69"
            motion.compose(p68,p69,True)
            tomb=root/"private69.motion69_removing"
            journal=root/"private69.motion69_journal.json"
            motion.atomic_ticket(journal,{
                "input":str(p68),"output":str(p69),"id":motion.MANIFEST_ID
            })
            os.rename(p69,tomb)
            (tomb/"UNRELATED_EMPTY_DIR").mkdir()
            with self.assertRaisesRegex(RuntimeError,"MOTION69_UNEXPECTED_DIRECTORY_REFUSED"):
                motion.compose(p68,p69,False)
            self.assertTrue((tomb/"UNRELATED_EMPTY_DIR").is_dir())

    def test_symlinked_parent_ancestor_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            link=root/"link"
            link.symlink_to(root, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,"SYMLINK_FORBIDDEN"):
                motion.compose(link/"private68",link/"private69",True)
            self.assertFalse((root/"private69").exists())

    def test_parent_and_output_must_share_lock_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            another=root/"another"
            another.mkdir()
            with self.assertRaisesRegex(RuntimeError,"MOTION69_PARENT_LOCK_DOMAIN_MISMATCH"):
                motion.compose(p68,another/"private69",True)
            self.assertFalse((another/"private69").exists())

    def test_symlink_output_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            real=root/"unrelated"
            real.mkdir()
            link=root/"private69"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaisesRegex(RuntimeError,"SYMLINK_FORBIDDEN"):
                motion.compose(p68,link,False)
            self.assertTrue(real.is_dir())

    def test_off_cannot_delete_parent_ancestor(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            _,p68,_,_,_=self.make_chain(root)
            with self.assertRaisesRegex(RuntimeError,"MOTION69_INPUT_OUTPUT_OVERLAP"):
                motion.compose(p68,root,False)
            self.assertTrue(p68.exists())

    def test_manifest_and_motion_security_guards(self):
        self.assertEqual(motion.blob(motion.AUTHOR.read_bytes()),motion.PIN)
        data=motion.AUTHOR.read_text("utf8")
        for token in ("MAX_MODELS = 16","MAX_ACTIVE_COSMETIC_PARTS = 56",
                      "VIEW_RANGE_STUDS = 105","ANIM_STEP = 1 / 25",
                      "P0D_ART_MINION_V1","model.Destroying", "script.Destroying"):
            self.assertIn(token,data)
        for token in ("FireServer(", "TakeDamage(", "OnServerEvent",
                      "Instance.new(\"Part\")", "Instance.new(\"RemoteEvent\")"):
            self.assertNotIn(token,data)

if __name__=="__main__":
    unittest.main()
