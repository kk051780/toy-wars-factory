import math
import unittest
from tests.reference import Chaos, Boss, TimeSafety, Progression, classify, level, mastery, STAGES

class ChaosTests(unittest.TestCase):
    def test_full_distribution(self):
        from collections import Counter
        d=Counter(classify(n,'S1')[0] for n in range(100))
        self.assertEqual(d, {'NORMAL':65,'BOSS':25,'WEATHER':10})
    def test_all_weathers(self):
        from collections import Counter
        self.assertEqual(Counter(classify(n,'S1')[1] for n in range(90,100)),{'WX01_METEOR':4,'WX02_SMALL':2,'WX03_CROWN':2,'WX04_GLIDE':1,'WX05_CLOCK':1})
    def test_stage_boss(self):
        for s,name in STAGES.items():self.assertEqual(classify(66,s),('BOSS',name))
    def test_invalid_roll(self):
        for n in (-1,100,1.5,float('nan'),float('inf'),True,'1'):
            with self.subTest(n=n),self.assertRaises(ValueError):classify(n,'S1')
    def test_stage_invalid(self):
        with self.assertRaises(ValueError):classify(12,'S0')
    def test_no_event_before_20(self):
        c=Chaos('m1','S1');self.assertIsNone(c.advance(19,60,roll=65));self.assertFalse(c.decided)
    def test_boss_telegraph_active_cleanup(self):
        c=Chaos('m1','S1');self.assertEqual(c.advance(20,60,roll=65)['event'],'WARNING')
        self.assertEqual(c.advance(23,60)['event'],'ACTIVATE');self.assertEqual(c.advance(40,60)['event'],'CLEANUP');self.assertIsNone(c.advance(41,60))
    def test_no_boss_on_inadequate_time(self):
        c=Chaos('m1','S1');self.assertIsNone(c.advance(45,60,65));self.assertEqual(c.kind,'NORMAL');self.assertTrue(c.decided)
    def test_no_double_event(self):
        c=Chaos('m1','S1');c.advance(20,60,90);self.assertIsNone(c.advance(21,60,95))
    def test_round_cleanup(self):
        c=Chaos('m1','S1');c.advance(20,60,65);self.assertEqual(c.advance(21,60,active=False)['event'],'CLEANUP');self.assertTrue(c.finished)
    def test_time_monotonic(self):
        c=Chaos('m1','S1');c.advance(25,60,10)
        with self.assertRaises(ValueError):c.advance(24,60,10)
    def test_weather_duration(self):
        for roll,secs in [(90,5),(94,7),(96,8),(98,6),(99,6)]:
            with self.subTest(roll=roll):
                c=Chaos('m1','S4');c.advance(20,60,roll);self.assertEqual(c.active_end,22+secs)
    def test_normal_is_quiet(self):
        c=Chaos('m1','S1');self.assertIsNone(c.advance(20,60,roll=20));self.assertEqual(c.kind,'NORMAL')

