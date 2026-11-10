import math, random, unittest
from tests.reference import Boss,valid_id,valid_pos

def P(x=0,y=0,z=0): return {'x':x,'y':y,'z':z}
def player(name='red',team='RED',x=5,y=0,z=0,alive=True,safe=False):
    return {'playerId':name,'team':team,'position':P(x,y,z),'alive':alive,'inSafeZone':safe}

class BossReferenceTests(unittest.TestCase):
    def setUp(self): self.b=Boss(); self.assertTrue(self.b.start())
    def run_command(self,t,ps=None,**kw):return self.b.tick(t,P(),ps if ps is not None else [player()],**kw)[0]
    def test_first_stomp_warning(self):
        v=self.run_command(2);self.assertEqual(v['kind'],'STOMP_WARNING');self.assertEqual(v['windupEnds'],4)
    def test_stomp_not_early(self):
        self.run_command(2);self.assertIsNone(self.run_command(3.99));self.assertEqual(self.run_command(4)['kind'],'STOMP_RESOLVE')
    def test_no_extra_stomp_same_tick(self):
        self.run_command(2);self.run_command(4);self.assertIsNone(self.run_command(4))
    def test_wait_for_cooldown(self):
        self.run_command(2);self.run_command(4);self.assertIsNone(self.run_command(5.99));self.assertEqual(self.run_command(6)['kind'],'STOMP_WARNING')
    def test_max_three_stomps(self):
        warnings=0
        for t in [2,4,6,8,10,12,13.1]:
            v=self.run_command(t)
            if v and v['kind']=='STOMP_WARNING':warnings+=1
        self.assertLessEqual(warnings,3)
    def test_event_end(self): self.assertEqual(self.run_command(14)['kind'],'END');self.assertIsNone(self.b.active)
    def test_early_stop(self):
        self.assertEqual(self.b.stop('round_1','evt_1')['kind'],'END');self.assertIsNone(self.b.active)
    def test_bad_stop(self):
        self.assertIsNone(self.b.stop('round_1','bad'));self.assertIsNotNone(self.b.active)
    def test_stale_round(self):
        self.assertEqual(self.b.tick(1,P(),[],round_id='other')[1],'STALE_OR_INVALID')
    def test_stale_event(self):
        self.assertEqual(self.b.tick(1,P(),[],event_id='other')[1],'STALE_OR_INVALID')
    def test_clock_rollback(self):
        self.run_command(3);self.assertEqual(self.b.tick(2,P(),[])[1],'STALE_OR_INVALID')
    def test_nan_clock(self):self.assertEqual(self.b.tick(float('nan'),P(),[])[1],'STALE_OR_INVALID')
    def test_invalid_boss_position(self):self.assertEqual(self.b.tick(1,P(float('inf')),[])[1],'STALE_OR_INVALID')
    def test_invalid_roster(self):self.assertEqual(self.b.tick(1,P(),[{'bad':'id'}])[1],'INVALID_ROSTER')
    def test_duplicate_roster_rejected(self):
        p=player();self.assertEqual(self.b.tick(1,P(),[p,p])[1],'INVALID_ROSTER')
    def test_overflow_roster(self):self.assertEqual(self.b.tick(1,P(),[player(str(i)) for i in range(25)])[1],'INVALID_ROSTER')
    def test_ignore_dead(self):self.assertIsNone(self.run_command(1,[player(alive=False)]))
    def test_ignore_safe_spawn(self):self.assertIsNone(self.run_command(1,[player(safe=True)]))
    def test_ignore_other_team(self):self.assertIsNone(self.run_command(1,[player(team='FAKE')]))
    def test_ignore_vertical(self):self.assertIsNone(self.run_command(1,[player(y=30)]))
    def test_ignore_distant(self):self.assertIsNone(self.run_command(1,[player(x=90)]))
    def test_both_teams_equal(self):
        cmd=self.run_command(1,[player('b','BLUE',x=22),player('a','RED',x=22)]);self.assertEqual(cmd['targetId'],'a')
    def test_target_nearest_regardless_team(self):
        self.assertEqual(self.run_command(1,[player('blue','BLUE',30),player('red','RED',12)])['targetId'],'red')
    def test_move_at_most_8(self):
        cmd=self.run_command(1,[player(x=35)]);self.assertLessEqual(abs(cmd['position']['x']),8)
    def test_move_cooldown(self):
        self.run_command(1,[player(x=35)]);self.assertIsNone(self.run_command(1.1,[player(x=35)]))
    def test_leash_return(self):
        cmd=self.b.tick(1,P(50),[])[0];self.assertEqual(cmd['reason'],'LEASH_RETURN');self.assertEqual(cmd['position'],P())
    def test_aggro_limit(self):self.assertIsNone(self.run_command(1,[player(x=46)]))
    def test_immediate_end_disables_attack(self):
        self.run_command(2);self.assertEqual(self.b.tick(2.1,P(),[],active=False)[0]['kind'],'END')
    def test_no_end_resurrection(self):
        self.run_command(14);self.assertEqual(self.b.tick(15,P(),[])[1],'INACTIVE')
    def test_same_round_restart_denied(self):
        self.b.stop('round_1','evt_1');self.assertFalse(self.b.start())
    def test_different_round_restart(self):
        self.b.stop('round_1','evt_1');self.assertTrue(self.b.start(round_id='round_2'))
    def test_seen_round_cap(self):
        self.b.stop('round_1','evt_1')
        for i in range(2,129):
            self.assertTrue(self.b.start(round_id=f'round_{i}'));self.b.stop(f'round_{i}','evt_1')
        self.assertFalse(self.b.start(round_id='round_129'))
    def test_no_target_no_attack(self):
        for t in range(1,13):self.assertIsNone(self.run_command(t,[]))
    def test_poison_unrelated(self):self.assertNotIn('poison',str(vars(self.b)))
    def test_attack_at_fixed_origin(self):
        self.run_command(2,[player(x=5)]);r=self.b.tick(4,P(3),[])[0];self.assertEqual(r['center'],P())
    def test_no_warning_near_expiry(self):
        self.assertIsNone(self.run_command(12.1,[player()]))
    def test_against_rapid_ticks_invariants(self):
        rng=random.Random(442)
        for i in range(3000):
            now= min(13.999,i/250)
            p=player('a' if i%2 else 'b','BLUE' if i%3 else 'RED', x=rng.uniform(-40,40))
            cmd,_=self.b.tick(now,P(),[p]);a=self.b.active
            self.assertLessEqual(a['stomps'],3)
            if cmd and cmd['kind']=='STOMP_RESOLVE': self.assertEqual(cmd['damage'],8)
    def test_no_double_resolve(self):
        self.run_command(2);a=self.run_command(4);b=self.run_command(4.0001)
        self.assertEqual(a['kind'],'STOMP_RESOLVE');self.assertNotEqual((b or {}).get('kind'),'STOMP_RESOLVE')
    def test_only_2_allowed_stages(self):
        b=Boss();self.assertTrue(b.start(stage='S3'));self.assertFalse(Boss().start(stage='S2'))
    def test_bad_kind(self):self.assertFalse(Boss().start(kind='WEATHER'))
    def test_bad_subtype(self):self.assertFalse(Boss().start(subtype='RAIGALD'))
    def test_long_ttl_rejected(self):self.assertFalse(Boss().start(ends_at=15))
    def test_zero_ttl_rejected(self):self.assertFalse(Boss().start(ends_at=0))
    def test_malformed_round(self):self.assertFalse(Boss().start(round_id='../bad'))
    def test_malformed_event(self):self.assertFalse(Boss().start(event_id=''))
    def test_unsafe_origin(self):self.assertFalse(Boss().start(origin=P(float('nan'))))
    def test_no_boss_before_canonical_activate(self):self.assertIsNone(Boss().tick(2,P(),[])[0])

# Parametrized adversarial boundary cases explicitly count as individual tests.
def add_player_variants():
    variants=[(-100,False),(0,True),(8,True),(9,True),(10,True),(45,True),(46,False),(100,False)]
    for j,(dist,eligible) in enumerate(variants):
        def case(self,dist=dist,eligible=eligible):
            b=Boss();b.start();cmd,_=b.tick(2,P(),[player(x=dist)])
            self.assertEqual(cmd is not None,eligible)
        setattr(BossReferenceTests,f'test_distance_variant_{j}',case)
add_player_variants()
if __name__=='__main__':unittest.main()
