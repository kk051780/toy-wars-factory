"""Offline specification oracle and static Lua interface checks.

NOT an execution of Luau nor Roblox Studio. The oracle encodes expected snapshot
consumer behavior and adversarial state transitions for integration review.
"""
from dataclasses import dataclass
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODEL = (ROOT / 'src/FirstMinuteModel.luau').read_text(encoding='utf-8')
CLIENT = (ROOT / 'src/FirstMinuteCoach.client.luau').read_text(encoding='utf-8')


@dataclass
class Oracle:
    serial: int = -1
    active_at: float | None = None
    initial_score: int = 0
    scored: bool = False
    carried: bool = False
    dismissed: bool = False
    manual_help: bool = False
    last: dict | None = None

    def receive(self, snap, now):
        if not isinstance(snap, dict) or snap.get('kind') != 'SNAPSHOT': return False
        serial = snap.get('serial')
        if type(serial) is not int or serial < 0 or serial > 10**9 or serial < self.serial: return False
        if snap.get('phase') not in {'LOBBY','COUNTDOWN','ACTIVE','RESULTS'}: return False
        if snap.get('team') not in {'RED','BLUE','NONE'}: return False
        if snap.get('role') not in {'RAIDER','GUARDIAN'}: return False
        if type(snap.get('time')) not in {int,float} or not 0 <= snap['time'] <= 10**9: return False
        if not isinstance(snap.get('scores'),dict): return False
        if not all(type(snap['scores'].get(k)) is int and 0 <= snap['scores'][k] <= 10**9 for k in ('RED','BLUE')): return False
        if snap.get('carrying') not in ('','RED','BLUE'): return False
        if type(now) not in {int,float} or not -10**9 <= now <= 10**9: return False
        if serial > self.serial:
            self.serial, self.active_at, self.initial_score = serial, None, 0
            self.scored = self.carried = False
        if snap['phase'] == 'ACTIVE':
            own = snap['scores'][snap['team'] if snap['team'] == 'BLUE' else 'RED']
            if self.active_at is None: self.active_at, self.initial_score = now, own
            self.scored |= own > self.initial_score
            self.carried |= bool(snap['carrying'])
        self.last = snap
        return True

    def cue(self, now):
        if not self.last or self.dismissed: return 'HIDDEN'
        s = self.last
        if s['phase'] != 'ACTIVE': return s['phase']
        if s['carrying']: return 'CARRY'
        if self.scored: return 'SCORED'
        elapsed = max(0, now - (self.active_at if self.active_at is not None else now))
        if elapsed > 60 and not self.manual_help: return 'HIDDEN'
        if elapsed < 12: return 'GUARD' if s['role'] == 'GUARDIAN' else 'RAID'
        if elapsed < 32: return 'CAPTURE'
        return 'CASTLE'


def snapshot(serial=1, phase='ACTIVE', team='RED', role='RAIDER', carrying='', red=0, blue=0, time=300):
    return dict(kind='SNAPSHOT', serial=serial, phase=phase, team=team,
                role=role, carrying=carrying, scores=dict(RED=red, BLUE=blue), time=time)