class BossTests(unittest.TestCase):
    def setUp(self):
        self.b=Boss('m1');self.assertTrue(self.b.spawn('GOROGAN',20)[0]);
        self.p={'matchId':'m1','team':'BLUE','userId':1,'serverRosterConfirmed':True,'alive':True,'hasRelicOrFreeTamerSkill':True,'inNeutralZone':True,'carryingEgg':False}
    def test_boss_once(self):self.assertEqual(self.b.spawn('GOROGAN',25)[1],'SPAWN_REJECTED')
    def test_control_limited(self):
        self.assertTrue(self.b.command(20,1,'BLUE',self.p)[0]);self.assertEqual(self.b.expires,27)
        self.assertEqual(self.b.command(21,2,'RED',dict(self.p,userId=2,team='RED'))[1],'ALREADY_CONTROLLED')
    def test_return_neutral(self):
        self.b.command(20,1,'BLUE',self.p);self.assertEqual(self.b.tick(27)[1],'RETURNED_NEUTRAL');self.assertIsNone(self.b.owner)
    def test_user_once(self):
        self.b.command(20,1,'BLUE',self.p);self.b.tick(27);self.assertEqual(self.b.command(27,1,'BLUE',self.p)[1],'ONE_COMMAND_PER_USER')
    def test_new_user_second(self):
        self.b.command(20,1,'BLUE',self.p);self.b.tick(27)
        self.assertTrue(self.b.command(27,2,'RED',dict(self.p,userId=2,team='RED'))[0])
    def test_wrong_owner(self):self.assertEqual(self.b.command(20,1,'RED',self.p)[1],'SERVER_EVIDENCE_REQUIRED')
    def test_no_roster(self):self.assertEqual(self.b.command(20,1,'BLUE',dict(self.p,serverRosterConfirmed=False))[1],'SERVER_EVIDENCE_REQUIRED')
    def test_carrying_egg(self):self.assertEqual(self.b.command(20,1,'BLUE',dict(self.p,carryingEgg=True))[1],'SERVER_EVIDENCE_REQUIRED')
    def test_missing_relic(self):self.assertEqual(self.b.command(20,1,'BLUE',dict(self.p,hasRelicOrFreeTamerSkill=False))[1],'SERVER_EVIDENCE_REQUIRED')
    def test_away_zone(self):self.assertEqual(self.b.command(20,1,'BLUE',dict(self.p,inNeutralZone=False))[1],'SERVER_EVIDENCE_REQUIRED')
    def test_end_cleanup(self):
        self.b.command(20,1,'BLUE',self.p);self.b.tick(22,active=False);self.assertFalse(self.b.present);self.assertIsNone(self.b.owner)
    def test_time_backwards(self):
        self.b.tick(30);self.assertEqual(self.b.command(29,1,'BLUE',self.p)[1],'TIME_REJECTED')
    def test_no_infinite_control(self):
        self.b.command(20,1,'BLUE',self.p)
        for at in (21,22,23,24,25,26):self.assertEqual(self.b.tick(at)[1],'NO_CHANGE')
        self.assertEqual(self.b.tick(27)[1],'RETURNED_NEUTRAL')

class TimeTests(unittest.TestCase):
    def setUp(self):
        self.t=TimeSafety('m1');self.r={'matchId':'m1','alive':True,'safeFloor':True,'carryingEgg':False};self.p={'matchId':'m1','userId':1,'alive':True,'carryingEgg':False,'activeMatch':True,'serverRosterConfirmed':True}
    def test_rewind_safe(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);self.t.record(3,1,dict(x=4,y=2,z=3),self.r)
        self.assertEqual(self.t.rewind(3.1,1,self.p,lambda p,s:True)[0],dict(x=1,y=2,z=3))
    def test_cannot_rewind_twice(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);self.t.rewind(3,1,self.p,lambda p,s:True)
        self.assertEqual(self.t.rewind(3,1,self.p,lambda p,s:True)[1],'RECALL_BLOCKED')
    def test_egg_carrier_forbidden(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);self.assertEqual(self.t.rewind(3,1,dict(self.p,carryingEgg=True),lambda p,s:True)[1],'RECALL_BLOCKED')
    def test_no_roster(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);self.assertEqual(self.t.rewind(3,1,dict(self.p,serverRosterConfirmed=False),lambda p,s:True)[1],'RECALL_BLOCKED')
    def test_invalid_vector(self):
        self.assertEqual(self.t.record(1,1,dict(x=float('nan'),y=1,z=1),self.r)[1],'POSITION_INVALID')
    def test_out_of_bounds(self):self.assertEqual(self.t.record(1,1,dict(x=10001,y=1,z=1),self.r)[1],'POSITION_INVALID')
    def test_no_validator(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);self.assertEqual(self.t.rewind(3,1,self.p,None)[1],'VALIDATOR_REQUIRED')
    def test_dangerous_destination(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);self.assertEqual(self.t.rewind(3,1,self.p,lambda p,s:False)[1],'NO_SAFE_SNAPSHOT')
    def test_bad_age(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);self.assertEqual(self.t.rewind(7,1,self.p,lambda p,s:True)[1],'NO_SAFE_SNAPSHOT')
    def test_close(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);self.t.close();self.assertEqual(self.t.rewind(3,1,self.p,lambda p,s:True)[1],'TIME_INVALID')
    def test_record_carrier_invalid(self):self.assertEqual(self.t.record(1,1,dict(x=1,y=2,z=3),dict(self.r,carryingEgg=True))[1],'RECORD_BLOCKED')
    def test_dont_restore_hp(self):
        self.t.record(1,1,dict(x=1,y=2,z=3),self.r);q,_=self.t.rewind(3,1,self.p,lambda p,s:True)
        self.assertEqual(set(q),{'x','y','z'})
    def test_samples_bounded(self):
        for i in range(20):self.t.record(i/4,1,dict(x=i,y=0,z=0),self.r)
        self.assertLessEqual(len(self.t.samples[1]),10)

