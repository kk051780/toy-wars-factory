"""Actual game-source activation guards; intentionally no Studio/device emulation."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime_activation import (
    REQUIRED_RUNTIME_SOURCES,
    evaluate_runtime_activation,
    guard_lines,
)


def clean_sources():
    return {name: "return { healthy = true }\n" for name in REQUIRED_RUNTIME_SOURCES}


class RuntimeActivationTest(unittest.TestCase):
    def test_real_current_game_host_early_return_impacts_eight_domains(self):
        sources = clean_sources()
        sources["EGGRUMBLE_LobbyCastleModesPreview"] = (
            "local RunService=game:GetService('RunService')\n"
            "if not RunService:IsStudio() then return end\n"
            "local flags = {}\n"
        )
        result = evaluate_runtime_activation(sources)
        self.assertEqual(result["production_runtime"], "BLOCKED_STUDIO_ONLY_GAME_HOST")
        self.assertEqual(len(result["eight_domain_production_impact"]), 8)
        self.assertFalse(result["product_go"])
        self.assertEqual(result["guards"][0]["line"], 2)
        self.assertEqual(result["guards"][0]["kind"], "STUDIO_ONLY_EARLY_RETURN")

    def test_bot_role_replay_score_assertion_all_block_product(self):
        sources = clean_sources()
        for name in ("EGGRUMBLE_BotActors", "EGGRUMBLE_SevenRoleCombat",
                     "EGGRUMBLE_RoundReplay", "EGGRUMBLE_MatchResultService"):
            sources[name] = "assert(RunService:IsStudio(), 'preview only')\nreturn {}\n"
        result = evaluate_runtime_activation(sources)
        self.assertEqual(result["guard_count"], 4)
        self.assertEqual(result["production_runtime"], "BLOCKED_STUDIO_ONLY_GAME_HOST")
        self.assertIn("battle", result["eight_domain_production_impact"])
        self.assertIn("balance", result["eight_domain_production_impact"])

    def test_studio_guard_comments_are_not_runtime_evidence(self):
        source = ('-- if not RunService:IsStudio() then return end\n'
                  'local title = "studio private preview"\n'
                  '-- assert(RunService:IsStudio(), "scaffold only")\n')
        self.assertEqual(guard_lines(source), [])

    def test_embedded_comment_after_guard_does_not_hide_it(self):
        rows = guard_lines("if not RunService:IsStudio() then return end -- private\n")
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["kind"], "STUDIO_ONLY_EARLY_RETURN")

    def test_missing_actor_source_is_fail_closed(self):
        sources = clean_sources()
        del sources["EGGRUMBLE_SevenRoleCombat"]
        result = evaluate_runtime_activation(sources)
        self.assertEqual(result["source_guard_inspection"], "MISSING_OWNER_SOURCE")
        self.assertIn("EGGRUMBLE_SevenRoleCombat", result["missing_sources"])
        self.assertFalse(result["product_go"])

    def test_guard_free_source_is_never_automatic_production_go(self):
        result = evaluate_runtime_activation(clean_sources())
        self.assertEqual(result["source_guard_inspection"], "COMPLETE")
        self.assertEqual(result["production_runtime"], "NOT_VERIFIED_FAIL_CLOSED")
        self.assertFalse(result["product_go"])
        self.assertEqual(result["official_rc_integrated"],
                         "UNVERIFIED_REQUIRES_AUTHENTICATED_220_ACK")

    def test_not_a_second_server_or_remote_implementation(self):
        import inspect
        import runtime_activation
        script = inspect.getsource(runtime_activation)
        self.assertNotIn("Instance.new(", script)
        self.assertNotIn("RemoteEvent:Fire", script)
        self.assertNotIn("DataStoreService", script)


if __name__ == "__main__":
    unittest.main()
