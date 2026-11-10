import copy
import math
import random
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reference'))
from ligardo_model import Ligardo,authorize_lightning


def actor(id='p',x=7,z=0,team='RAIDERS',alive=True,invulnerable=False):
    return {'id':id,'pos':{'x':x,'z':z},'team':team,'alive':alive,'invulnerable':invulnerable}

def round_(stage='S2', roster=None, **kw):
    v={'roundId':'round-1','eventId':'event-1','bossId':'LIGARDO','stage':stage,
       'authorized':True,'running':True,'bossAlive':True,'roster':roster if roster is not None else [actor()]}
    v.update(kw)
    return v

def instance(stage='S2'):
    return Ligardo('round-1','event-1','LIGARDO',stage,{'x':0,'z':0},0)

class CoreTests(unittest.TestCase):
    def test_valid_start_stage(self):
        for st in ('S2','S4'):
            self.assertEqual(instance(st).stage,st)
    def test_invalid_stages(self):
        for st in ('S1','S3','S5',None,7):
            with self.subTest(st=st),self.assertRaises(ValueError):instance(st)
    def test_invalid_ids(self):
        for bad in ('','a b','../evil','a'*65,'☠'):
            with self.subTest(bad=bad),self.assertRaises(ValueError):Ligardo('r','e',bad,'S2',{'x':0,'z':0},0)
    def test_invalid_spawn(self):
        for bad in ({'x':math.nan,'z':0},{'x':math.inf,'z':0},{'x':0},{'x':True,'z':0}):
            with self.subTest(bad=bad),self.assertRaises(ValueError):Ligardo('r','e','b','S2',bad,0)
    def test_first_telegraph_no_damage(self):
        r,e=instance().tick(round_(),1,1)
        self.assertIsNone(e);self.assertEqual([x['kind'] for x in r],['TELEGRAPH'])
    def test_telegraph_waits_two_seconds(self):
        s=instance();s.tick(round_(),1,1)
        self.assertEqual(s.tick(round_(),2.99,2)[0],[])
        self.assertEqual(s.tick(round_(),3,3)[0][0]['kind'],'LIGHTNING_INTENT')
    def test_max_damage_is_intent_not_application(self):
        s=instance();s.tick(round_(),1,1)
        out,_=s.tick(round_(),3,2)
        self.assertEqual(out[0]['damageCap'],7)
        self.assertNotIn('damageApplied',out[0])
    def test_rapid_duplicate_sequence_rejected(self):
        s=instance();s.tick(round_(),1,1)
        self.assertEqual(s.tick(round_(),1,1),( [],'STALE_INPUT'))
        self.assertEqual(s.attempts,1)
    def test_regressed_clock_rejected(self):
        s=instance();s.tick(round_(),2,1)
        self.assertEqual(s.tick(round_(),1.999,2),( [],'STALE_INPUT'))
    def test_noninteger_sequence_rejected(self):
        self.assertEqual(instance().tick(round_(),1,1.5)[1],'STALE_INPUT')
    def test_negative_sequence_rejected(self):
        self.assertEqual(instance().tick(round_(),1,-1)[1],'STALE_INPUT')
    def test_nan_clock_rejected(self):
        self.assertEqual(instance().tick(round_(),math.nan,1)[1],'STALE_INPUT')
    def test_nan_seq_rejected(self):
        self.assertEqual(instance().tick(round_(),1,math.nan)[1],'STALE_INPUT')
    def test_infinite_clock_rejected(self):
        self.assertEqual(instance().tick(round_(),math.inf,1)[1],'STALE_INPUT')
    def test_false_round_id_stops(self):
        s=instance();o,e=s.tick(round_(roundId='other'),1,1)
        self.assertEqual(e,'ROUND_MISMATCH');self.assertEqual(o[0]['kind'],'STOP')
    def test_false_event_id_stops(self):
        s=instance();self.assertEqual(s.tick(round_(eventId='bad'),1,1)[1],'ROUND_MISMATCH')
    def test_false_stage_stops(self):
        s=instance();self.assertEqual(s.tick(round_('S4'),1,1)[1],'ROUND_MISMATCH')
    def test_false_boss_id_stops(self):
        s=instance();self.assertEqual(s.tick(round_(bossId='fake'),1,1)[1],'ROUND_MISMATCH')
    def test_false_authorization_stops(self):
        s=instance();self.assertEqual(s.tick(round_(authorized=False),1,1)[1],'ROUND_MISMATCH')
    def test_false_running_stops(self):
        s=instance();self.assertEqual(s.tick(round_(running=False),1,1)[1],'ROUND_MISMATCH')
    def test_boss_death_stops(self):
        s=instance();a,_=s.tick(round_(bossAlive=False),1,1)
        self.assertEqual(a[0]['why'],'BOSS_DEAD_OR_EXPIRED')
    def test_boss_lifetime_stop(self):
        s=instance();a,_=s.tick(round_(),16,1)
        self.assertEqual(a[0]['kind'],'STOP')
    def test_closed_never_emits_again(self):
        s=instance();s.stop();self.assertEqual(s.tick(round_(),1,1),( [],'CLOSED'))
    def test_empty_roster_safe(self):
        self.assertEqual(instance().tick(round_(roster=[]),1,1)[0],[])
    def test_roster_limit_reject(self):
        self.assertEqual(instance().tick(round_(roster=[actor(str(i)) for i in range(17)]),1,1)[1],'INVALID_ROSTER')
    def test_ally_not_attacked(self):
        self.assertEqual(instance().tick(round_(roster=[actor(team='DEFENDERS')]),1,1)[0],[])
    def test_dead_not_attacked(self):
        self.assertEqual(instance().tick(round_(roster=[actor(alive=False)]),1,1)[0],[])
    def test_invulnerable_not_attacked(self):
        self.assertEqual(instance().tick(round_(roster=[actor(invulnerable=True)]),1,1)[0],[])
    def test_boss_actor_never_attacked(self):
        self.assertEqual(instance().tick(round_(roster=[actor(id='LIGARDO')]),1,1)[0],[])
    def test_far_from_spawn_ignored(self):
        self.assertEqual(instance().tick(round_(roster=[actor(x=56)]),1,1)[0],[])
    def test_nearest_target(self):
        s=instance();r,_=s.tick(round_(roster=[actor('far',10),actor('near',5)]),1,1)
        self.assertEqual(r[0]['targetId'],'near')
    def test_tiebreak_id(self):
        s=instance();r,_=s.tick(round_(roster=[actor('z',7),actor('a',-7)]),1,1)
        self.assertEqual(r[0]['targetId'],'a')
    def test_move_intent_bounded_to_half_second(self):
        s=instance();r,_=s.tick(round_(roster=[actor(x=20)]),10,1)
        self.assertEqual(r[0]['kind'],'MOVE_INTENT');self.assertLessEqual(r[0]['position']['x'],5)
    def test_move_clamped_to_leash(self):
        s=instance();r=round_(roster=[actor(x=54)])
        for i in range(1,13):
            s.tick(r,float(i)*.5,i)
            self.assertLessEqual(math.hypot(s.pos['x'],s.pos['z']),36.0001)
    def test_disappearing_target_drops_attack(self):
        s=instance();s.tick(round_(),1,1)
        a,_=s.tick(round_(roster=[]),3,2)
        self.assertEqual(a,[])
    def test_moved_target_drops_attack(self):
        s=instance();s.tick(round_(),1,1)
        a,_=s.tick(round_(roster=[actor(x=20)]),3,2)
        self.assertEqual(a,[])
    def test_team_change_drops_attack(self):
        s=instance();s.tick(round_(),1,1)
        a,_=s.tick(round_(roster=[actor(team='DEFENDERS')]),3,2)
        self.assertEqual(a,[])
    def test_invulnerability_change_drops_attack(self):
        s=instance();s.tick(round_(),1,1)
        a,_=s.tick(round_(roster=[actor(invulnerable=True)]),3,2)
        self.assertEqual(a,[])
    def test_duplicate_victim_drops_attack(self):
        s=instance();s.tick(round_(),1,1)
        a,_=s.tick(round_(roster=[actor(),actor()]),3,2)
        self.assertEqual(a,[])
    def test_charge_cooldown_is_2_5_s(self):
        s=instance();s.tick(round_(),1,1);s.tick(round_(),3,2)
        self.assertEqual(s.tick(round_(),5.49,3)[0],[])
        self.assertEqual(s.tick(round_(),5.5,4)[0][0]['kind'],'TELEGRAPH')
    def test_no_more_than_3_attempts(self):
        s=instance()
        kinds=[]
        for i in range(1,160):
            a,_=s.tick(round_(),i/10,i)
            kinds.extend(x['kind'] for x in a)
        self.assertLessEqual(kinds.count('TELEGRAPH'),3)
        self.assertLessEqual(kinds.count('LIGHTNING_INTENT'),3)
    def test_randomized_boundedness(self):
        for seed in range(9):
            rng=random.Random(seed);s=instance()
            for i in range(1,120):
                t=round_(roster=[actor(str(j),rng.uniform(-70,70),rng.uniform(-70,70),team=rng.choice(['RAIDERS','DEFENDERS']),alive=rng.choice([True,False])) for j in range(8)])
                out,_=s.tick(t, i/10,i)
                self.assertLessEqual(len(out),1)
                self.assertLessEqual(s.attempts,3)
                self.assertLessEqual(math.hypot(s.pos['x'],s.pos['z']),36.01)
                for event in out:
                    if event['kind']=='LIGHTNING_INTENT':self.assertEqual(event['damageCap'],7)

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.s=instance();self.s.tick(round_(),1,1)
        self.intent=self.s.tick(round_(),3,2)[0][0]
        self.snapshot={**round_(), 'bossPos':{'x':0,'z':0}}
        self.ledger={'roundId':'round-1','eventId':'event-1','consumed':set()}
    def auth(self,los=lambda a,b,c: True):
        return authorize_lightning(self.intent,self.snapshot,los,self.ledger)
    def test_authorized_once(self):
        accepted,data=self.auth();self.assertTrue(accepted);self.assertEqual(data['maxDamage'],7)
        self.assertEqual(self.auth()[1],'REPLAY')
    def test_los_denied(self):
        self.assertEqual(self.auth(lambda a,b,c:False)[1],'LOS_BLOCKED')
        self.assertTrue(self.auth()[0])
    def test_no_los_callback(self):
        self.assertFalse(self.auth(None)[0])
    def test_reject_untrusted_round(self):
        self.snapshot['authorized']=False;self.assertEqual(self.auth()[1],'UNTRUSTED_ROUND')
    def test_reject_old_round(self):
        self.snapshot['roundId']='wrong';self.assertEqual(self.auth()[1],'STALE_ROUND')
    def test_reject_wrong_ledger(self):
        self.ledger['eventId']='wrong';self.assertEqual(self.auth()[1],'LEDGER_REQUIRED')
    def test_reject_no_ledger(self):
        self.ledger=None;self.assertEqual(self.auth()[1],'LEDGER_REQUIRED')
    def test_reject_too_far_boss_pos(self):
        self.snapshot['bossPos']={'x':40,'z':0};self.assertEqual(self.auth()[1],'BOSS_POSITION')
    def test_reject_target_not_alive(self):
        self.snapshot['roster']=[actor(alive=False)];self.assertEqual(self.auth()[1],'INVALID_TARGET')
    def test_reject_target_team(self):
        self.snapshot['roster']=[actor(team='DEFENDERS')];self.assertEqual(self.auth()[1],'INVALID_TARGET')
    def test_reject_target_invuln(self):
        self.snapshot['roster']=[actor(invulnerable=True)];self.assertEqual(self.auth()[1],'INVALID_TARGET')
    def test_reject_target_moved(self):
        self.snapshot['roster']=[actor(x=14)];self.assertEqual(self.auth()[1],'INVALID_TARGET')
    def test_reject_damage_tamper(self):
        self.intent['damageCap']=9000;self.assertEqual(self.auth()[1],'CAP')
    def test_reject_attack_num_tamper(self):
        self.intent['attackNo']=500;self.assertEqual(self.auth()[1],'CAP')
    def test_reject_duplicate_target_in_roster(self):
        self.snapshot['roster']=[actor(),actor()];self.assertEqual(self.auth()[1],'TARGET_COUNT')
    def test_reject_roster_oversize(self):
        self.snapshot['roster']=[actor(str(i)) for i in range(17)];self.assertEqual(self.auth()[1],'ROSTER_OR_LOS')

if __name__=='__main__':unittest.main()