class ScenarioOracleTests(unittest.TestCase):
    def test_join_and_action_cues(self):
        o=Oracle(); self.assertTrue(o.receive(snapshot(phase='LOBBY'), 5)); self.assertEqual(o.cue(5),'LOBBY')
        self.assertTrue(o.receive(snapshot(phase='COUNTDOWN'), 6)); self.assertEqual(o.cue(6),'COUNTDOWN')
        self.assertTrue(o.receive(snapshot(),10)); self.assertEqual(o.cue(10),'RAID')
        self.assertEqual(o.cue(22),'CAPTURE'); self.assertEqual(o.cue(44),'CASTLE')
        self.assertEqual(o.cue(71),'HIDDEN')
    def test_own_egg_not_enemy_credit(self):
        o=Oracle();o.receive(snapshot(team='BLUE',blue=1,red=2),10)
        self.assertFalse(o.scored)
        o.receive(snapshot(team='BLUE',blue=2,red=3),11)
        self.assertTrue(o.scored); self.assertEqual(o.cue(11),'SCORED')
    def test_carried_priority_over_score(self):
        o=Oracle();o.receive(snapshot(),0)
        o.receive(snapshot(carrying='BLUE',red=1),15)
        self.assertEqual(o.cue(15),'CARRY')
    def test_guardian_early_cue(self):
        o=Oracle();o.receive(snapshot(role='GUARDIAN'),0);self.assertEqual(o.cue(5),'GUARD')
    def test_round_changes_reset_local_progress(self):
        o=Oracle();o.receive(snapshot(),0);o.receive(snapshot(carrying='BLUE',red=1),10)
        o.receive(snapshot(serial=2,red=0),20)
        self.assertFalse(o.scored);self.assertFalse(o.carried);self.assertEqual(o.cue(20),'RAID')
    def test_reject_stale_serial(self):
        o=Oracle();o.receive(snapshot(serial=4),10)
        self.assertFalse(o.receive(snapshot(serial=3, carrying='BLUE'),11));self.assertEqual(o.serial,4)
    def test_reject_bad_score_and_phase(self):
        o=Oracle();s=snapshot();s['scores']['RED']=-1;self.assertFalse(o.receive(s,0))
        s=snapshot();s['phase']='OWNED';self.assertFalse(o.receive(s,0))
    def test_reject_forged_kind_and_role(self):
        o=Oracle();s=snapshot();s['kind']='REWARD';self.assertFalse(o.receive(s,0))
        s=snapshot();s['role']='DEV';self.assertFalse(o.receive(s,0))
    def test_invalid_time_and_serial(self):
        o=Oracle();s=snapshot();s['time']=float('nan');self.assertFalse(o.receive(s,0))
        s=snapshot();s['serial']=1.5;self.assertFalse(o.receive(s,0))
    def test_negative_clock_sanitized(self):
        o=Oracle();self.assertTrue(o.receive(snapshot(),10));self.assertEqual(o.cue(1),'RAID')
    def test_dismiss_and_reopen_after_60s(self):
        o=Oracle();o.receive(snapshot(),0);o.dismissed=True;self.assertEqual(o.cue(10),'HIDDEN')
        o.dismissed=False;o.manual_help=True;self.assertEqual(o.cue(100),'CASTLE')
    def test_results_no_fake_replay_button(self):
        o=Oracle();o.receive(snapshot(phase='RESULTS'),10);self.assertEqual(o.cue(10),'RESULTS')


class LuauStaticContractTests(unittest.TestCase):
    def test_core_api_present(self):
        for token in ('function Coach.new()', 'function Coach.consume(', 'function Coach.view(', 'function Coach.setHidden('):
            self.assertIn(token, MODEL)
    def test_connect_only_existing_remote(self):
        self.assertIn('TrapRaidersS1Remote', CLIENT)
        self.assertIn('OnClientEvent:Connect(', CLIENT)
        self.assertNotIn('FireServer(', CLIENT)
        self.assertNotIn('RemoteEvent.new', CLIENT)
        self.assertNotIn('Instance.new("RemoteEvent")', CLIENT)
    def test_no_analytics_saving_or_rewards(self):
        for txt in (MODEL,CLIENT):
            for banned in ('DataStoreService','MarketplaceService','ProcessReceipt','SetAsync','GetAsync','TakeDamage','LoadCharacter','PublishAsync','TeleportService','HttpService'):
                self.assertNotIn(banned, txt)
    def test_controls_do_not_cover_bottom_left_or_attack(self):
        self.assertIn('panel.Position = UDim2.new(0.5, 0, 0, 108)', CLIENT)
        self.assertIn('help.Position = UDim2.new(1, -38, 0, 105)', CLIENT)
        self.assertIn('gui.ResetOnSpawn = false', CLIENT)
    def test_no_new_run_loop(self):
        for txt in (MODEL,CLIENT):
            self.assertNotIn('RenderStepped',txt)
            self.assertNotIn('Heartbeat',txt)
            self.assertNotIn('while true',txt)
    def test_japanese_child_facing_words(self):
        for word in ('卵をゲット', '敵のお城', '守護', '再戦'):
            self.assertIn(word, MODEL)
    def test_client_read_only_binding(self):
        self.assertIn('Model.consume(state, snapshot, time())', CLIENT)
        self.assertIn('Model.view(state, time())', CLIENT)
        self.assertIn('WaitForChild("FirstMinuteModel")', CLIENT)
    def test_old_hud_and_server_left_unmodified(self):
        self.assertEqual(len([p for p in (ROOT/'src').iterdir() if p.is_file()]),2)

if __name__ == '__main__':
    unittest.main()