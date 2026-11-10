import unittest,math,random
from gorogan_reference import VisualPolicy,packet,valid_pos,valid_id

class PolicyTests(unittest.TestCase):
 def setUp(self):self.p=VisualPolicy()
 def start(self,now=1):return self.p.apply(packet(),now)
 def test_valid_s1(self):self.assertEqual(self.start(),'STARTED')
 def test_s3(self):self.assertEqual(VisualPolicy(stage='S3').apply(packet(stageId='S3'),1),'STARTED')
 def test_other_stage_rejected(self):
  with self.assertRaises(AssertionError):VisualPolicy(stage='S2')
 def test_missing(self):self.assertEqual(self.p.apply(None,1),'REJECTED_PACKET')
 def test_non_table(self):self.assertEqual(self.p.apply('hi',1),'REJECTED_PACKET')
 def test_identity_wrong_round(self):self.assertEqual(self.p.apply(packet(matchId='OTHER'),1),'REJECTED_IDENTITY')
 def test_identity_wrong_boss(self):self.assertEqual(self.p.apply(packet(bossId='DRAGON'),1),'REJECTED_IDENTITY')
 def test_identity_wrong_stage(self):self.assertEqual(self.p.apply(packet(stageId='S3'),1),'REJECTED_IDENTITY')
 def test_identity_invalid_event(self):self.assertEqual(self.p.apply(packet(eventId='../../abc'),1),'REJECTED_IDENTITY')
 def test_identity_invalid_event_type(self):self.assertEqual(self.p.apply(packet(eventId=123),1),'REJECTED_IDENTITY')
 def test_seq_0(self):self.assertEqual(self.p.apply(packet(seq=0),1),'REJECTED_REPLAY')
 def test_seq_float(self):self.assertEqual(self.p.apply(packet(seq=1.5),1),'REJECTED_REPLAY')
 def test_seq_nan(self):self.assertEqual(self.p.apply(packet(seq=math.nan),1),'REJECTED_REPLAY')
 def test_seq_infinite(self):self.assertEqual(self.p.apply(packet(seq=math.inf),1),'REJECTED_REPLAY')
 def test_seq_max(self):self.assertEqual(self.p.apply(packet(seq=1e12),1),'REJECTED_REPLAY')
 def test_invalid_coordinate_nan(self):self.assertEqual(self.p.apply(packet(position={'x':math.nan,'y':0,'z':0}),1),'REJECTED_START')
 def test_invalid_coordinate_far(self):self.assertEqual(self.p.apply(packet(position={'x':2050,'y':0,'z':0}),1),'REJECTED_START')
 def test_invalid_y(self):self.assertEqual(self.p.apply(packet(position={'x':0,'y':900,'z':0}),1),'REJECTED_START')
 def test_invalid_pos_type(self):self.assertEqual(self.p.apply(packet(position='x'),1),'REJECTED_START')
 def test_invalid_pos_bool(self):self.assertEqual(self.p.apply(packet(position={'x':True,'y':0,'z':0}),1),'REJECTED_START')
 def test_success_immutable_copy(self):
  p=packet();self.assertEqual(self.p.apply(p,1),'STARTED');p['position']['x']=900;self.assertEqual(self.p.pos[0],0)
 def test_replay(self):self.start();self.assertEqual(self.p.apply(packet(),2),'REJECTED_REPLAY')
 def test_one_start(self):self.start();self.assertEqual(self.p.apply(packet(seq=2),1.4),'REJECTED_START')
 def test_one_start_after_end(self):
  self.start();self.assertEqual(self.p.apply(packet('END',2),2),'ENDED');self.assertEqual(self.p.apply(packet(seq=3),3),'REJECTED_START')
 def test_warning_clears(self):self.start();self.assertEqual(self.p.expire(3),'STOMP_CLEARED');self.assertEqual(self.p.phase,'ACTIVE')
 def test_valid_stomp(self):self.start();self.assertEqual(self.p.apply(packet('STOMP',2),2),'STOMP_STARTED')
 def test_stomp_replay(self):self.start();self.p.apply(packet('STOMP',2),2);self.assertEqual(self.p.apply(packet('STOMP',2),3),'REJECTED_REPLAY')
 def test_stomp_limit(self):
  self.start();self.assertEqual([self.p.apply(packet('STOMP',i),i) for i in (2,4,6)],['STOMP_STARTED']*3)
  self.assertEqual(self.p.apply(packet('STOMP',7),7),'REJECTED_STOMP_LIMIT')
 def test_stomp_deadline(self):self.start();self.assertEqual(self.p.apply(packet('STOMP',2),14.5),'REJECTED_STOMP_TIME')
 def test_stomp_wrong_event(self):self.start();self.assertEqual(self.p.apply(packet('STOMP',2,eventId='other'),2),'REJECTED_EVENT')
 def test_stomp_clears(self):self.start();self.p.apply(packet('STOMP',2),3);self.assertEqual(self.p.expire(5),'STOMP_CLEARED')
 def test_end(self):self.start();self.assertEqual(self.p.apply(packet('END',2),2),'ENDED');self.assertFalse(self.p.active)
 def test_end_wrong_event(self):self.start();self.assertEqual(self.p.apply(packet('END',2,eventId='other'),2),'REJECTED_EVENT')
 def test_expire(self):self.start();self.assertEqual(self.p.expire(15),'EXPIRED')
 def test_after_expire(self):self.start();self.p.expire(15);self.assertEqual(self.p.apply(packet('STOMP',3),15.2),'REJECTED_EVENT')
 def test_backward_clock(self):self.start(3);self.assertEqual(self.p.apply(packet('END',2),2),'REJECTED_CLOCK')
 def test_nan_clock(self):self.assertEqual(self.p.apply(packet(),math.nan),'REJECTED_CLOCK')
 def test_new_end_unsupported(self):self.start();self.assertEqual(self.p.apply(packet('DELETE',2),2),'REJECTED_KIND')
 def test_future_packet_no_clock(self):self.assertEqual(self.start(1e13),'REJECTED_CLOCK')
 def test_position_boundary_valid(self):self.assertTrue(valid_pos({'x':2048,'y':700,'z':-2048}))
 def test_valid_id_unicode_reject(self):self.assertFalse(valid_id('巨人'))
 def test_cannot_restart_after_expire(self):self.start();self.p.expire(15);self.assertEqual(self.p.apply(packet(seq=2),16),'REJECTED_START')
 def test_4000_fuzz_invariant(self):
  rnd=random.Random(1023)
  p=self.p;now=0
  for k in range(4000):
   now+=rnd.random()*.01
   kind=rnd.choice(('START','STOMP','END','MALFORMED'))
   msg=packet(kind, k+1, eventId=rnd.choice(['boss_1','other']))
   if rnd.random()<.05: msg['position']={'x':rnd.random()*5000,'y':0,'z':0}
   p.apply(msg,now)
   self.assertLessEqual(p.stomp_count,3)
   self.assertLessEqual(p.expires_at,14+now)
   if p.active:self.assertTrue(p.seen_start)
 def test_2_client_local_oracles(self):
  a=VisualPolicy();b=VisualPolicy();msg=packet();self.assertEqual(a.apply(msg,1),b.apply(msg,1))
  self.assertEqual(a.apply(packet('STOMP',2),2),b.apply(packet('STOMP',2),2))
  self.assertEqual(a.pos,b.pos)

if __name__ == '__main__':unittest.main()
