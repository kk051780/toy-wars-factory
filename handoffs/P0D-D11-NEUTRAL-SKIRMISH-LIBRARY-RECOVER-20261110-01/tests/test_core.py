import random
import unittest
from tests.reference import new, step, end_round, hostile, actor


def s1(units=None):
    return new('match-123', units or [{'id':'z', 'kind':'ZOMBIE'}], 0)[0]


def tick(s, from_time, thru_time, a=None, unit='z'):
    events=[]
    for t in range(from_time, thru_time+1):
        s, ev, err = step(s, t, {unit:[a or actor()]})
        assert err is None
        events.extend(ev)
    return s, events

class ValidationTests(unittest.TestCase):
    def test_match_id_empty(self): self.assertIsNone(new('', [{'id':'z','kind':'ZOMBIE'}], 0)[0])
    def test_match_id_long(self): self.assertIsNone(new('a'*97, [{'id':'z','kind':'ZOMBIE'}], 0)[0])
    def test_time_nan(self): self.assertIsNone(new('m', [{'id':'z','kind':'ZOMBIE'}], float('nan'))[0])
    def test_time_inf(self): self.assertIsNone(new('m', [{'id':'z','kind':'ZOMBIE'}], float('inf'))[0])
    def test_zero_units(self): self.assertIsNone(new('m', [], 0)[0])
    def test_three_units(self): self.assertIsNone(new('m', [{'id':str(i),'kind':'BEAST'} for i in range(3)], 0)[0])
    def test_duplicate_units(self): self.assertIsNone(new('m', [{'id':'x','kind':'BEAST'},{'id':'x','kind':'ZOMBIE'}], 0)[0])
    def test_invalid_kind(self): self.assertIsNone(new('m', [{'id':'x','kind':'DRAGON'}], 0)[0])
    def test_order_sorted(self): self.assertEqual(new('m',[{'id':'z','kind':'ZOMBIE'},{'id':'a','kind':'BEAST'}],0)[0]['order'], ['a','z'])
    def test_nonmonotonic_time(self):
        state=s1()
        state,_,_=step(state,2,{})
        self.assertEqual(step(state,1,{})[2], 'REJECTED_STEP')
    def test_rejected_step_preserves(self):
        state=s1()
        after,_,err=step(state,float('nan'),{})
        self.assertIs(after,state);self.assertEqual(err,'REJECTED_STEP')
    def test_bad_observations(self): self.assertEqual(step(s1(),1,None)[2],'REJECTED_STEP')

