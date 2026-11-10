"""No Roblox Studio execution; Python oracle + structural Luau safety checks."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from seat_reference import Seats

SRC = (ROOT / 'luau' / 'SeatAuthorityPolicy.luau').read_text(encoding='utf-8')


def frame(**over):
    result = dict(server_authorized=True, match_id='roundA', epoch=4, stage=1,
                  vehicle_id='carA', now=0.0, sequence=1, role='DRIVER',
                  player_id='actorA', character_generation=3,
                  player_alive=True, server_seat_occupant_verified=True)
    result.update(over)
    return result


class Behavior(unittest.TestCase):
    def start(self):
        s = Seats()
        self.assertEqual(s.begin(frame()), 'STARTED')
        return s

    def test_init_inactive(self):
        self.assertEqual(Seats().assign(frame(now=1)), 'REJECTED')

    def test_begin_requires_server(self):
        self.assertEqual(Seats().begin(frame(server_authorized=False)), 'REJECTED')

    def test_begin_rejects_stage_invalid(self):
        self.assertEqual(Seats().begin(frame(stage=5)), 'REJECTED')

    def test_begin_rejects_negative_epoch(self):
        self.assertEqual(Seats().begin(frame(epoch=-1)), 'REJECTED')

    def test_two_seats(self):
        s=self.start()
        self.assertEqual(s.assign(frame(now=0.1)), 'MOUNT_INTENT')
        self.assertEqual(s.assign(frame(role='PASSENGER',player_id='actorB',now=0.2,sequence=2)), 'MOUNT_INTENT')
        self.assertEqual(len(s.occupants),2)

    def test_duplicate_seat_rejected(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.assign(frame(now=0.2,sequence=2,player_id='B')), 'REJECTED')

    def test_player_cannot_claim_two_seats(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.assign(frame(role='PASSENGER',now=0.2,sequence=2)), 'REJECTED')

    def test_fake_occupant_rejected(self):
        s=self.start()
        self.assertEqual(s.assign(frame(now=0.1,server_seat_occupant_verified=False)), 'REJECTED')

    def test_dead_player_rejected(self):
        s=self.start()
        self.assertEqual(s.assign(frame(now=0.1,player_alive=False)), 'REJECTED')

    def test_replay_sequence_rejected(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.assign(frame(role='PASSENGER',player_id='B',now=0.2,sequence=1)), 'REJECTED')

    def test_time_reversal_rejected(self):
        s=self.start()
        s.assign(frame(now=0.3))
        self.assertEqual(s.assign(frame(role='PASSENGER',player_id='B',now=0.2,sequence=2)), 'REJECTED')

    def test_epoch_change_clears(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.assign(frame(now=0.2,epoch=5,sequence=2)), 'REJECTED')
        self.assertFalse(s.active)
        self.assertEqual(len(s.occupants),0)

    def test_vehicle_change_clears(self):
        s=self.start()
        self.assertEqual(s.assign(frame(now=0.1,vehicle_id='other')), 'REJECTED')
        self.assertFalse(s.active)

    def test_valid_refresh(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.refresh(frame(now=1.0,sequence=2)), 'REFRESHED')
        self.assertAlmostEqual(s.occupants['DRIVER'].expires,2.5)

    def test_stale_refresh_rejected(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.refresh(frame(now=2.0,sequence=2)), 'REJECTED')
        self.assertEqual(len(s.occupants),0)

    def test_generation_mismatch_clears_seat(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.refresh(frame(now=0.2,sequence=2,character_generation=4)), 'REJECTED')
        self.assertEqual(len(s.occupants),0)

    def test_unauthorized_release_rejected(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.release(frame(now=0.2,sequence=2,player_id='B')), 'REJECTED')

    def test_valid_release(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.release(frame(now=0.2,sequence=2)), 'RELEASED')
        self.assertFalse(s.occupants)

    def test_expiry_tick(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.tick(frame(now=1.61)), 'TICK')
        self.assertFalse(s.occupants)

    def test_round_change_tick_fails_closed(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.tick(frame(now=0.2,match_id='next')), 'STOPPED')
        self.assertFalse(s.active)

    def test_explicit_stop(self):
        s=self.start()
        s.assign(frame(now=0.1))
        self.assertEqual(s.stop(), 'STOPPED')
        self.assertFalse(s.occupants)


class Static(unittest.TestCase):
    def test_default_off(self):
        self.assertIn('enabled = false',SRC)

    def test_receipt_only(self):
        self.assertIn('physical_mount_performed = false',SRC)
        self.assertIn('authority_receipt_required = true',SRC)

    def test_no_remotes(self):
        self.assertNotIn('OnServerEvent',SRC)
        self.assertNotIn('FireClient(',SRC)
        self.assertNotIn('FireServer(',SRC)

    def test_no_physics(self):
        self.assertNotIn('Instance.new(',SRC)
        self.assertNotIn('WeldConstraint',SRC)
        self.assertNotIn('PivotTo(',SRC)
        self.assertNotIn('Humanoid.Sit',SRC)

    def test_no_other_seat_claim(self):
        self.assertNotIn('SeatCore',SRC)
        self.assertNotIn('VehicleSeat',SRC)

    def test_no_reward_or_rng(self):
        self.assertNotIn('math.random',SRC)
        self.assertNotIn('DataStore',SRC)
        self.assertNotIn('TakeDamage',SRC)

    def test_strict_server_approval(self):
        self.assertIn('server_seat_occupant_verified ~= true',SRC)
        self.assertIn('s.server_authorized == true',SRC)

    def test_generation_binding(self):
        self.assertIn('held.character_generation ~= s.character_generation',SRC)

    def test_duplicate_actor_check(self):
        self.assertIn('held.player_id == s.player_id',SRC)

    def test_bounded_lease(self):
        self.assertIn('s.now + 1.5',SRC)

    def test_cap_two_roles(self):
        self.assertIn('DRIVER = true, PASSENGER = true',SRC)


if __name__ == '__main__':
    unittest.main()
