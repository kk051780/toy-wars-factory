"""Fault tests for the exact one-source overlay and source-lock boundary."""
from __future__ import annotations
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

DIRECTORY=Path(__file__).resolve().parent
if not (DIRECTORY/'apply_shop_lifecycle.py').is_file():
    DIRECTORY=DIRECTORY.parent/'quality_gameplay/gq805_shop_lifecycle_20261123'
spec=importlib.util.spec_from_file_location('gq805_overlay_under_test',DIRECTORY/'apply_shop_lifecycle.py')
overlay=importlib.util.module_from_spec(spec);spec.loader.exec_module(overlay)

class OverlayBoundary(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock,cls.patch=overlay.load_contract(DIRECTORY)

    def contract_with(self,lock=None,patch=None):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root=Path(temporary.name)
        for name,value in [('source_lock.json',self.lock if lock is None else lock),
                           ('shop_lifecycle_patch.json',self.patch if patch is None else patch)]:
            (root/name).write_text(json.dumps(value,ensure_ascii=False))
        return root

    def test_forward_and_inverse_restore_exact_source(self):
        before=self.patch['before_body'].encode()
        after=overlay.transform(before,self.patch)
        self.assertNotEqual(before,after)
        self.assertEqual(overlay.transform(after,self.patch,True),before)

    def test_stale_parent_source_rejected(self):
        with self.assertRaisesRegex(ValueError,'TRANSFORM_INPUT'):
            overlay.transform(self.patch['before_body'].encode()+b'\n',self.patch)

    def test_altered_candidate_cannot_be_rolled_back_as_exact(self):
        with self.assertRaisesRegex(ValueError,'TRANSFORM_INPUT'):
            overlay.transform(self.patch['after_body'].encode()+b'\n',self.patch,True)

    def test_second_runtime_target_rejected(self):
        patch=deepcopy(self.patch);patch['source']='ServerScriptService/EGGRUMBLE_SwarmCombat.luau'
        with self.assertRaisesRegex(ValueError,'SCOPE'):
            overlay.load_contract(self.contract_with(patch=patch))

    def test_changed_parent_pin_rejected(self):
        lock=deepcopy(self.lock);lock['sources'][overlay.SOURCE]['identity']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'PATCH_BASE_LOCK'):
            overlay.load_contract(self.contract_with(lock=lock))

    def test_changed_candidate_body_rejected(self):
        patch=deepcopy(self.patch);patch['after_body']+='\n'
        with self.assertRaisesRegex(ValueError,'PATCH_IDENTITIES'):
            overlay.load_contract(self.contract_with(patch=patch))

    def test_changed_candidate_pin_rejected(self):
        lock=deepcopy(self.lock);lock['candidate_source']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'PATCH_AFTER_LOCK'):
            overlay.load_contract(self.contract_with(lock=lock))

    def test_seventieth_source_rejected(self):
        lock=deepcopy(self.lock);lock['sources']['SecondShop.client.luau']={}
        with self.assertRaisesRegex(ValueError,'SOURCE_COUNT'):
            overlay.load_contract(self.contract_with(lock=lock))

    def test_boolean_or_float_byte_count_not_integer_evidence(self):
        record=overlay.identity(b'')
        for bad in (False,0.0):
            with self.subTest(bad=repr(bad)):
                record['bytes']=bad
                self.assertFalse(overlay.matches(b'',record))

    def test_duplicate_or_nonfinite_json_rejected(self):
        for raw in ('{"x":1,"x":2}','{"x":NaN}','{"x":Infinity}'):
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                overlay.strict_json(raw)

    def test_drifted_shared_helper_rejected_before_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);path=root/overlay.HELPER
            path.parent.mkdir(parents=True);path.write_text('raise RuntimeError("must not execute")\n')
            with self.assertRaisesRegex(ValueError,'HELPER_DRIFT'):
                overlay.load_helper(root,self.lock)

if __name__=='__main__': unittest.main()
