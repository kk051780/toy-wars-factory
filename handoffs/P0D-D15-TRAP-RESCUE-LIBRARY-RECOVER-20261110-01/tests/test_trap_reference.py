import sys
import unittest
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference import TrapState, MAX_ROSTER, TICKS, DAMAGE, COOLDOWN, IMMUNITY


def game():
    g=TrapState('S1:match:123')
    assert g.sync(11,'BLUE','TRAPPER',True,0,0)[0]
    assert g.sync(22,'RED','WARRIOR',True,8,0)[0]
    assert g.sync(33,'RED','MAGE',True,8,2)[0]
    assert g.sync(44,'BLUE','WARRIOR',True,8,1)[0]
    return g


class TestCasting(unittest.TestCase):
    def test_basic_cast(self):
        g=game();self.assertEqual(g.cast(11,22),(True,'TRAPPED'))
    def test_status_rooted(self):
        g=game();g.cast(11,22);self.assertTrue(g.status(22)['rooted'])
    def test_status_poison(self):
        g=game();g.cast(11,22);self.assertTrue(g.status(22)['poison'])
    def test_non_trapper(self):
        g=game();self.assertEqual(g.cast(44,22)[1],'WRONG_JOB')
    def test_friend(self):
        g=game();self.assertEqual(g.cast(11,44)[1],'FRIENDLY_FIRE')
    def test_self(self):
        g=game();self.assertEqual(g.cast(11,11)[1],'BAD_IDS')
    def test_missing(self):
        g=game();self.assertEqual(g.cast(11,999)[1],'NO_LIVE_PLAYER')
    def test_dead_caster(self):
        g=game();g.sync(11,'BLUE','TRAPPER',False,0,0);self.assertEqual(g.cast(11,22)[1],'NO_LIVE_PLAYER')
    def test_dead_target(self):
        g=game();g.sync(22,'RED','WARRIOR',False,8,0);self.assertEqual(g.cast(11,22)[1],'NO_LIVE_PLAYER')
    def test_at_range_boundary(self):
        g=game();g.sync(22,'RED','WARRIOR',True,16,0);self.assertTrue(g.cast(11,22)[0])
    def test_outside_range(self):
        g=game();g.sync(22,'RED','WARRIOR',True,16.01,0);self.assertEqual(g.cast(11,22)[1],'OUT_OF_RANGE')
    def test_cooldown_after_cast(self):
        g=game();g.cast(11,22);self.assertEqual(g.cast(11,33)[1],'COOLDOWN')
    def test_owner_limit_after_cooldown(self):
        g=game();g.cast(11,22);g.advance(12);self.assertTrue(g.cast(11,33)[0])
    def test_simultaneous_caster_rejected(self):
        g=game();g.sync(55,'BLUE','TRAPPER',True,3,0);g.cast(11,22);self.assertEqual(g.cast(55,22)[1],'ALREADY_TRAPPED')
    def test_own_expired_immunity(self):
        g=game();g.sync(55,'BLUE','TRAPPER',True,3,0);g.cast(11,22);g.advance(3);self.assertEqual(g.cast(55,22)[1],'TARGET_IMMUNE');g.advance(12);self.assertTrue(g.cast(55,22)[0])
    def test_two_trappers_cannot_chain(self):
        g=game();g.sync(55,'BLUE','TRAPPER',True,3,0);g.cast(11,22);g.advance(3);self.assertEqual(g.cast(55,22)[1],'TARGET_IMMUNE')
    def test_bool_ids_rejected(self):
        g=game();self.assertEqual(g.cast(True,22)[1],'BAD_IDS')
    def test_float_ids_rejected(self):
        g=game();self.assertEqual(g.cast(11.2,22)[1],'BAD_IDS')


