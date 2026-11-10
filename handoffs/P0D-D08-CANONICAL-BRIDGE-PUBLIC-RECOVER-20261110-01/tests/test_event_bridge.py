import math,random,unittest
from reference_bridge import BridgeReference,classify,Rejected

class Classification(unittest.TestCase):
    def test_every_roll_accepted(self):
        for s in ('S1','S2','S3','S4'):
            for r in range(100):self.assertIn(classify(r,s)[0],('NORMAL','BOSS','WEATHER'))
    def test_distribution(self):
        got=[classify(i,'S1')[0] for i in range(100)]
        self.assertEqual([got.count(k) for k in ('NORMAL','BOSS','WEATHER')],[65,25,10])
    def test_each_weather(self):
        want=['WX01_METEOR']*4+['WX02_SMALL']*2+['WX03_CROWN']*2+['WX04_GLIDE','WX05_CLOCK']
        self.assertEqual([classify(i,'S1')[1] for i in range(90,100)],want)
    def test_stage_boss_map(self):
        for s,b in [('S1','GOROGAN'),('S2','RAIGALD'),('S3','GOROGAN'),('S4','RAIGALD')]:
            self.assertEqual(classify(65,s),('BOSS',b))
    def test_invalid_stage(self):
        for s in ['S0','S5','',None]:
            with self.subTest(s=s),self.assertRaises(Rejected):classify(66,s)
    def test_invalid_rolls(self):
        for r in [-1,100,None,1.5,True,9999,'3']:
            with self.subTest(r=r),self.assertRaises(Rejected):classify(r,'S1')

