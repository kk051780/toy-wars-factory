import unittest
import pathlib
from scale_oracle import ScaleState

PKG = pathlib.Path(__file__).resolve().parents[1]
CORE = (PKG / 'luau' / 'D16ScaleFxCore.luau').read_text(encoding='utf-8')


def args(**updates):
    p = dict(match_id='M1', event_id='E1', epoch=1, now_ms=1000,
             effect='GIANT_ONE', roster=[3, 2, 1], target=2)
    p.update(updates)
    return p


class D16ScaleOracle(unittest.TestCase):
    def test_giant(self):
        s = ScaleState(); self.assertEqual(s.begin(**args()), (True, 'STARTED'))
        x, state = s.snapshot(1000, 'M1', 1)
        self.assertEqual(state, 'ACTIVE'); self.assertEqual(x['visualScale'], 1.6)
        self.assertEqual(x['userIds'], [2]); self.assertEqual(x['expiresAtMs'], 9000)

    def test_mini(self):
        s = ScaleState(); self.assertTrue(s.begin(**args(effect='MINI_ALL', target=None))[0])
        self.assertEqual(s.snapshot(2000, 'M1', 1)[0]['userIds'], [1,2,3]); self.assertEqual(s.active['visualScale'], .7)

    def test_copy_not_mutable(self):
        s=ScaleState();s.begin(**args()); x,_=s.snapshot(2000,'M1',1)
        x['userIds'].append(999);self.assertEqual(s.snapshot(3000,'M1',1)[0]['userIds'],[2])

    def test_expire_exact_8_seconds(self):
        s=ScaleState();s.begin(**args());self.assertEqual(s.snapshot(8999,'M1',1)[1],'ACTIVE')
        self.assertEqual(s.snapshot(9000,'M1',1)[1],'CLOSED_OR_EXPIRED')

    def test_close_early(self):
        s=ScaleState();s.begin(**args());self.assertEqual(s.close('M1',1,1050),(True,'CLOSED'))
        self.assertIsNone(s.snapshot(1051,'M1',1)[0])

    def test_replay_after_close_rejected(self):
        s=ScaleState();s.begin(**args());s.close('M1',1,1100)
        self.assertEqual(s.begin(**args(now_ms=1200)),(False,'DUPLICATE_OR_ACTIVE'))

    def test_another_active_rejected(self):
        s=ScaleState();s.begin(**args());self.assertEqual(s.begin(**args(match_id='M2',epoch=2,now_ms=1500)),(False,'DUPLICATE_OR_ACTIVE'))

    def test_new_round_after_close(self):
        s=ScaleState();s.begin(**args());s.close('M1',1,1100)
        self.assertTrue(s.begin(**args(match_id='M2',epoch=2,now_ms=1101))[0])

    def test_stale_epoch(self):
        s=ScaleState();s.begin(**args(epoch=4));s.close('M1',4,1100)
        self.assertEqual(s.begin(**args(epoch=3,now_ms=1200)),(False,'STALE_EPOCH'))

    def test_match_end_clears(self):
        s=ScaleState();s.begin(**args());self.assertEqual(s.snapshot(1100,'M2',1)[1],'CLOSED_OR_EXPIRED')

    def test_disconnect_requires_close(self):
        s=ScaleState();s.begin(**args());self.assertTrue(s.close('M1',1,1200)[0])

    def test_reject_no_target(self):
        self.assertEqual(ScaleState().begin(**args(target=None))[1],'INVALID_TARGET')

    def test_reject_target_not_roster(self):
        self.assertEqual(ScaleState().begin(**args(target=99))[1],'TARGET_NOT_IN_ROSTER')

    def test_reject_target_in_mini(self):
        self.assertEqual(ScaleState().begin(**args(effect='MINI_ALL'))[1],'UNEXPECTED_TARGET')

    def test_reject_bad_effect(self):
        self.assertEqual(ScaleState().begin(**args(effect='METEOR'))[1],'INVALID_EFFECT')

    def test_reject_empty_roster(self):
        self.assertEqual(ScaleState().begin(**args(roster=[]))[1],'INVALID_ROSTER')

    def test_reject_duplicate_roster(self):
        self.assertEqual(ScaleState().begin(**args(roster=[1,1]))[1],'INVALID_ROSTER')

    def test_reject_bool_player(self):
        self.assertEqual(ScaleState().begin(**args(roster=[True,2]))[1],'INVALID_ROSTER')

    def test_reject_inf_nan(self):
        for v in [float('inf'), float('-inf'), float('nan')]:
            with self.subTest(v=v):self.assertEqual(ScaleState().begin(**args(now_ms=v))[1],'INVALID_CLOCK')

    def test_reject_clock_regression(self):
        s=ScaleState();s.begin(**args());self.assertEqual(s.snapshot(999,'M1',1)[1],'CLOCK_BACKWARDS')

    def test_reject_no_id(self):
        self.assertEqual(ScaleState().begin(**args(match_id=''))[1],'INVALID_ID')

    def test_reject_bad_epoch(self):
        self.assertEqual(ScaleState().begin(**args(epoch=1.5))[1],'INVALID_ID')

    def test_reject_bad_roster_type(self):
        self.assertEqual(ScaleState().begin(**args(roster={1:2}))[1],'INVALID_ROSTER')

    def test_roster_upper_bound(self):
        self.assertEqual(ScaleState().begin(**args(roster=list(range(1,26))))[1],'INVALID_ROSTER')

    def test_capacity_fail_closed(self):
        s=ScaleState();s.seen={('M'+str(x),x) for x in range(128)}
        self.assertEqual(s.begin(**args(match_id='FRESH'))[1],'ANTI_REPLAY_CAPACITY')

    def test_no_roblox_instance_manipulation(self):
        for forbidden in ['Instance.new','Humanoid','RemoteEvent','SetPrimaryPartCFrame','BodyScale','LoadCharacter','math.random']:
            with self.subTest(forbidden=forbidden):self.assertNotIn(forbidden,CORE)

    def test_luau_contract_names(self):
        for token in ['function Core.begin', 'function Core.snapshot', 'function Core.close', 'GIANT_ONE = 1.6', 'MINI_ALL = 0.7', 'TTL_MS = 8000', 'MAX_SEEN_ROUNDS = 128']:
            with self.subTest(token=token):self.assertIn(token,CORE)

    def test_no_side_effectful_scheduler(self):
        for forbidden in ['Heartbeat:Connect','RunService','task.spawn','task.delay','while true','OnServerEvent']:
            with self.subTest(forbidden=forbidden):self.assertNotIn(forbidden, CORE)

if __name__=='__main__': unittest.main()