class CaptureTests(unittest.TestCase):
    def test_exactly_three_seconds(self):
        state=s1();state,ev=tick(state,1,3)
        self.assertEqual(len(ev),1);self.assertEqual(state['units']['z']['faction'],'BLUE')
    def test_two_seconds_insufficient(self):
        state,ev=tick(s1(),1,2);self.assertFalse(ev);self.assertEqual(state['units']['z']['progress'],2)
    def test_no_presence_resets(self):
        state,ev=tick(s1(),1,2)
        state,_,_=step(state,3,{})
        self.assertEqual(state['units']['z']['progress'],0)
    def test_switching_team_resets(self):
        state,_=tick(s1(),1,2)
        state,ev=tick(state,3,4,actor(team='RED'))
        self.assertEqual(ev,[]);self.assertEqual(state['units']['z']['progress'],2)
    def test_contest_resets(self):
        state,_=tick(s1(),1,2)
        state,ev,_=step(state,3,{'z':[actor(),actor('q','RED')]})
        self.assertEqual(state['units']['z']['progress'],0);self.assertEqual(ev,[])
    def test_capture_at_radius(self):
        state,ev=tick(s1(),1,3,actor(distance=14));self.assertEqual(ev[0]['type'],'CAPTURED')
    def test_too_far(self):
        state,ev=tick(s1(),1,3,actor(distance=14.1));self.assertEqual(ev,[])
    def test_negative_distance(self):
        state,ev=tick(s1(),1,3,actor(distance=-1));self.assertEqual(ev,[])
    def test_nan_distance(self):
        state,ev=tick(s1(),1,3,actor(distance=float('nan')));self.assertEqual(ev,[])
    def test_dead_cannot_claim(self):
        state,ev=tick(s1(),1,3,actor(alive=False));self.assertEqual(ev,[])
    def test_no_intent(self):
        state,ev=tick(s1(),1,3,actor(wants=False));self.assertEqual(ev,[])
    def test_egg_carrier_cannot_claim(self):
        state,ev=tick(s1(),1,3,actor(egg=True));self.assertEqual(ev,[])
    def test_invalid_team(self):
        state,ev=tick(s1(),1,3,actor(team='ADMIN'));self.assertEqual(ev,[])
    def test_duplicate_player_id_fail_closed(self):
        state,ev,_=step(s1(),1,{'z':[actor(),actor()]});self.assertEqual(state['units']['z']['progress'],0)
    def test_excess_candidates_fail_closed(self):
        state,ev,_=step(s1(),1,{'z':[actor(str(i)) for i in range(65)]});self.assertEqual(ev,[])
    def test_long_jump_clamped(self):
        state,ev,_=step(s1(),300,{'z':[actor()]});self.assertEqual(state['units']['z']['progress'],1)
    def test_existing_control_not_retriggered(self):
        state,ev=tick(s1(),1,3);state,ev2,_=step(state,4,{'z':[actor()]});self.assertEqual(ev2,[])
    def test_expiry(self):
        state,_=tick(s1(),1,3);state,ev,_=step(state,11,{})
        self.assertEqual(ev[0]['type'],'EXPIRED');self.assertEqual(state['units']['z']['faction'],'NEUTRAL')
    def test_rearm_cooldown(self):
        state,_=tick(s1(),1,3);state,_,_=step(state,11,{})
        for t in [12,13,14]:
            state,ev,_=step(state,t,{'z':[actor()]});self.assertEqual(ev,[])
        state,_,_=step(state,15,{'z':[actor()]});self.assertEqual(state['units']['z']['progress'],1)
    def test_expiry_no_immediate_claim(self):
        state,_=tick(s1(),1,3);state,ev,_=step(state,11,{'z':[actor()]})
        self.assertEqual(len(ev),1);self.assertEqual(state['units']['z']['progress'],0)
    def test_per_team_cap(self):
        state=s1([{'id':'a','kind':'ZOMBIE'},{'id':'b','kind':'BEAST'}]);ev=[]
        for t in range(1,4): state,e,_=step(state,t,{'a':[actor('p')],'b':[actor('q')]});ev+=e
        self.assertEqual(len(ev),1);self.assertEqual(state['units']['b']['faction'],'NEUTRAL')
    def test_two_teams_control_two_units(self):
        state=s1([{'id':'a','kind':'ZOMBIE'},{'id':'b','kind':'BEAST'}]);ev=[]
        for t in range(1,4): state,e,_=step(state,t,{'a':[actor('p')],'b':[actor('q','RED')]});ev+=e
        self.assertEqual(len(ev),2);self.assertEqual(state['units']['a']['faction'],'BLUE');self.assertEqual(state['units']['b']['faction'],'RED')
    def test_snapshot_immutable(self):
        state=s1();initial=state.copy();newstate,ev,_=step(state,1,{'z':[actor()]})
        self.assertEqual(state['units']['z']['progress'],0);self.assertEqual(newstate['units']['z']['progress'],1)
    def test_end_round_neutralizes(self):
        state,_=tick(s1(),1,3);state,_,_=end_round(state,4)
        self.assertTrue(state['closed']);self.assertEqual(state['units']['z']['faction'],'NEUTRAL')
    def test_end_round_rejects_rollback(self):
        state,_=tick(s1(),1,2);self.assertEqual(end_round(state,1)[2],'REJECTED_END')
    def test_closed_rejects_step(self):
        state,_,_=end_round(s1(),1);self.assertEqual(step(state,2,{})[2],'REJECTED_STEP')

class HostilityTests(unittest.TestCase):
    def test_neutral_zombie_beast_fight(self): self.assertTrue(hostile('NEUTRAL','NEUTRAL','ZOMBIE','BEAST'))
    def test_neutral_same_kind_peace(self): self.assertFalse(hostile('NEUTRAL','NEUTRAL','ZOMBIE','ZOMBIE'))
    def test_owned_same_team_peace(self): self.assertFalse(hostile('BLUE','BLUE'))
    def test_owned_opposing_fight(self): self.assertTrue(hostile('BLUE','RED'))
    def test_neutral_attacks_teams(self): self.assertTrue(hostile('NEUTRAL','BLUE'))
    def test_teams_attack_neutral(self): self.assertTrue(hostile('RED','NEUTRAL'))
    def test_bad_faction_fails_closed(self): self.assertFalse(hostile('ADMIN','BLUE'))

class RandomizedTests(unittest.TestCase):
    def test_seeded_invariants_and_no_double_claim(self):
        rng=random.Random(43001)
        state=s1([{'id':'a','kind':'ZOMBIE'},{'id':'b','kind':'BEAST'}]);at=0
        for _ in range(1500):
            at+=rng.choice([0.1,0.2,0.5,1,3])
            obs={}
            for uid in ('a','b'):
                obs[uid]=[actor(str(rng.randrange(10)),rng.choice(['BLUE','RED']),rng.uniform(0,20),
                                rng.random()>.15, rng.random()>.3, rng.random()<.15)]
                if rng.random()<.16:
                    obs[uid].append(actor(str(rng.randrange(10)),rng.choice(['BLUE','RED'])))
            state,events,err=step(state,at,obs)
            self.assertIsNone(err)
            counts={'BLUE':0,'RED':0}
            for unit in state['units'].values():
                self.assertIn(unit['faction'],['NEUTRAL','BLUE','RED'])
                self.assertGreaterEqual(unit['progress'],0)
                self.assertLessEqual(unit['progress'],3)
                if unit['faction'] in counts: counts[unit['faction']]+=1
            self.assertLessEqual(counts['BLUE'],1);self.assertLessEqual(counts['RED'],1)

if __name__=='__main__': unittest.main()
