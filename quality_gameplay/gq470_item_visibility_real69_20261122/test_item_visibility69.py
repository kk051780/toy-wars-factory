"""GQ470 ART: REAL source nonoverlap + mutation rejection; NOT Studio testing."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from patch_item_visibility69 import (OFFICIAL_HEAD, TARGET, TARGET_FILE, TARGET_SHA,
    FEATURE, START, END, OLD_END, transform, patch_artifact, sha, walk_project)

HERE = Path(__file__).resolve()
DEFAULT_ZIP = Path(__import__('os').environ.get('GQ470_REAL69_ZIP', '/mnt/data/github-actions-artifact-14610422120.zip'))


class TestActualSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(DEFAULT_ZIP) as z:
            cls.source = z.read(TARGET_FILE).decode('utf-8')
            cls.project = json.loads(z.read('EGGRUMBLE_REAL69.project.json'))
            cls.receipt = json.loads(z.read('REAL69_LEGACY_INTAKE_RECEIPT.json'))

    def assert_reject(self, mutated):
        with self.assertRaises(ValueError):
            transform(mutated)

    def test_true_official_source(self):
        self.assertEqual(sha(self.source.encode()), TARGET_SHA)
        self.assertEqual(self.receipt['build_head'], OFFICIAL_HEAD)
        self.assertEqual(len(walk_project(self.project['tree'])), 69)

    def test_real_patch_covers_item_only(self):
        new = transform(self.source)
        self.assertEqual(new.split(START,1)[0], self.source.split(START,1)[0])
        self.assertEqual(new.split(END,1)[1], self.source.split(END,1)[1])
        self.assertEqual(new.count('jewel(trim,item,'), self.source.count('jewel(trim,item,'))
        self.assertEqual(new.count('Instance.new('), self.source.count('Instance.new('))
        self.assertEqual(new.count('task.wait'), self.source.count('task.wait'))
        self.assertIn('transparencyConnection:Disconnect()', new)
        self.assertIn('queryConnection:Disconnect()', new)
        self.assertIn('syncItemArtVisibility()\n item.Destroying', new)
        self.assertEqual(new.count(FEATURE), 1)

    def test_double_apply_rejected(self):
        self.assert_reject(transform(self.source))

    def test_missing_anchor_rejected(self):
        self.assert_reject(self.source.replace(OLD_END, 'end\n'))

    def test_unexpected_visual_budget_rejected(self):
        self.assert_reject(self.source.replace('jewel(trim,item,"WingTip"', 'jewel(trim,item,"WingTip2"'))

    def test_no_studio_fence_rejected(self):
        self.assert_reject(self.source.replace('if not RunService:IsStudio() then return end', ''))

    def test_no_world_cap_rejected(self):
        self.assert_reject(self.source.replace('MAX_DECORATED_ITEMS_PER_WORLD', 'ITEMS_UNLIMITED'))

    def test_no_game_collision_rejected(self):
        self.assert_reject(self.source.replace('p.CanTouch=false', 'p.CanTouch=true'))

    def test_no_item_scope_rejected(self):
        self.assert_reject(self.source.replace('if kind~="HEAL" and kind~="DASH" and kind~="SHIELD" then return end',''))

    def test_actual_zip_all69_lock_and_off_place(self):
        with tempfile.TemporaryDirectory() as temp:
            rep = patch_artifact(DEFAULT_ZIP, Path(temp))
            self.assertEqual(rep['unchanged_sources'], 68)
            self.assertTrue(rep['private_place_is_unmodified_original'])
            self.assertFalse(rep['studio_tested'])
            self.assertEqual((Path(temp) / TARGET_FILE).read_text(), transform(self.source))

    def test_tampered_source_zip_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            altered = Path(temp) / 'bad.zip'
            with zipfile.ZipFile(DEFAULT_ZIP) as src, zipfile.ZipFile(altered, 'w') as dst:
                for name in src.namelist():
                    data = src.read(name)
                    if name == TARGET_FILE:
                        data = data.replace(b'jewel(trim,item,"GroundHalo"', b'jewel(trim,item,"GroundHala"')
                    dst.writestr(name, data)
            with self.assertRaisesRegex(ValueError,'RED_SOURCE_HASH'):
                patch_artifact(altered, Path(temp)/'candidate')

    def test_stale_official_zip_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            altered = Path(temp) / 'stale.zip'
            with zipfile.ZipFile(DEFAULT_ZIP) as src, zipfile.ZipFile(altered, 'w') as dst:
                for name in src.namelist():
                    data = src.read(name)
                    if name == 'REAL69_LEGACY_INTAKE_RECEIPT.json':
                        receipt = json.loads(data)
                        receipt['build_head'] = '0'*40
                        data = json.dumps(receipt).encode()
                    dst.writestr(name, data)
            with self.assertRaisesRegex(ValueError,'RED_OFFICIAL_HEAD'):
                patch_artifact(altered, Path(temp)/'candidate')


if __name__ == '__main__':
    unittest.main()
