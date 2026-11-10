"""Pure Python behavior oracle + strict source surface tests (NOT Luau execution)."""
from __future__ import annotations
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MODEL = (ROOT / 'src/WorldRouteModel.luau').read_text('utf-8')
CLIENT = (ROOT / 'src/WorldRouteGuide.client.luau').read_text('utf-8')
DOC = (ROOT / 'docs/INTEGRATION.md').read_text('utf-8')


def resolve(snapshot, last_serial=-1):
    if not isinstance(snapshot, dict) or snapshot.get('kind') != 'SNAPSHOT':
        return None
    serial = snapshot.get('serial')
    if type(serial) is not int or serial < 0 or serial > 10**9 or serial < last_serial:
        return None
    phase, team, carrying = snapshot.get('phase'), snapshot.get('team'), snapshot.get('carrying')
    if phase not in {'LOBBY','COUNTDOWN','ACTIVE','RESULTS'}:
        return None
    if team not in {'RED','BLUE','NONE'} or carrying not in {'','RED','BLUE'}:
        return None
    if phase != 'ACTIVE':
        return (serial, 'NONE', None, None)
    if team not in {'RED','BLUE'}: return None
    enemy = 'BLUE' if team == 'RED' else 'RED'
    if carrying == enemy: return (serial,'HOME_PAD',f'{team}_CASTLE',f'{team}_SCORE_PAD')
    if carrying == '': return (serial,'ENEMY_EGG',f'{enemy}_CASTLE',f'{enemy}_EGG')
    return None


def sample(**updates):
    x = {'kind':'SNAPSHOT','serial':1,'phase':'ACTIVE','team':'RED','carrying':''}
    x.update(updates)
    return x


class WorldRouteModelContract(unittest.TestCase):
    def test_red_enemy_egg(self): self.assertEqual(resolve(sample()), (1,'ENEMY_EGG','BLUE_CASTLE','BLUE_EGG'))
    def test_blue_enemy_egg(self): self.assertEqual(resolve(sample(team='BLUE')), (1,'ENEMY_EGG','RED_CASTLE','RED_EGG'))
    def test_red_home_pad(self): self.assertEqual(resolve(sample(carrying='BLUE')), (1,'HOME_PAD','RED_CASTLE','RED_SCORE_PAD'))
    def test_blue_home_pad(self): self.assertEqual(resolve(sample(team='BLUE',carrying='RED')), (1,'HOME_PAD','BLUE_CASTLE','BLUE_SCORE_PAD'))
    def test_lobby_hidden(self): self.assertEqual(resolve(sample(phase='LOBBY'))[1], 'NONE')
    def test_countdown_hidden(self): self.assertEqual(resolve(sample(phase='COUNTDOWN'))[1], 'NONE')
    def test_results_hidden(self): self.assertEqual(resolve(sample(phase='RESULTS'))[1], 'NONE')
    def test_drop_returns_to_enemy_egg(self):
        self.assertEqual(resolve(sample(serial=2,carrying=''))[1], 'ENEMY_EGG')
    def test_stale_round_refused(self): self.assertIsNone(resolve(sample(serial=1),2))
    def test_same_round_repeated_ok(self): self.assertIsNotNone(resolve(sample(serial=2),2))
    def test_new_round_ok(self): self.assertIsNotNone(resolve(sample(serial=3),2))
    def test_invalid_team_none_active(self): self.assertIsNone(resolve(sample(team='NONE')))
    def test_invalid_own_egg_red(self): self.assertIsNone(resolve(sample(carrying='RED')))
    def test_invalid_own_egg_blue(self): self.assertIsNone(resolve(sample(team='BLUE',carrying='BLUE')))
    def test_bad_carry(self): self.assertIsNone(resolve(sample(carrying='PWN')))
    def test_missing_carry(self): self.assertIsNone(resolve({'kind':'SNAPSHOT','serial':1,'phase':'ACTIVE','team':'RED'}))
    def test_wrong_kind(self): self.assertIsNone(resolve(sample(kind='ATTACK')))
    def test_wrong_packet_type(self): self.assertIsNone(resolve('attack'))
    def test_negative_serial(self): self.assertIsNone(resolve(sample(serial=-1)))
    def test_bool_serial(self): self.assertIsNone(resolve(sample(serial=True)))
    def test_fraction_serial(self): self.assertIsNone(resolve(sample(serial=1.5)))
    def test_huge_serial(self): self.assertIsNone(resolve(sample(serial=10**12)))
    def test_bad_phase(self): self.assertIsNone(resolve(sample(phase='ADMIN')))


class WorldRouteStaticBoundaries(unittest.TestCase):
    def test_pure_model_no_engine_services(self):
        for token in ('game:GetService', 'RemoteEvent', 'FireServer', 'FireClient', 'DataStore', 'math.random'):
            self.assertNotIn(token, MODEL)
    def test_single_existing_remote_subscriber(self):
        self.assertIn('WaitForChild("TrapRaidersS1Remote")', CLIENT)
        self.assertEqual(CLIENT.count('OnClientEvent:Connect'), 1)
    def test_zero_client_fire_or_network_creation(self):
        self.assertNotRegex(CLIENT, r'FireServer\s*\(|FireClient\s*\(|Instance\.new\("Remote')
    def test_single_pooled_billboard(self):
        self.assertEqual(CLIENT.count('Instance.new("BillboardGui")'), 1)
        self.assertEqual(CLIENT.count('Instance.new("TextLabel")'), 1)
    def test_adorn_same_world_parts(self):
        for item in ('TRAP_RAIDERS_S1', 'BLUE_CASTLE', 'RED_CASTLE', 'BLUE_EGG',
                     'RED_EGG', 'BLUE_SCORE_PAD', 'RED_SCORE_PAD'):
            source = CLIENT + MODEL + DOC
            self.assertIn(item, source)
    def test_no_player_gui_overwrite(self):
        self.assertNotIn('Destroy(', CLIENT)
        self.assertNotIn('ClearAllChildren', CLIENT)
    def test_retry_late_replication_without_wait_block(self):
        self.assertIn('FindFirstChild("TRAP_RAIDERS_S1")', CLIENT)
        self.assertIn('local target = resolveWorldPart(', CLIENT)
    def test_no_loop_heartbeat_renderstep(self):
        self.assertNotIn('RenderStepped', CLIENT)
        self.assertNotIn('Heartbeat', CLIENT)
        self.assertNotIn('while true', CLIENT)
    def test_no_teleport_or_damage(self):
        for token in ('CFrame =', 'TakeDamage', 'Humanoid.Health', 'RemoteFunction', 'MarketplaceService'):
            self.assertNotIn(token, CLIENT)
    def test_client_requires_pure_model(self):
        self.assertIn('require(shared:WaitForChild("WorldRouteModel"))', CLIENT)
    def test_status_no_studio_claims(self):
        self.assertIn('NOT_TESTED', DOC)
        self.assertIn('Rollback', DOC)


if __name__ == '__main__': unittest.main()