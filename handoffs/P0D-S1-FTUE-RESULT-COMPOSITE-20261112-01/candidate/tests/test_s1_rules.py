import unittest
from s1_reference import S1, ROLES

class S1Regression(unittest.TestCase):
    def setUp(self):
        self.g = S1()
        self.g.join('a')
        self.g.join('b')
        self.assertTrue(self.g.start())
        self.g.advance(3)

    def test_balanced_teams(self):
        self.assertEqual((self.g.players['a'].team, self.g.players['b'].team), ('RED','BLUE'))
    def test_no_solo_start(self):
        g=S1();g.join('a');self.assertFalse(g.start())
    def test_start_serial(self): self.assertEqual(self.g.serial,1)
    def test_steal_enemy_egg(self): self.assertTrue(self.g.steal('a','BLUE'))
    def test_cannot_steal_own(self): self.assertFalse(self.g.steal('a','RED'))
    def test_far_steal_denied(self): self.assertFalse(self.g.steal('a','BLUE',40))
    def test_negative_distance_denied(self): self.assertFalse(self.g.steal('a','BLUE',-1))
    def test_duplicate_egg_carrier(self):
        self.g.steal('a','BLUE');self.g.join('c');self.assertFalse(self.g.steal('c','BLUE'))
    def test_carry_only_one(self):
        self.g.steal('a','BLUE');self.assertFalse(self.g.steal('a','RED'))
    def test_death_drops_egg(self):
        self.g.steal('a','BLUE');self.g.death('a');self.assertIsNone(self.g.egg_owner['BLUE'])
    def test_disconnect_drops_egg(self):
        self.g.steal('a','BLUE');self.g.quit('a');self.assertIsNone(self.g.egg_owner['BLUE'])
    def test_steal_after_drop(self):
        self.g.steal('a','BLUE');self.g.death('a');self.g.join('c');self.assertTrue(self.g.steal('c','BLUE'))
    def test_can_score_enemy_egg(self):
        self.g.steal('a','BLUE');self.assertTrue(self.g.deliver('a','RED'));self.assertEqual(self.g.score['RED'],1)
    def test_cannot_score_at_enemy_pad(self):
        self.g.steal('a','BLUE');self.assertFalse(self.g.deliver('a','BLUE'))
    def test_far_score_denied(self):
        self.g.steal('a','BLUE');self.assertFalse(self.g.deliver('a','RED',200))
    def test_own_egg_stolen_cannot_score(self):
        self.g.steal('a','BLUE');self.g.steal('b','RED');self.assertFalse(self.g.deliver('a','RED'))
    def test_two_captures_win(self):
        for _ in range(2):self.g.steal('a','BLUE');self.g.deliver('a','RED')
        self.assertEqual((self.g.winner,self.g.phase,self.g.reason),('RED','RESULTS','EGG_CAPTURE'))
    def test_post_victory_no_steals(self):
        for _ in range(2):self.g.steal('a','BLUE');self.g.deliver('a','RED')
        self.assertFalse(self.g.steal('b','RED'))
    def test_role_switch_active_blocked(self): self.assertFalse(self.g.role('a',1,'GUARDIAN'))
    def test_invalid_role_blocked(self): self.g.phase='LOBBY';self.assertFalse(self.g.role('a',1,'WIZARD'))
    def test_role_changes_before_match(self):
        self.g.phase='LOBBY';self.assertTrue(self.g.role('a',1,'GUARDIAN'));self.assertEqual(self.g.players['a'].role,'GUARDIAN')
    def test_role_change_cooldown(self):
        self.g.phase='LOBBY';self.g.role('a',1,'GUARDIAN');self.assertFalse(self.g.role('a',2,'RAIDER'))
    def test_role_cooldown_after_time(self):
        self.g.phase='LOBBY';self.g.role('a',1,'GUARDIAN');self.g.advance(3);self.assertTrue(self.g.role('a',2,'RAIDER'))
    def test_invalid_seq_zero(self): self.assertFalse(self.g.attack('a',0))
    def test_invalid_seq_bool(self): self.assertFalse(self.g.attack('a',True))
    def test_invalid_seq_string(self): self.assertFalse(self.g.attack('a','bad'))
    def test_invalid_seq_beyond_cap(self): self.assertFalse(self.g.attack('a',10**10))
    def test_repeated_seq_refused(self):
        self.g.attack('a',1,castle_distance=8);self.assertFalse(self.g.attack('a',1,castle_distance=8))
    def test_seq_must_be_increasing(self):
        self.g.attack('a',10,castle_distance=8);self.assertFalse(self.g.attack('a',9))
    def test_rate_limited_attack(self):
        self.assertTrue(self.g.attack('a',1,castle_distance=8));self.assertFalse(self.g.attack('a',2,castle_distance=8))
    def test_cooldown_expires(self):
        self.g.attack('a',1,castle_distance=8);self.g.advance(.9);self.assertTrue(self.g.attack('a',2,castle_distance=8))
    def test_attacking_enemy_damages(self):
        hp=self.g.players['b'].hp;self.assertTrue(self.g.attack('a',1,enemy_pid='b',castle_distance=999));self.assertEqual(self.g.players['b'].hp,hp-24)
    def test_invisible_enemy_no_damage(self):
        self.assertFalse(self.g.attack('a',1,enemy_pid='b',line_of_sight=False,castle_distance=999))
    def test_out_of_reach_enemy(self):
        self.assertFalse(self.g.attack('a',1,enemy_pid='b',enemy_distance=99,castle_distance=999))
    def test_attack_enemy_behind_back(self):
        self.assertFalse(self.g.attack('a',1,enemy_pid='b',target_dot=-1,castle_distance=999))
    def test_spawn_shield(self):
        self.g.players['b'].invulnerable_until=self.g.now+2;self.assertFalse(self.g.attack('a',1,enemy_pid='b',castle_distance=999))
    def test_cannot_hit_friend(self):
        self.g.join('c');self.assertFalse(self.g.attack('a',1,enemy_pid='c',castle_distance=999))
    def test_castle_only_enemy(self):
        self.assertTrue(self.g.attack('a',1,castle_distance=10));self.assertEqual(self.g.castle['BLUE'],286)
    def test_castle_far_denied(self): self.assertFalse(self.g.attack('a',1,castle_distance=99))
    def test_castle_behind_denied(self): self.assertFalse(self.g.attack('a',1,castle_distance=10,castle_dot=-1))
    def test_castle_destruction_wins(self):
        for _ in range(22):
            self.g.attack('a',self.g.players['a'].last_seq+1,castle_distance=9)
            self.g.advance(.9)
        self.assertEqual((self.g.winner,self.g.reason),('RED','CASTLE_DESTROYED'))
    def test_guardian_damage_lower(self):
        self.g.players['a'].role='GUARDIAN';self.g.attack('a',1,castle_distance=10);self.assertEqual(self.g.castle['BLUE'],290)
    def test_dead_attacker_denied(self):
        self.g.death('a');self.assertFalse(self.g.attack('a',1,castle_distance=9))
    def test_quitter_forfeit(self):
        self.g.quit('b');self.assertEqual((self.g.winner,self.g.reason),('RED','OPPONENT_LEFT'))
    def test_results_prevent_damage(self):
        self.g.finish('BLUE','FORFEIT');self.assertFalse(self.g.attack('a',1,castle_distance=9))
    def test_alarm_transitions(self):
        self.g.advance(53);self.assertEqual(self.g.alarm,'WARNING');self.g.advance(3);self.assertEqual(self.g.alarm,'SIGNAL');self.g.advance(6);self.assertEqual(self.g.alarm,'IDLE')
    def test_alarm_doesnt_damage(self):
        self.g.advance(55);self.assertEqual(self.g.castle,{'RED':300,'BLUE':300})
    def test_second_round_resets_rewards(self):
        self.g.steal('a','BLUE');self.g.deliver('a','RED');self.g.finish('RED','TEST');self.assertTrue(self.g.start());self.assertEqual((self.g.score['RED'],self.g.serial),(0,2))
    def test_seq_survives_new_match(self):
        self.g.attack('a',7,castle_distance=8);self.g.finish('BLUE','TEST');self.g.start();self.assertFalse(self.g.attack('a',7,castle_distance=9))
    def test_clock_negative_denied(self):
        with self.assertRaises(ValueError):self.g.advance(-1)
    def test_all_role_presets(self):self.assertEqual(set(ROLES),{'RAIDER','GUARDIAN'})

if __name__ == '__main__':unittest.main()
