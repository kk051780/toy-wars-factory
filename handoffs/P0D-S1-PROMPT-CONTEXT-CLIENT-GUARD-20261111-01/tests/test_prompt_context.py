"""Independent Python scenario oracle + actual Luau text static boundaries (NOT Luau execution)."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODEL = (ROOT / 'src/PromptContextModel.luau').read_text(encoding='utf-8')
CLIENT = (ROOT / 'src/PromptContextGuard.client.luau').read_text(encoding='utf-8')


def consume(state, payload):
    if not isinstance(payload, dict) or payload.get('kind') != 'SNAPSHOT':
        return False
    n = payload.get('serial')
    serial_ok = type(n) in (int, float) and n == n and 0 <= n <= 10**9 and n % 1 == 0
    if serial_ok and n < state['serial']:
        return False
    state['valid'] = False
    if not serial_ok:
        return False
    state['serial'] = n
    phase, team, carry = payload.get('phase'), payload.get('team'), payload.get('carrying')
    if phase not in {'LOBBY', 'COUNTDOWN', 'ACTIVE', 'RESULTS'}:
        return False
    if team not in {'RED', 'BLUE', 'NONE'}:
        return False
    if carry not in {'', 'RED', 'BLUE'}:
        return False
    if phase == 'ACTIVE' and (team == 'NONE' or carry == team):
        return False
    state.update(phase=phase, team=team, carrying=carry, valid=True)
    return True


def view(state, own_egg_visible):
    result = {key: False for key in ['RED_EGG', 'BLUE_EGG', 'RED_SCORE_PAD', 'BLUE_SCORE_PAD']}
    if not state['valid'] or state['phase'] != 'ACTIVE' or state['team'] not in {'RED', 'BLUE'}:
        return result
    enemy = 'BLUE' if state['team'] == 'RED' else 'RED'
    if state['carrying'] == '':
        result[enemy + '_EGG'] = True
    elif state['carrying'] == enemy and own_egg_visible is True:
        result[state['team'] + '_SCORE_PAD'] = True
    return result


def packet(phase='ACTIVE', team='RED', carrying='', serial=1):
    return dict(kind='SNAPSHOT', serial=serial, phase=phase, team=team, carrying=carrying)


class TestScenario(unittest.TestCase):
    def setUp(self):
        self.s = dict(serial=-1, valid=False, phase='UNKNOWN', team='NONE', carrying='')

    def test_preauthority_hidden(self):
        self.assertFalse(any(view(self.s, True).values()))

    def test_lobby_hidden(self):
        self.assertTrue(consume(self.s, packet('LOBBY')))
        self.assertFalse(any(view(self.s, True).values()))

    def test_countdown_hidden(self):
        consume(self.s, packet('COUNTDOWN'))
        self.assertFalse(any(view(self.s, True).values()))

    def test_results_hidden(self):
        consume(self.s, packet('RESULTS'))
        self.assertFalse(any(view(self.s, True).values()))

    def test_red_empty_carries_only_blue_egg(self):
        consume(self.s, packet())
        self.assertEqual([k for k, v in view(self.s, True).items() if v], ['BLUE_EGG'])

    def test_blue_empty_carries_only_red_egg(self):
        consume(self.s, packet(team='BLUE'))
        self.assertEqual([k for k, v in view(self.s, True).items() if v], ['RED_EGG'])

    def test_red_carried_blue_score_own(self):
        consume(self.s, packet(carrying='BLUE'))
        self.assertEqual([k for k, v in view(self.s, True).items() if v], ['RED_SCORE_PAD'])

    def test_blue_carried_red_score_own(self):
        consume(self.s, packet(team='BLUE', carrying='RED'))
        self.assertEqual([k for k, v in view(self.s, True).items() if v], ['BLUE_SCORE_PAD'])

    def test_hidden_when_own_egg_stolen(self):
        consume(self.s, packet(carrying='BLUE'))
        self.assertFalse(any(view(self.s, False).values()))

    def test_hidden_when_unknown_own_egg(self):
        consume(self.s, packet(carrying='BLUE'))
        self.assertFalse(any(view(self.s, None).values()))

    def test_snap_back_to_enemy_egg_after_delivery(self):
        consume(self.s, packet(carrying='BLUE'))
        consume(self.s, packet(carrying=''))
        self.assertTrue(view(self.s, True)['BLUE_EGG'])

    def test_round_serial_change(self):
        consume(self.s, packet(serial=2, team='RED'))
        consume(self.s, packet('LOBBY', serial=2))
        self.assertFalse(any(view(self.s, True).values()))
        consume(self.s, packet(serial=3, team='BLUE'))
        self.assertEqual([k for k, v in view(self.s, True).items() if v], ['RED_EGG'])

    def test_stale_serial_is_ignored(self):
        consume(self.s, packet(serial=3))
        self.assertFalse(consume(self.s, packet(serial=2, phase='RESULTS')))
        self.assertTrue(view(self.s, True)['BLUE_EGG'])

    def test_unrelated_non_snapshot_ignored(self):
        consume(self.s, packet())
        self.assertFalse(consume(self.s, {'kind': 'EVENT', 'serial': 99}))
        self.assertTrue(view(self.s, True)['BLUE_EGG'])

    def test_malformed_current_snapshot_fails_closed(self):
        consume(self.s, packet())
        self.assertFalse(consume(self.s, packet(team='WRONG')))
        self.assertFalse(any(view(self.s, True).values()))

    def test_recover_after_invalid(self):
        consume(self.s, packet(team='WRONG'))
        self.assertTrue(consume(self.s, packet()))
        self.assertTrue(view(self.s, True)['BLUE_EGG'])

    def test_mismatched_team_carry_fails(self):
        self.assertFalse(consume(self.s, packet(team='RED', carrying='RED')))
        self.assertFalse(any(view(self.s, True).values()))

    def test_active_none_team_fails(self):
        self.assertFalse(consume(self.s, packet(team='NONE')))

    def test_missing_carry_fails(self):
        d = packet()
        del d['carrying']
        self.assertFalse(consume(self.s, d))

    def test_missing_serial_fails(self):
        d = packet()
        del d['serial']
        self.assertFalse(consume(self.s, d))

    def test_nan_inf_negative_serial_invalid(self):
        for n in (float('nan'), float('inf'), -1, 1e10, -float('inf'), 1.5, True):
            with self.subTest(n=n):
                self.assertFalse(consume(self.s, packet(serial=n)))

    def test_non_table_rejected(self):
        for d in (None, 'text', 1, [], {}):
            self.assertFalse(consume(self.s, d))

    def test_invalid_phase(self):
        self.assertFalse(consume(self.s, packet(phase='PAUSE')))

    def test_invalid_carry(self):
        self.assertFalse(consume(self.s, packet(carrying='ANY')))

    def test_both_sides_symmetric(self):
        for team in ('RED', 'BLUE'):
            self.s = dict(serial=-1, valid=False)
            consume(self.s, packet(team=team))
            self.assertEqual(sum(view(self.s, True).values()), 1)
            consume(self.s, packet(team=team, carrying='BLUE' if team == 'RED' else 'RED'))
            self.assertEqual(sum(view(self.s, True).values()), 1)


class TestActualSourceContract(unittest.TestCase):
    def test_real_luau_module_functions(self):
        for s in ('function PromptPolicy.new()', 'function PromptPolicy.consume(', 'function PromptPolicy.view(', 'return PromptPolicy'):
            self.assertIn(s, MODEL)

    def test_local_script_has_real_remote_listener(self):
        self.assertIn('remote.OnClientEvent:Connect(', CLIENT)
        self.assertIn('Model.consume(current, packet)', CLIENT)

    def test_server_remote_not_invoked(self):
        for s in (MODEL, CLIENT):
            self.assertNotIn('FireServer', s) if 'client-only' in s else None
            self.assertNotIn('Instance.new("RemoteEvent")', s)
        # Comment documentation may mention forbidden operations; distinguish executable methods.
        self.assertNotRegex(CLIENT, r'\bremote\s*:\s*FireServer\s*\(')
        self.assertNotRegex(CLIENT, r'\bremote\s*:\s*FireClient\s*\(')

    def test_no_enabled_mutation(self):
        for line in CLIENT.splitlines():
            if not line.strip().startswith('--'):
                self.assertNotRegex(line, r'\.Enabled\s*=')

    def test_only_local_style_mutation(self):
        self.assertIn('Enum.ProximityPromptStyle.Custom', CLIENT)
        self.assertIn('Enum.ProximityPromptStyle.Default', CLIENT)
        self.assertIn('prompt.Style = desired', CLIENT)

    def test_original_map_scoped(self):
        self.assertIn('"TRAP_RAIDERS_S1"', CLIENT)
        for token in ('"RED"', '"BLUE"', '"_EGG"', '"_SCORE_PAD"'):
            self.assertIn(token, CLIENT)

    def test_current_team_egg_home_fails_closed(self):
        self.assertIn('ownEgg.Transparency <= 0.05', CLIENT)
        self.assertIn('Model.view(current, ownEggVisible and alive())', CLIENT)

    def test_unknown_custom_ui_not_overwritten(self):
        self.assertIn('prompt.Style ~= Enum.ProximityPromptStyle.Default then return', CLIENT)

    def test_restore_on_destroy(self):
        self.assertIn('script.Destroying:Connect(restoreOwned)', CLIENT)

    def test_no_scheduler_loop(self):
        self.assertNotIn('while true', CLIENT)
        self.assertNotIn('RunService', CLIENT)

    def test_schema_contract_json(self):
        m = json.loads((ROOT / 'BUILD_MANIFEST.json').read_text())
        self.assertEqual(set(m), {'format', 'game_id', 'work_id', 'packet_id', 'public_source_allowed', 'files'})
        self.assertEqual(m['format'], 'P0D_PUBLIC_SOURCE_V1')
        self.assertEqual(m['game_id'], 'TRAP_RAIDERS')
        self.assertTrue(m['public_source_allowed'])
        self.assertEqual(len(m['files']), 5)

    def test_manifest_sha_bytes(self):
        m = json.loads((ROOT / 'BUILD_MANIFEST.json').read_text())
        self.assertEqual(len(m['files']), 5)
        for item in m['files']:
            with self.subTest(path=item['path']):
                content = (ROOT / item['path']).read_bytes()
                self.assertEqual(len(content), item['size'])
                self.assertEqual(hashlib.sha256(content).hexdigest(), item['sha256'])


if __name__ == '__main__':
    unittest.main()
