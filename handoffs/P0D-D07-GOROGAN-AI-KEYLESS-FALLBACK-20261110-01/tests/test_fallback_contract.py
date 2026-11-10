"""Static safety contract tests for the independent D07 fallback.

These tests do NOT execute Luau and do NOT establish Roblox Studio QA.
"""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "src" / "GoroganS1AttackIntent.luau").read_text(encoding="utf-8")


class Contract(unittest.TestCase):
    def test_file_has_returned_module(self):
        self.assertIn("return Core", SOURCE)

    def test_no_network_authority(self):
        self.assertNotRegex(SOURCE, r"(?i)RemoteEvent|FireServer|OnServerEvent")

    def test_no_hp_writer(self):
        self.assertNotRegex(SOURCE, r"(?i)TakeDamage|Humanoid.Health|SetAttribute\(.*HP")

    def test_no_new_event_scheduler(self):
        self.assertNotRegex(SOURCE, r"(?i)Random\.new|math\.random|RoundCoordinator")

    def test_default_inactive(self):
        self.assertRegex(SOURCE, r"active\s*=\s*false")

    def test_server_only_gate(self):
        self.assertGreaterEqual(SOURCE.count("server_authorized == true"), 2)

    def test_stale_round_rejected(self):
        self.assertIn("s.match_id == self.match_id", SOURCE)
        self.assertIn("s.epoch == self.epoch", SOURCE)

    def test_stage_s1_only(self):
        self.assertIn("s.stage == 1", SOURCE)
        self.assertIn("trusted.stage ~= 1", SOURCE)

    def test_monotonic_time(self):
        self.assertIn("s.now <= self.last_time", SOURCE)

    def test_two_second_warning(self):
        self.assertIn("s.now - self.tell_started < 2.0", SOURCE)
        self.assertIn("min_resolve_time = s.now + 2", SOURCE)

    def test_three_attack_limit(self):
        self.assertIn("self.count >= 3", SOURCE)

    def test_damage_cap(self):
        self.assertIn("max_damage = 8", SOURCE)

    def test_receipt_required(self):
        self.assertIn("receipt_required = true", SOURCE)

    def test_damage_not_applied_here(self):
        self.assertGreaterEqual(SOURCE.count("damage_applied = false"), 3)

    def test_target_disappearance_fails_closed(self):
        self.assertIn("s.target_id ~= self.target_id", SOURCE)

    def test_distance_cap_on_resolve(self):
        self.assertIn("distance2(s.boss, s.target) > 10 * 10", SOURCE)

    def test_no_shared_lock_mutation(self):
        self.assertNotRegex(SOURCE, r"(?i)CAS|lock\.json|WORK_REQUESTS|DataStore")

    def test_no_hardcoded_private_key(self):
        self.assertNotRegex(SOURCE, r"(?i)PRIVATE KEY|github_pat_|ghp_")

    def test_stop_no_active_target(self):
        self.assertIn('self.target_id = nil', SOURCE)

    def test_clean_room_explicit(self):
        self.assertIn("NOT the original encrypted", SOURCE)


if __name__ == "__main__":
    unittest.main()