class TestRescue(unittest.TestCase):
    def test_rescue_too_early(self):
        g=game();g.cast(11,22);self.assertEqual(g.rescue(33,22)[1],'RESCUE_TOO_EARLY')
    def test_rescue_success(self):
        g=game();g.cast(11,22);g.advance(.5);self.assertEqual(g.rescue(33,22),(True,'RESCUED'));self.assertFalse(g.status(22)['trapped'])
    def test_rescue_again_rejected(self):
        g=game();g.cast(11,22);g.advance(.5);g.rescue(33,22);self.assertEqual(g.rescue(33,22)[1],'NOT_TRAPPED')
    def test_enemy_cannot_rescue(self):
        g=game();g.cast(11,22);g.advance(.5);self.assertEqual(g.rescue(44,22)[1],'NOT_ALLY')
    def test_rescuer_dead(self):
        g=game();g.cast(11,22);g.advance(.5);g.sync(33,'RED','MAGE',False,8,2);self.assertEqual(g.rescue(33,22)[1],'NO_LIVE_PLAYER')
    def test_rescue_range(self):
        g=game();g.cast(11,22);g.advance(.5);g.sync(33,'RED','MAGE',True,19,0);self.assertEqual(g.rescue(33,22)[1],'OUT_OF_RANGE')
    def test_rescue_range_boundary(self):
        g=game();g.cast(11,22);g.advance(.5);g.sync(33,'RED','MAGE',True,18,0);self.assertTrue(g.rescue(33,22)[0])
    def test_rescue_grants_immunity(self):
        g=game();g.cast(11,22);g.advance(.5);g.rescue(33,22);self.assertAlmostEqual(g.status(22)['immunityRemaining'],6)
    def test_rescue_preserves_other(self):
        g=game();g.sync(55,'BLUE','TRAPPER',True,4,0);g.cast(11,22);g.cast(55,33);g.advance(.5);g.rescue(33,22);self.assertTrue(g.status(33)['trapped'])
    def test_solo_escape_before(self):
        g=game();g.cast(11,22);g.advance(1.24);self.assertEqual(g.escape(22)[1],'ESCAPE_TOO_EARLY')
    def test_solo_escape_exact(self):
        g=game();g.cast(11,22);g.advance(1.25);self.assertEqual(g.escape(22),(True,'ESCAPED'))
    def test_solo_escape_again(self):
        g=game();g.cast(11,22);g.advance(1.25);g.escape(22);self.assertEqual(g.escape(22)[1],'NOT_TRAPPED')
    def test_cannot_escape_for_other_with_remote_if_server_wires_identity(self):
        g=game();g.cast(11,22);g.advance(1.25)
        self.assertTrue(g.escape(22)[0])
        # caller MUST resolve targetId from authenticated Player/UserId, never remote payload
    def test_cast_cooldown_not_refunded_by_rescue(self):
        g=game();g.cast(11,22);g.advance(.5);g.rescue(33,22);self.assertEqual(g.cast(11,33)[1],'COOLDOWN')


class TestClockAndPoison(unittest.TestCase):
    def test_one_tick(self):
        g=game();g.cast(11,22);self.assertEqual(len(g.advance(1)[2]),1)
    def test_three_ticks_total(self):
        g=game();g.cast(11,22);e=g.advance(3)[2];self.assertEqual([z['tick'] for z in e],[1,2,3]);self.assertEqual(sum(z['damage'] for z in e),9)
    def test_no_double_tick(self):
        g=game();g.cast(11,22);g.advance(1);self.assertEqual(g.advance(1)[2],[])
    def test_stalled_clock_max_three(self):
        g=game();g.cast(11,22);self.assertEqual(len(g.advance(20)[2]),3)
    def test_clock_reversal_rejected(self):
        g=game();g.advance(2);self.assertFalse(g.advance(1)[0])
    def test_clock_nan_rejected(self):
        g=game();self.assertEqual(g.advance(float('nan'))[1],'BAD_CLOCK')
    def test_clock_infinity_rejected(self):
        g=game();self.assertEqual(g.advance(float('inf'))[1],'BAD_CLOCK')
    def test_clock_bool_rejected(self):
        g=game();self.assertEqual(g.advance(True)[1],'BAD_CLOCK')
    def test_max_clock_rejected(self):
        g=game();self.assertEqual(g.advance(3600.1)[1],'BAD_CLOCK')
    def test_root_ends_before_poison(self):
        g=game();g.cast(11,22);g.advance(2.1);self.assertFalse(g.status(22)['rooted']);self.assertTrue(g.status(22)['poison'])
    def test_rescue_cancels_future_poison(self):
        g=game();g.cast(11,22);g.advance(.5);g.rescue(33,22);self.assertEqual(g.advance(3)[2],[])
    def test_escape_cancels_future_poison(self):
        g=game();g.cast(11,22);g.advance(1.25);g.escape(22);self.assertEqual(g.advance(3)[2],[])
    def test_advance_before_rescue_due_damage_applied(self):
        g=game();g.cast(11,22);due=g.advance(1)[2];g.rescue(33,22);self.assertEqual(len(due),1)
    def test_eggs_not_stored_or_mutated(self):
        g=game();g.cast(11,22);g.advance(1.5);self.assertFalse(any('egg' in k.lower() or 'score' in k.lower() for k in vars(g)))