class Lifecycle(unittest.TestCase):
    def test_no_event_before_20(self):
        b=BridgeReference();self.assertEqual(b.tick(19.99),'WAIT');self.assertEqual(b.roll_calls,0)
    def test_one_warning_and_one_activation(self):
        b=BridgeReference();self.assertEqual(b.tick(20,66),'WARNING');self.assertEqual(b.tick(20.01),'TELEGRAPH');self.assertEqual(b.tick(22.49),'TELEGRAPH');self.assertEqual(b.tick(22.5),'ACTIVATE');self.assertEqual(b.tick(22.51),'ACTIVE');self.assertEqual(b.warnings,1);self.assertEqual(b.activations,1);self.assertEqual(b.roll_calls,1)
    def test_end_boss_event(self):
        b=BridgeReference();b.tick(20,66);b.tick(22.5);self.assertEqual(b.tick(39.5),'CLEANUP');self.assertEqual(b.history,['WARNING','ACTIVATE','CLEANUP'])
    def test_no_repeat_finished(self):
        b=BridgeReference();b.tick(20,66);b.tick(22.5);b.tick(40);b.tick(42);self.assertEqual(b.cleanup_calls,1)
    def test_normal(self):
        b=BridgeReference();self.assertEqual(b.tick(20,20),'NORMAL');self.assertEqual(b.roll_calls,1);self.assertEqual(b.activations,0)
    def test_tight_round_no_roll(self):
        b=BridgeReference(deadline=38);self.assertEqual(b.tick(20,66),'INSUFFICIENT_TIME');self.assertEqual(b.roll_calls,0)
    def test_warn_enough_time_required(self):
        b=BridgeReference(deadline=39.4);self.assertEqual(b.tick(20,66),'NORMAL_DUE_TIME');self.assertEqual(b.warnings,0)
    def test_alias_s2_default_blocked(self):
        b=BridgeReference(stage='S2');self.assertEqual(b.tick(20,75),'RAIGALD_LIGARDO_ALIAS_REVIEW_REQUIRED');self.assertEqual(b.warnings,0)
    def test_alias_s4_default_blocked(self):
        b=BridgeReference(stage='S4');self.assertEqual(b.tick(20,75),'RAIGALD_LIGARDO_ALIAS_REVIEW_REQUIRED')
    def test_alias_explicit_after_pc_review(self):
        b=BridgeReference(stage='S2',approved_ligardo_alias=True);self.assertEqual(b.tick(20,75),'WARNING');self.assertEqual(b.subtype,'LIGARDO')
    def test_weather_default_blocks(self):
        b=BridgeReference();self.assertEqual(b.tick(20,95),'WEATHER_RUNTIME_MISSING');self.assertEqual(b.warnings,0)
    def test_weather_with_server_handler(self):
        b=BridgeReference(approved_weather=True);self.assertEqual(b.tick(20,95),'WARNING');self.assertEqual(b.tick(22),'ACTIVATE');self.assertEqual(b.tick(29),'CLEANUP')
    def test_weather_meteor_5s(self):
        b=BridgeReference(approved_weather=True);b.tick(20,90);b.tick(22);self.assertEqual(b.tick(27),'CLEANUP')
    def test_weather_clock_6s(self):
        b=BridgeReference(approved_weather=True);b.tick(20,99);b.tick(22);self.assertEqual(b.tick(28),'CLEANUP')
    def test_weather_crown_8s(self):
        b=BridgeReference(approved_weather=True);b.tick(20,96);b.tick(22);self.assertEqual(b.tick(30),'CLEANUP')
    def test_stop_in_warning_cleans(self):
        b=BridgeReference();b.tick(20,65);b.stop();self.assertEqual(b.cleanup_calls,1)
    def test_stop_in_active_cleans(self):
        b=BridgeReference();b.tick(20,66);b.tick(23);b.stop();self.assertEqual(b.cleanup_calls,1)
    def test_stop_before_warning_no_cleanup(self):
        b=BridgeReference();b.stop();self.assertEqual(b.cleanup_calls,0)
    def test_round_close_after_warning(self):
        b=BridgeReference();b.tick(20,65);self.assertEqual(b.tick(21,active=False),'ROUND_FINISHED');self.assertEqual(b.cleanup_calls,1)
    def test_round_close_after_active(self):
        b=BridgeReference();b.tick(20,65);b.tick(23);b.tick(23.2,active=False);self.assertEqual(b.cleanup_calls,1)
    def test_time_reversed_blocks(self):
        b=BridgeReference();b.tick(20,65);self.assertEqual(b.tick(19),'TIME_REVERSED');self.assertEqual(b.cleanup_calls,1)
    def test_match_replaced_blocks(self):
        b=BridgeReference();b.tick(20,65);self.assertEqual(b.tick(21,match_id='other'),'ROUND_REPLACED');self.assertEqual(b.cleanup_calls,1)
    def test_epoch_replaced_blocks(self):
        b=BridgeReference();b.tick(20,65);self.assertEqual(b.tick(21,epoch=2),'ROUND_REPLACED');self.assertEqual(b.cleanup_calls,1)
    def test_stage_replaced_blocks(self):
        b=BridgeReference();b.tick(20,65);self.assertEqual(b.tick(21,stage='S2'),'STAGE_REPLACED');self.assertEqual(b.cleanup_calls,1)
    def test_none_roll_blocks(self):
        b=BridgeReference();self.assertEqual(b.tick(20),'ROLL_UNAVAILABLE')
    def test_invalid_roll_blocks(self):
        for r in [100,-1,True,1.5,float('nan')]:
            b=BridgeReference();self.assertEqual(b.tick(20,r),'ROLL_INVALID')
    def test_one_roll_on_many_updates(self):
        b=BridgeReference();
        for t in range(0,21):b.tick(t,65)
        for t in range(21,41):b.tick(t,65)
        self.assertEqual(b.roll_calls,1)
    def test_fuzz_no_multiple_events(self):
        rng=random.Random(901)
        for trial in range(250):
            b=BridgeReference(stage=rng.choice(['S1','S2','S3','S4']),approved_ligardo_alias=True,approved_weather=True)
            now=0
            for _ in range(150):
                now+=rng.uniform(0,1)
                b.tick(now,rng.randrange(100))
            self.assertLessEqual(b.warnings,1)
            self.assertLessEqual(b.activations,1)
            self.assertLessEqual(b.cleanup_calls,1)
            self.assertLessEqual(b.roll_calls,1)
            self.assertFalse(b.activations and not b.warnings)
    def test_server_event_only_no_client_roll(self):
        b=BridgeReference();self.assertEqual(b.roll_calls,0)

if __name__=='__main__':unittest.main()
