import random
import unittest
from siege_oracle import Director

def e(i,kind='gate_damage',team='red',r='match-1'):
    return {'id':str(i),'type':kind,'defenderTeam':team,'roundId':r}

def roster():
    return [dict(id='egg',team='red',post='EGG',alive=True,movable=True),
        dict(id='front',team='red',post='FRONT',alive=True,movable=True),
        dict(id='flank',team='red',post='FLANK',alive=True,movable=True),
        dict(id='reserve1',team='red',post='RESERVE',alive=True,movable=True),
        dict(id='reserve2',team='red',post='RESERVE',alive=True,movable=True),
        dict(id='blue1',team='blue',post='RESERVE',alive=True,movable=True)]

class ResponseTests(unittest.TestCase):
    def test_front_reassignment_only_existing_guards(self):
        x=Director('match-1');o=x.step(1,e(1),roster());self.assertEqual(o['status'],'ACCEPTED')
        self.assertEqual([i['guardId'] for i in o['intents']],['reserve1','reserve2'])
        self.assertTrue(all(i['toPost']=='FRONT' for i in o['intents']))
    def test_flank_los_only(self):
        x=Director('match-1');o=x.step(1,e(1,'guard_los'),roster());self.assertEqual(o['mode'],'ALERT')
        self.assertTrue(all(i['toPost']=='FLANK' for i in o['intents']))
    def test_egg_carrier_chase_only_los(self):
        x=Director('match-1');x.step(1,e(1,'egg_picked'),roster());o=x.step(2,e(2,'egg_carrier_los'),roster())
        self.assertEqual(o['mode'],'CHASE')
        self.assertTrue(all(set(i)=={'guardId','fromPost','toPost'} for i in o['intents']))
    def test_duplicate_no_double_retask(self):
        x=Director('match-1');x.step(1,e(1),roster());self.assertEqual(x.step(2,e(1),roster())['status'],'DUPLICATE')
    def test_reject_wrong_round(self):
        x=Director('match-1');self.assertEqual(x.step(1,e(1,r='other'),roster())['status'],'REJECT_EVENT')
    def test_reject_time_rollback(self):
        x=Director('match-1');x.step(10,e(1),roster());self.assertEqual(x.step(8,e(2),roster())['status'],'REJECT_TIME')
    def test_no_egg_guard_move(self):
        x=Director('match-1');out=x.step(1,e(1),roster());self.assertNotIn('egg',[i['guardId'] for i in out['intents']])
    def test_no_enemy_guards_move(self):
        x=Director('match-1');out=x.step(1,e(1),roster());self.assertNotIn('blue1',[i['guardId'] for i in out['intents']])
    def test_outcome_limited_to_two(self):
        x=Director('match-1');g=roster()+[dict(id=f'res{i}',team='red',post='RESERVE',alive=True,movable=True) for i in range(30)]
        self.assertLessEqual(len(x.step(1,e(1),g)['intents']),2)
    def test_no_extra_guards(self):
        x=Director('match-1');self.assertEqual(x.step(1,e(1),roster())['intents'][0]['guardId'],'reserve1')
    def test_egg_drop_resets(self):
        x=Director('match-1');x.step(1,e(1,'egg_picked'),roster());o=x.step(2,e(2,'egg_dropped'),roster());self.assertEqual(o['mode'],'RESET')
    def test_round_end_blocks(self):
        x=Director('match-1');self.assertEqual(x.step(1,e(1,'round_end'),roster())['status'],'ENDED');self.assertEqual(x.step(2,e(2),roster())['status'],'CLOSED')
    def test_flank_minimum(self):
        g=[z for z in roster() if z['post']!='RESERVE'];x=Director('match-1');self.assertEqual(x.step(1,e(1),g)['intents'],[])
    def test_retask_cooldown(self):
        x=Director('match-1');x.step(1,e(1),roster());self.assertEqual(x.step(1.5,e(2),roster())['intents'],[])
    def test_retask_after_cooldown(self):
        x=Director('match-1');x.step(1,e(1),roster());self.assertEqual(len(x.step(3.2,e(2),roster())['intents']),2)
    def test_enemy_team_isolated(self):
        x=Director('match-1');x.step(1,e(1),roster());o=x.step(2,e(2,team='blue'),roster());self.assertEqual(o['intents'],[{'guardId':'blue1','fromPost':'RESERVE','toPost':'FRONT'}])
    def test_invalid_ids(self):
        x=Director('match-1');d=e(1);d['id']='';self.assertEqual(x.step(1,d,roster())['status'],'REJECT_EVENT')
    def test_invalid_action_shape(self):
        x=Director('match-1');v=e(1);v['type']=[]
        self.assertEqual(x.step(1,v,roster())['status'],'REJECT_EVENT')
    def test_infinite_time_rejected(self):
        x=Director('match-1')
        self.assertEqual(x.step(float('inf'),e(1),roster())['status'],'REJECT_TIME')
    def test_nan_and_negative(self):
        x=Director('match-1');self.assertEqual(x.step(float('nan'),e(1),roster())['status'],'REJECT_TIME');self.assertEqual(x.step(-1,e(1),roster())['status'],'REJECT_TIME')
    def test_expiry_not_warp(self):
        x=Director('match-1');x.step(1,e(1),roster());o=x.step(10,e(2),roster());self.assertEqual(o['mode'],'WATCH')
    def test_no_player_position_output(self):
        x=Director('match-1');o=x.step(1,e(1,'egg_picked'),roster());self.assertTrue(all('position' not in i and 'playerId' not in i for i in o['intents']))
    def test_threat_clamped_to_higher(self):
        x=Director('match-1');x.step(1,e(1,'egg_carrier_los'),roster());o=x.step(2,e(2,'gate_damage'),roster());self.assertEqual(o['mode'],'CHASE')
    def test_reject_unknown_action(self):
        x=Director('match-1');self.assertEqual(x.step(1,e(1,'client_claim'),roster())['status'],'REJECT_EVENT')
    def test_long_deterministic_random(self):
        rng=random.Random(2234);events=['gate_damage','guard_los','egg_picked','egg_carrier_los','egg_dropped']
        a=Director('match-1');b=Director('match-1');t=0
        for j in range(400):
            t+=rng.random()*0.5+0.01;v=e(j,rng.choice(events));g=roster()
            self.assertEqual(a.step(t,v,g),b.step(t,v,g))
    def test_random_no_created_id(self):
        rng=random.Random(42);x=Director('match-1');t=0
        for j in range(250):
            t+=0.5;g=roster();r=x.step(t,e(j,rng.choice(list(['gate_damage','guard_los','egg_picked','egg_dropped']))),g)
            self.assertTrue(all(i['guardId'] in {z['id'] for z in g} for i in r['intents']))
    def test_round_id_reject_does_not_advance_clock(self):
        x=Director('match-1');x.step(5,e('bad',r='other'),roster());self.assertEqual(x.last_time,-1)

if __name__=='__main__':unittest.main()
