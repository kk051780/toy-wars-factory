import random
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unittest
from engagement_metrics import sanitize,summarize

def e(i,kind,s='sess',r='round1',origin='studio',t=None):
 return {'event_id':str(i),'session_id':s,'round_id':r,'timestamp':float(i if t is None else t),'origin':origin,'event':kind}

class MetricsTests(unittest.TestCase):
 def test_empty(self):
  x=summarize([], 'studio');self.assertEqual(x['sessions'],0);self.assertIsNone(x['first_round_completion_rate'])
 def test_one_completed(self):
  x=summarize([e(1,'session_start'),e(2,'round_start'),e(3,'round_end')],'studio');self.assertEqual(x['first_round_completion_rate'],1)
 def test_not_started(self):
  x=summarize([e(1,'session_start'),e(2,'round_end')],'studio');self.assertEqual(x['sessions_with_round_end'],0)
 def test_end_before_start(self):
  x=summarize([e(1,'session_start'),e(2,'round_end'),e(3,'round_start')],'studio');self.assertEqual(x['sessions_with_round_end'],0)
 def test_duplicate_id(self):
  self.assertEqual(len(sanitize([e(1,'session_start'),e(1,'session_start')])),1)
 def test_rematch_after_completed(self):
  x=summarize([e(1,'session_start'),e(2,'round_start'),e(3,'round_end'),e(4,'rematch_click')],'studio');self.assertEqual(x['rematch_intent_rate'],1)
 def test_rematch_without_completion(self):
  x=summarize([e(1,'session_start'),e(2,'rematch_click')],'studio');self.assertIsNone(x['rematch_intent_rate'])
 def test_cosmetic_intent(self):
  x=summarize([e(1,'session_start'),e(2,'round_start'),e(3,'round_end'),e(4,'cosmetic_preview_open')],'studio');self.assertEqual(x['cosmetic_preview_rate'],1)
 def test_shop_preview_not_sale(self):
  x=summarize([e(1,'session_start'),e(2,'round_start'),e(3,'round_end'),e(4,'shop_preview_open')],'studio');self.assertEqual(x['Robux_revenue'],'UNKNOWN')
 def test_missing_id(self):
  z=e(1,'session_start');del z['session_id'];self.assertRaises(ValueError,sanitize,[z])
 def test_unauthorized_fields_rejected(self):
  for fld in ['ip_address','userId','email','account_age','platformId','spentRobux']:
   z=e(1,'session_start');z[fld]='secret'
   self.assertRaises(ValueError,sanitize,[z])
 def test_nan_rejected(self):
  z=e(1,'session_start',t=float('nan'));self.assertRaises(ValueError,sanitize,[z])
 def test_inf_rejected(self):
  z=e(1,'session_start',t=float('inf'));self.assertRaises(ValueError,sanitize,[z])
 def test_negative_rejected(self):
  z=e(1,'session_start',t=-1);self.assertRaises(ValueError,sanitize,[z])
 def test_boolean_timestamp_rejected(self):
  z=e(1,'session_start');z['timestamp']=True;self.assertRaises(ValueError,sanitize,[z])
 def test_unknown_type_rejected(self):
  self.assertRaises(ValueError,sanitize,[e(1,'purchase_success')])
 def test_studio_live_separate(self):
  data=[e(1,'session_start'),e(2,'round_start'),e(3,'round_end'),e(1,'session_start',origin='live')]
  self.assertEqual(summarize(data,'live')['sessions_with_round_end'],0)
  self.assertEqual(summarize(data,'studio')['sessions_with_round_end'],1)
 def test_round_dedupe(self):
  data=[e(1,'session_start'),e(2,'round_start'),e(3,'round_end'),e(4,'round_end')]
  self.assertEqual(summarize(data,'studio')['completed_rounds'],1)
 def test_two_sessions(self):
  x=summarize([e(1,'session_start'),e(2,'round_start'),e(3,'round_end'),e(4,'session_start','second'),e(5,'round_start','second')],'studio')
  self.assertEqual(x['first_round_completion_rate'],.5)
 def test_no_cross_round_end(self):
  x=summarize([e(1,'session_start'),e(2,'round_start',r='r1'),e(3,'round_end',r='r2')],'studio')
  self.assertEqual(x['sessions_with_round_end'],0)
 def test_payload_count_same_on_reorder(self):
  data=[e(1,'session_start'),e(2,'round_start'),e(3,'round_end'),e(4,'rematch_click')]
  self.assertEqual(summarize(data,'studio'),summarize(list(reversed(data)),'studio'))
 def test_seeded_random_idempotency(self):
  rng=random.Random(20261110)
  for _ in range(50):
   data=[e(i+1,rng.choice(['session_start','round_start','round_end','rematch_click','shop_preview_open'])) for i in range(30)]
   self.assertEqual(summarize(data+data,'studio'),summarize(data,'studio'))
 def test_rejected_origin(self):
  self.assertRaises(ValueError,summarize,[],'production_claimed')
 def test_no_d1_inferred(self):
  d=summarize([e(1,'session_start')],'studio');self.assertEqual(d['D1_retention'],'UNKNOWN')
 def test_empty_round_name_rejected(self):
  z=e(1,'session_start');z['round_id']='';self.assertRaises(ValueError,sanitize,[z])

if __name__=='__main__':unittest.main()
