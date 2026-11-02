"""Synthetic chronology regressions. No provider attestation or network I/O."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import importlib.util
import sys
import unittest

MODULE = Path(__file__).resolve().parents[1] / "tools" / "system_dispatch_run_attribution.py"
spec = importlib.util.spec_from_file_location("system_dispatch_run_attribution", MODULE)
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)

TICKET = {"epoch": 412, "owner_id": "0b4b06ab-e120-461d-b086-7021cc95429d",
          "acquired_at": "2026-11-02T09:14:57.299Z", "expires_at": "2026-11-02T09:16:57.299Z"}
RUN = {"task_id": mod.WORKER_TASK, "id": "f57248f2-d7f4-8332-a947-2aceb260cdc4",
       "scheduled_for": "2026-11-02T09:14:33.425089Z",
       "started_at": "2026-11-02T09:19:35.615992Z",
       "completed_at": "2026-11-02T09:19:48.645149Z", "recorded_status": "completed",
       "chat_ref": {"type": "chatgpt", "id": "6ae4c147-ede8-83e8-8cc4-57e49f5f77bb"}}


def values():
    return deepcopy(TICKET), deepcopy(RUN)


def stamp(seconds):
    d = datetime.fromisoformat(TICKET["acquired_at"].replace("Z", "+00:00"))
    return (d + timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


class DispatchAttributionTests(unittest.TestCase):
    def denied(self, outcome):
        self.assertEqual(outcome["attribution"], "UNATTRIBUTED")
        self.assertEqual(outcome["cause"], "INDETERMINATE")
        self.assertEqual(outcome["provider_run_binding_verified"], False)
        for key in ("may_adopt", "may_write", "may_extend_ticket", "may_recover_foreign", "may_dispatch"):
            self.assertIs(outcome[key], False)

    def test_actual_epoch412_due_before_acquire(self):
        t, r = values()
        x = mod.audit(t, r)
        self.assertEqual(x["state"], "SCHEDULED_BEFORE_DISPATCH")
        self.denied(x)

    def test_actual_epoch413_within_ttl_still_unattributed(self):
        t, r = values()
        t.update(epoch=413, owner_id="f5e13e26-b090-45d8-9021-6b6cb845b752",
                 acquired_at="2026-11-02T11:23:37.378Z", expires_at="2026-11-02T11:25:37.378Z")
        r.update(id="234b995f-4c0c-8323-b0be-61ccc5700ef4",
                 scheduled_for="2026-11-02T11:24:20.222809Z",
                 started_at="2026-11-02T11:24:48.570149Z",
                 completed_at="2026-11-02T11:25:00.132494Z")
        x = mod.audit(t, r)
        self.assertEqual(x["state"], "WITHIN_TTL_BUT_UNATTRIBUTED")
        self.denied(x)

    def test_start_after_expiry(self):
        t, r = values()
        r.update(scheduled_for=stamp(1), started_at=stamp(121), completed_at=stamp(122))
        self.assertEqual(mod.audit(t, r)["state"], "STARTED_AFTER_EXPIRY")

    def test_exact_expiry_is_expired(self):
        t, r = values()
        r.update(scheduled_for=stamp(1), started_at=stamp(120), completed_at=stamp(121))
        self.assertEqual(mod.audit(t, r)["state"], "STARTED_AFTER_EXPIRY")

    def test_exact_second_before_expiry_not_authorized(self):
        t, r = values()
        r.update(scheduled_for=stamp(1), started_at=stamp(119), completed_at=stamp(121))
        self.denied(mod.audit(t, r))

    def test_zero_second(self):
        t, r = values()
        r.update(scheduled_for=stamp(0), started_at=stamp(0), completed_at=stamp(1))
        self.assertEqual(mod.audit(t, r)["state"], "WITHIN_TTL_BUT_UNATTRIBUTED")

    def test_run_started_before_ticket(self):
        t, r = values()
        r.update(scheduled_for=stamp(0), started_at=stamp(-1), completed_at=stamp(1))
        self.assertEqual(mod.audit(t, r)["state"], "STARTED_BEFORE_DISPATCH")

    def test_missing_chat_ref_does_not_grant(self):
        t, r = values()
        r.update(chat_ref=None, scheduled_for=stamp(1), started_at=stamp(2), completed_at=stamp(3))
        self.denied(mod.audit(t, r))

    def test_failure_status_does_not_grant(self):
        t, r = values()
        r["recorded_status"] = "failed"
        self.denied(mod.audit(t, r))

    def test_no_update_status_does_not_grant(self):
        t, r = values()
        r["recorded_status"] = "no_update"
        self.denied(mod.audit(t, r))

    def test_bad_ticket_shape_rejected(self):
        t, r = values()
        t["provider_verified"] = True
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_TICKET_SHAPE"): mod.audit(t, r)

    def test_bad_run_shape_rejected(self):
        t, r = values()
        r["dispatch_id"] = t["owner_id"]
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_RUN_SHAPE"): mod.audit(t, r)

    def test_bool_epoch_rejected(self):
        t, r = values()
        t["epoch"] = True
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_EPOCH"): mod.audit(t, r)

    def test_wrong_task_rejected(self):
        t, r = values()
        r["task_id"] = "other"
        with self.assertRaisesRegex(mod.EvidenceError, "WRONG_TASK"): mod.audit(t, r)

    def test_bad_uuid_rejected(self):
        t, r = values()
        r["id"] = "not-a-uuid"
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_UUID"): mod.audit(t, r)

    def test_expiry_121_seconds_rejected(self):
        t, r = values()
        t["expires_at"] = stamp(121)
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_DISPATCH_TTL"): mod.audit(t, r)

    def test_expiry_119_seconds_rejected(self):
        t, r = values()
        t["expires_at"] = stamp(119)
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_DISPATCH_TTL"): mod.audit(t, r)

    def test_finished_before_started_rejected(self):
        t, r = values()
        r["completed_at"] = stamp(-120)
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_RUN_CHRONOLOGY"): mod.audit(t, r)

    def test_naive_time_rejected(self):
        t, r = values()
        r["started_at"] = "2026-11-02T09:19:35"
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_INSTANT"): mod.audit(t, r)

    def test_nonterminal_rejected(self):
        t, r = values()
        r["recorded_status"] = "in_progress"
        with self.assertRaisesRegex(mod.EvidenceError, "RUN_NOT_TERMINAL"): mod.audit(t, r)

    def test_foreign_chat_ref_rejected(self):
        t, r = values()
        r["chat_ref"] = {"type": "codex", "id": "x"}
        with self.assertRaisesRegex(mod.EvidenceError, "INVALID_CHAT_REF"): mod.audit(t, r)

    def test_none_or_list_inputs_rejected(self):
        t, r = values()
        for inp in (None, [], "{}"):
            with self.subTest(inp=inp), self.assertRaises(mod.EvidenceError): mod.audit(inp, r)

    def test_time_offset_equivalence(self):
        t, r = values()
        t["acquired_at"] = "2026-11-02T18:14:57.299+09:00"
        t["expires_at"] = "2026-11-02T18:16:57.299+09:00"
        self.assertEqual(mod.audit(t, r)["state"], "SCHEDULED_BEFORE_DISPATCH")


    def test_epoch412_reports_both_conditions_not_only_first(self):
        t, r = values()
        flags = mod.audit(t, r)["chronology_signals"]
        self.assertIs(flags["scheduled_before_acquire"], True)
        self.assertIs(flags["started_at_or_after_expiry"], True)
        self.assertIs(flags["started_before_acquire"], False)
        self.assertIs(flags["scheduled_time_after_start"], False)

    def test_epoch413_in_window_has_no_temporal_contradiction(self):
        t, r = values()
        t.update(epoch=413, owner_id="f5e13e26-b090-45d8-9021-6b6cb845b752",
                 acquired_at="2026-11-02T11:23:37.378Z", expires_at="2026-11-02T11:25:37.378Z")
        r.update(id="234b995f-4c0c-8323-b0be-61ccc5700ef4",
                 scheduled_for="2026-11-02T11:24:20.222809Z",
                 started_at="2026-11-02T11:24:48.570149Z",
                 completed_at="2026-11-02T11:25:00.132494Z")
        self.assertEqual(mod.audit(t, r)["chronology_signals"],
                         {"scheduled_before_acquire": False,
                          "started_before_acquire": False,
                          "started_at_or_after_expiry": False,
                          "scheduled_time_after_start": False})

    def test_expiry_boundary_flag_is_independent_of_schedule_flag(self):
        t, r = values()
        r.update(scheduled_for=stamp(-1), started_at=stamp(120), completed_at=stamp(121))
        flags = mod.audit(t, r)["chronology_signals"]
        self.assertIs(flags["scheduled_before_acquire"], True)
        self.assertIs(flags["started_at_or_after_expiry"], True)

    def test_early_run_start_flag_is_independent(self):
        t, r = values()
        r.update(scheduled_for=stamp(-20), started_at=stamp(-10), completed_at=stamp(1))
        flags = mod.audit(t, r)["chronology_signals"]
        self.assertIs(flags["scheduled_before_acquire"], True)
        self.assertIs(flags["started_before_acquire"], True)
        self.assertIs(flags["started_at_or_after_expiry"], False)

    def test_scheduled_time_after_start_is_informational_only(self):
        t, r = values()
        r.update(scheduled_for=stamp(70), started_at=stamp(20), completed_at=stamp(30))
        result = mod.audit(t, r)
        self.assertIs(result["chronology_signals"]["scheduled_time_after_start"], True)
        self.denied(result)



if __name__ == "__main__": unittest.main()