class TestLifecycle(unittest.TestCase):
    def test_target_death_clears(self):
        g=game();g.cast(11,22);g.sync(22,'RED','WARRIOR',False,8,0);self.assertFalse(g.status(22)['trapped'])
    def test_caster_death_clears(self):
        g=game();g.cast(11,22);g.sync(11,'BLUE','TRAPPER',False,0,0);self.assertFalse(g.status(22)['trapped'])
    def test_disconnect_clears(self):
        g=game();g.cast(11,22);g.remove(22);self.assertFalse(g.status(22)['trapped'])
    def test_caster_disconnect_clears(self):
        g=game();g.cast(11,22);g.remove(11);self.assertFalse(g.status(22)['trapped'])
    def test_team_switch_clears(self):
        g=game();g.cast(11,22);g.sync(22,'BLUE','WARRIOR',True,8,0);self.assertFalse(g.status(22)['trapped'])
    def test_job_change_clears_trap(self):
        g=game();g.cast(11,22);g.sync(11,'BLUE','MAGE',True,0,0);self.assertFalse(g.status(22)['trapped'])
    def test_closed_rejects_actions(self):
        g=game();g.cast(11,22);g.end_match();self.assertEqual(g.cast(11,22)[1],'MATCH_CLOSED');self.assertEqual(g.advance(3)[1],'MATCH_CLOSED')
    def test_end_clears_all(self):
        g=game();g.cast(11,22);g.end_match();self.assertEqual(len(g.effects),0);self.assertEqual(len(g.roster),0)
    def test_bad_team(self):
        g=game();self.assertEqual(g.sync(77,'GREEN','TRAPPER',True,0,0)[1],'BAD_SERVER_ROSTER')
    def test_bad_coord(self):
        g=game();self.assertEqual(g.sync(77,'RED','TRAPPER',True,float('nan'),0)[1],'BAD_SERVER_ROSTER')
    def test_roster_full(self):
        g=game()
        for i in range(100,100+MAX_ROSTER-4):self.assertTrue(g.sync(i,'RED','MAGE',True,0,0)[0])
        self.assertEqual(g.sync(999,'RED','MAGE',True,0,0)[1],'ROSTER_FULL')
    def test_update_full_roster(self):
        g=game()
        for i in range(100,100+MAX_ROSTER-4):g.sync(i,'RED','MAGE',True,0,0)
        self.assertTrue(g.sync(11,'BLUE','TRAPPER',True,2,0)[0])
    def test_unregistered_removal(self):
        g=game();g.remove(999);self.assertTrue(g.sync(88,'RED','MAGE',True,0,0)[0])
    def test_match_invalid(self):
        with self.assertRaises(ValueError):TrapState('')


class TestProperties(unittest.TestCase):
    def test_seeded_random_sequence_bounded_damage_and_no_repeat(self):
        rnd=random.Random(5481)
        g=game();g.sync(55,'BLUE','TRAPPER',True,2,0)
        seen=set();total={}
        now=0.
        for _ in range(500):
            now+=rnd.random()*.12
            ok,_,events=g.advance(now)
            self.assertTrue(ok)
            for e in events:
                key=(e['targetId'],e['casterId'],e['tick'],g.next_cast_at.get(e['casterId']))
                self.assertNotIn(key,seen);seen.add(key)
                self.assertLessEqual(e['damage'],DAMAGE)
            action=rnd.randrange(6)
            if action==0:g.cast(rnd.choice([11,55]),rnd.choice([22,33]))
            elif action==1:g.rescue(rnd.choice([22,33]),rnd.choice([22,33]))
            elif action==2:g.escape(rnd.choice([22,33]))
            elif action==3:g.sync(22,'RED','WARRIOR',True,rnd.randrange(7,17),0)
            elif action==4:g.sync(33,'RED','MAGE',True,rnd.randrange(7,17),2)
            else:g.status(rnd.choice([22,33]))
            self.assertLessEqual(len(g.effects),2)
            for e in g.effects.values():self.assertTrue(0<=e['ticks']<=TICKS)
    def test_stuck_target_never_permanent_root(self):
        g=game();g.cast(11,22)
        for t in [0.3,0.7,1.1,2,2.1,2.6,3]:g.advance(t)
        self.assertFalse(g.status(22)['rooted'])
    def test_cooldown_can_not_be_reset_by_remove(self):
        g=game();g.cast(11,22);g.remove(11);g.sync(11,'BLUE','TRAPPER',True,0,0);self.assertEqual(g.cast(11,33)[1],'COOLDOWN')
    def test_diff_match_instances_isolation(self):
        a,b=game(),game();a.cast(11,22);self.assertFalse(b.status(22)['trapped'])
    def test_poison_total_across_twelve_seconds_bounded(self):
        g=game();g.cast(11,22)
        damage=sum(z['damage'] for _,_,es in [g.advance(1),g.advance(2),g.advance(3),g.advance(12)] for z in es)
        self.assertEqual(damage,9)
    def test_friendly_fire_not_possible_after_switch(self):
        g=game();g.sync(22,'BLUE','WARRIOR',True,8,0);self.assertEqual(g.cast(11,22)[1],'FRIENDLY_FIRE')


class TestSourceContracts(unittest.TestCase):
    def test_luau_reference_has_same_entrypoints(self):
        content=(Path(__file__).resolve().parents[1]/'luau'/'TrapRescueCore.luau').read_text()
        for name in ('new','syncPlayer','removePlayer','advance','tryCast','tryRescue','tryEscape','status','endMatch'):
            self.assertIn('function Core.'+name,content)
    def test_luau_no_remote_or_datastore(self):
        content=(Path(__file__).resolve().parents[1]/'luau'/'TrapRescueCore.luau').read_text()
        self.assertNotIn('RemoteEvent.new',content)
        self.assertNotIn('DataStoreService',content)
        self.assertNotIn('Humanoid:TakeDamage',content)
    def test_luau_duration_limits(self):
        content=(Path(__file__).resolve().parents[1]/'luau'/'TrapRescueCore.luau').read_text()
        self.assertIn('ROOT_SECONDS = 2',content)
        self.assertIn('DOT_PER_TICK = 3',content)
        self.assertIn('IMMUNITY_SECONDS = 6',content)


if __name__=='__main__':unittest.main()