class ProgressionTests(unittest.TestCase):
    def setUp(self):
        self.p=Progression('demo');self.e=dict(matchId='a',scope='demo',userId=1,job='WARRIOR',serverRoundFinalized=True,rosterConfirmed=True,duration=60,activeSeconds=20,meaningfulActionConfirmed=True,won=True,eggDelivered=True,assistTypes={'DEFENSE':True,'ESCORT':True,'SUPPORT':True})
    def test_full_reward(self):
        q,s=self.p.finalize(self.e);self.assertEqual(s,'FINALIZED');self.assertEqual((q['xpAwarded'],q['masteryAwarded']),(104,57))
    def test_loss_reward(self):
        q,_=self.p.finalize(dict(self.e,won=False,eggDelivered=False,assistTypes={}));self.assertEqual(q['xpAwarded'],45)
    def test_afk_zero(self):self.assertEqual(self.p.finalize(dict(self.e,activeSeconds=0))[0]['xpAwarded'],0)
    def test_no_action_zero(self):self.assertEqual(self.p.finalize(dict(self.e,meaningfulActionConfirmed=False))[0]['xpAwarded'],0)
    def test_duplicate(self):
        self.p.finalize(self.e);self.assertEqual(self.p.finalize(self.e)[1],'ALREADY_FINALIZED')
    def test_duplicate_after_zero(self):
        self.p.finalize(dict(self.e,activeSeconds=0));self.assertEqual(self.p.finalize(self.e)[1],'ALREADY_FINALIZED')
    def test_spoofed_scope(self):self.assertEqual(self.p.finalize(dict(self.e,scope='another'))[1],'INVALID_SERVER_EVIDENCE')
    def test_roster_false(self):self.assertEqual(self.p.finalize(dict(self.e,rosterConfirmed=False))[1],'INVALID_SERVER_EVIDENCE')
    def test_match_false(self):self.assertEqual(self.p.finalize(dict(self.e,serverRoundFinalized=False))[1],'INVALID_SERVER_EVIDENCE')
    def test_invalid_job(self):self.assertEqual(self.p.finalize(dict(self.e,job='HACKER'))[1],'INVALID_SERVER_EVIDENCE')
    def test_negative_active(self):self.assertEqual(self.p.finalize(dict(self.e,activeSeconds=-1))[1],'INVALID_SERVER_EVIDENCE')
    def test_active_too_long(self):self.assertEqual(self.p.finalize(dict(self.e,activeSeconds=61))[1],'INVALID_SERVER_EVIDENCE')
    def test_round_cap(self):
        for i in range(512):self.p.finalize(dict(self.e,matchId=f'm{i}'))
        self.assertEqual(self.p.finalize(dict(self.e,matchId='overflow'))[1],'LEDGER_FULL')
    def test_level_thresholds(self):
        self.assertEqual(level(0),1);self.assertEqual(level(39),1);self.assertEqual(level(40),2)
        self.assertEqual(level(9240),25)
    def test_mastery_thresholds(self):
        self.assertEqual([mastery(x) for x in [0,100,250,500,1000,2000]],[0,1,2,3,4,5])
    def test_no_saved_false(self):
        q,_=self.p.finalize(self.e);self.assertFalse(q['saved']);self.assertTrue(q['sessionOnly']);self.assertFalse(q['combatStatsChanged'])
    def test_assists_capped(self):
        q,_=self.p.finalize(dict(self.e,assistTypes=dict(DEFENSE=True,ESCORT=True,SUPPORT=True,FOURTH=True)));self.assertEqual(q['xpAwarded'],104)
    def test_multijob_isolation(self):
        q,_=self.p.finalize(self.e);r,_=self.p.finalize(dict(self.e,matchId='b',job='MAGE'));self.assertEqual(r['jobMastery'],0)
    def test_short_match_threshold(self):
        q,_=self.p.finalize(dict(self.e,duration=10,activeSeconds=3,won=False,eggDelivered=False,assistTypes={}));self.assertEqual(q['xpAwarded'],45)
    def test_invalid_nan(self):self.assertEqual(self.p.finalize(dict(self.e,activeSeconds=float('nan')))[1],'INVALID_SERVER_EVIDENCE')

if __name__=='__main__':unittest.main()
