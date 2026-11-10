import unittest
import math
import random
from stamp_reference import State, new_state, apply, view, sample, valid_evidence, MAX_ROUNDS


class StampReferenceTests(unittest.TestCase):
    def setUp(self):
        self.s = new_state(123456)

    def test_fresh(self): self.assertEqual(view(self.s)["stamps"], 0)
    def test_new_state_zero(self): self.assertFalse(self.s.finalized)
    def test_new_state_owner_zero(self):
        with self.assertRaises(ValueError): new_state(0)
    def test_new_state_bool(self):
        with self.assertRaises(ValueError): new_state(True)
    def test_new_state_negative(self):
        with self.assertRaises(ValueError): new_state(-1)
    def test_loss_earns_one(self): self.assertEqual(apply(self.s, sample())[1]["awarded"], 1)
    def test_win_earns_two(self): self.assertEqual(apply(self.s, sample(won=True))[1]["awarded"], 2)
    def test_assist_earns_two(self): self.assertEqual(apply(self.s, sample(contributed=True))[1]["awarded"], 2)
    def test_win_assist_no_three(self): self.assertEqual(apply(self.s, sample(won=True, contributed=True))[1]["awarded"], 2)
    def test_stamps_no_persistence(self):
        s, _ = apply(self.s, sample())
        self.assertTrue(view(s)["sessionOnly"])
        self.assertFalse(view(s)["saved"])
    def test_no_mutation(self):
        s, _ = apply(self.s, sample())
        self.assertEqual(self.s.stamps, 0)
        self.assertEqual(self.s.finalized, {})
        self.assertNotEqual(s.finalized, self.s.finalized)
    def test_duplicate_rejected(self):
        s, _ = apply(self.s, sample())
        z, r = apply(s, sample(won=True))
        self.assertIs(z, s)
        self.assertEqual(r["status"], "DUPLICATE_FINALIZATION")
    def test_afk_rejected(self): self.assertEqual(apply(self.s, sample(activeSeconds=0))[1]["awarded"], 0)
    def test_no_action(self): self.assertEqual(apply(self.s, sample(meaningfulServerActions=0))[1]["awarded"], 0)
    def test_afk_finalized_no_later_win(self):
        s, r = apply(self.s, sample(activeSeconds=0))
        self.assertEqual(r["status"], "INELIGIBLE_FINALIZED")
        self.assertEqual(apply(s, sample(won=True))[1]["awarded"], 0)
    def test_short_round_below_threshold(self): self.assertEqual(apply(self.s, sample(roundSeconds=10, activeSeconds=2.9))[1]["awarded"], 0)
    def test_short_round_at_threshold(self): self.assertEqual(apply(self.s, sample(roundSeconds=10, activeSeconds=3))[1]["awarded"], 1)
    def test_long_round_under_15(self): self.assertEqual(apply(self.s, sample(activeSeconds=14.9))[1]["awarded"], 0)
    def test_long_round_at_15(self): self.assertEqual(apply(self.s, sample(activeSeconds=15))[1]["awarded"], 1)
    def test_bad_owner(self): self.assertEqual(apply(self.s, sample(userId=123455))[1]["status"], "INVALID_EVIDENCE")
    def test_bad_kind(self): self.assertEqual(apply(self.s, sample(kind="CLIENT_EVENT"))[1]["status"], "INVALID_EVIDENCE")
    def test_unfinished(self): self.assertEqual(apply(self.s, sample(completed=False))[1]["status"], "INVALID_EVIDENCE")
    def test_bad_job(self): self.assertEqual(apply(self.s, sample(jobId="ADMIN"))[1]["status"], "INVALID_EVIDENCE")
    def test_bad_stage(self): self.assertEqual(apply(self.s, sample(stageId="S5"))[1]["status"], "INVALID_EVIDENCE")
    def test_invalid_match_id(self): self.assertEqual(apply(self.s, sample(matchId="a"))[1]["status"], "INVALID_EVIDENCE")
    def test_missing_match_id(self): self.assertEqual(apply(self.s, sample(matchId=None))[1]["status"], "INVALID_EVIDENCE")
    def test_whitespace_match_id(self): self.assertEqual(apply(self.s, sample(matchId="bad-id "))[1]["status"], "INVALID_EVIDENCE")
    def test_nan_round(self): self.assertEqual(apply(self.s, sample(roundSeconds=math.nan))[1]["status"], "INVALID_EVIDENCE")
    def test_inf_active(self): self.assertEqual(apply(self.s, sample(activeSeconds=math.inf))[1]["status"], "INVALID_EVIDENCE")
    def test_active_over_round(self): self.assertEqual(apply(self.s, sample(activeSeconds=61))[1]["status"], "INVALID_EVIDENCE")
    def test_active_negative(self): self.assertEqual(apply(self.s, sample(activeSeconds=-1))[1]["status"], "INVALID_EVIDENCE")
    def test_bool_action(self): self.assertEqual(apply(self.s, sample(meaningfulServerActions=True))[1]["status"], "INVALID_EVIDENCE")
    def test_negative_action(self): self.assertEqual(apply(self.s, sample(meaningfulServerActions=-1))[1]["status"], "INVALID_EVIDENCE")
    def test_action_float(self): self.assertEqual(apply(self.s, sample(meaningfulServerActions=0.5))[1]["status"], "INVALID_EVIDENCE")
    def test_win_not_bool(self): self.assertEqual(apply(self.s, sample(won=1))[1]["status"], "INVALID_EVIDENCE")
    def test_contribution_not_bool(self): self.assertEqual(apply(self.s, sample(contributed=1))[1]["status"], "INVALID_EVIDENCE")
    def test_first_unlock(self):
        s, _ = apply(self.s, sample("m-0001", won=True))
        s, r = apply(s, sample("m-0002"))
        self.assertEqual(r["unlocks"], ("FREE_EGG_BANNER",))
        self.assertEqual(s.stamps, 3)
    def test_second_unlock(self):
        s = self.s
        for i in range(2): s, _ = apply(s, sample(f"m-{i+1:04d}", won=True))
        s, r = apply(s, sample("m-0003", won=True))
        self.assertEqual(r["unlocks"], ("FREE_TRAP_TRAIL",))
        self.assertEqual(s.stamps, 6)
    def test_unlock_idempotent(self):
        s, _ = apply(self.s, sample("m-0001", won=True))
        s, r = apply(s, sample("m-0002", won=True))
        self.assertIn("FREE_EGG_BANNER", r["unlocks"])
        s, r2 = apply(s, sample("m-0002", won=True))
        self.assertEqual(r2["unlocks"], ())
    def test_view_no_private_ledger(self):
        s, _ = apply(self.s, sample())
        self.assertFalse(any("ledger" in k.lower() or "match" in k.lower() or "user" in k.lower() for k in view(s)))
    def test_view_milestones(self):
        s = self.s
        for i in range(3): s, _ = apply(s, sample(f"m-{i+1:04d}", won=True))
        self.assertIsNone(view(s)["nextRewardAt"])
        self.assertEqual(view(s)["toNextReward"], 0)
    def test_multiple_players_state(self):
        other = new_state(654321)
        self.assertEqual(apply(other, sample())[1]["status"], "INVALID_EVIDENCE")
    def test_ledger_capacity_fail_closed(self):
        ledger = {f"m-{i:04d}": 1 for i in range(MAX_ROUNDS)}
        s = State(123456, MAX_ROUNDS, ledger)
        nxt, r = apply(s, sample("new-round"))
        self.assertIs(nxt, s)
        self.assertEqual(r["status"], "LEDGER_FULL")
    def test_invalid_state(self):
        s = State(123456, -1)
        self.assertEqual(apply(s, sample())[1]["status"], "INVALID_STATE")
    def test_oversized_ledger(self):
        s = State(123456, 0, {f"m-{i:04d}": 0 for i in range(MAX_ROUNDS + 1)})
        self.assertEqual(apply(s, sample())[1]["status"], "INVALID_STATE")
    def test_exact_full_ledger(self):
        s = State(123456, 1022, {f"m-{i:04d}": 2 for i in range(MAX_ROUNDS-1)})
        nxt, r = apply(s, sample("next-round", won=True))
        self.assertEqual(nxt.stamps, 1024)
        self.assertEqual(r["awarded"], 2)
        self.assertEqual(apply(nxt, sample("extra-round"))[1]["status"], "LEDGER_FULL")
    def test_tampered_total_rejected(self):
        s = State(123456, 1023, {"old-round": 2})
        self.assertEqual(apply(s, sample("new-round"))[1]["status"], "INVALID_STATE")
    def test_randomized_invariants(self):
        rng = random.Random(44037)
        s = self.s
        seen = set()
        for i in range(400):
            ident = f"match-{rng.randint(1, 180):04d}"
            ev = sample(ident, won=bool(rng.randrange(2)), contributed=bool(rng.randrange(2)),
                        activeSeconds=rng.random() * 60, meaningfulServerActions=rng.randint(0, 6))
            before = s.stamps
            s, receipt = apply(s, ev)
            self.assertGreaterEqual(s.stamps, before)
            self.assertLessEqual(s.stamps-before, 2)
            self.assertEqual(s.stamps, sum(s.finalized.values()))
            if ident in seen:
                self.assertEqual(receipt["awarded"], 0)
            seen.add(ident)
    def test_every_job_and_stage(self):
        for job in ["WARRIOR", "NINJA", "TRAPPER", "ZOMBIE_MASTER", "BEAST_TAMER", "MAGE", "BUILDER"]:
            for stage in ("S1", "S2", "S3", "S4"):
                self.assertTrue(valid_evidence(sample(jobId=job, stageId=stage), 123456))
    def test_reconnect_same_user_different_state_not_persistent(self):
        old, _ = apply(self.s, sample())
        new = new_state(123456)
        self.assertEqual(new.stamps, 0)
        self.assertEqual(old.stamps, 1)

if __name__ == "__main__": unittest.main()
