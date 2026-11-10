"""Local data-only regression, NOT Roblox Studio verification."""
import json
import unittest
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / 'design/P0D_D18_HERO72_V8_FINAL12.json').read_text(encoding='utf-8'))
EXPECTED_IDS = {'TRCA-TR-009','TRCA-BE-018','TRCA-SP-027','TRCA-VE-036',
 'TRCA-WE-045','TRCA-ZO-054','TRCA-TR-063','TRCA-BE-072',
 'TRCA-SP-081','TRCA-VE-090','TRCA-WE-099','TRCA-ZO-108'}
class EditorialV8Spec(unittest.TestCase):
 def test_identity(self):
  self.assertEqual(DATA['packet_id'],'P0D-D18-HERO72-FINAL12-20261111-01')
  self.assertEqual(DATA['game_id'],'TRAP_RAIDERS')
  self.assertEqual(DATA['work_id'],'p0d-siege-v19')
 def test_coverage(self):
  cs=DATA['characters']; self.assertEqual(len(cs),12)
  self.assertEqual({c['id'] for c in cs},EXPECTED_IDS)
  self.assertEqual(DATA['hero_editorial_total'],72)
  self.assertEqual(DATA['editorial_total'],78)
 def test_balanced(self):
  self.assertEqual(sorted(Counter(c['category'] for c in DATA['characters']).values()),[2]*6)
  self.assertEqual(len({c['world'] for c in DATA['characters']}),12)
 def test_character_depth(self):
  for c in DATA['characters']:
   with self.subTest(c=c['id']):
    for f in ('silhouette','flaw','keepsake','act1','act2','act3','idle','tap','win','loss','sound','mesh','lod','free','scope'):
     self.assertGreater(len(c[f]),8)
 def test_no_fake_qa(self):
  self.assertEqual(DATA['game_3d'],'NOT_CREATED')
  self.assertEqual(DATA['studio_qa'],'NOT_TESTED')
if __name__=='__main__':unittest.main()
