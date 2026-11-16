#!/usr/bin/env python3
"""Static/source-only checks; real native Luau and Studio require separate evidence."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
POLICY = (ROOT / "EGGRUMBLE_CastleDefensePolicy.luau").read_text(encoding="utf-8")
RUNTIME = (ROOT / "EGGRUMBLE_CastleDefenseLive.luau").read_text(encoding="utf-8")
NATIVE = (ROOT / "tests" / "EGGRUMBLE_CastleDefensePolicy.spec.luau").read_text(encoding="utf-8")


class DefenseSourceContract(unittest.TestCase):
    def test_three_real_server_mechanics(self):
        for term in ('for _,kind in ipairs(Policy.ORDER)', 'kind=="TRAP"', 'kind=="SENSOR"'):
            self.assertIn(term, RUNTIME)
        self.assertIn("closest.hum:TakeDamage", RUNTIME)
        self.assertIn('p:SetAttribute("EGGRUMBLE_StealthUntil",now)', RUNTIME)

    def test_no_second_authoritative_game_or_spend(self):
        for forbidden in ("DataStoreService", "MarketplaceService", "RemoteEvent",
                          "MessagingService", "TeleportService", "FireServer",
                          "PromptProductPurchase"):
            self.assertNotIn(forbidden, RUNTIME + POLICY)

    def test_cannot_run_as_public_published_game(self):
        self.assertIn('assert(RunService:IsStudio()', RUNTIME)

    def test_only_session_bound_targets(self):
        self.assertIn("pairs(session.rules.castles)", RUNTIME)
        self.assertIn("Policy.canTarget(session.mode,owner,enemy)", RUNTIME)
        self.assertIn("Policy.canTarget(session.mode,owner,targetState)", RUNTIME)
        self.assertNotIn("workspace:GetDescendants()", RUNTIME)

    def test_disarmed_after_match_and_owner_elimination(self):
        self.assertIn('session.rules.phase=="ACTIVE"', RUNTIME)
        self.assertIn("if not owner.alive", RUNTIME)
        self.assertIn("if not targetState or not Policy.canTarget", RUNTIME)

    def test_no_wall_penetration_by_damage(self):
        self.assertIn("RespectCanCollide=true", RUNTIME)
        self.assertIn("clearRay(part.Position,root.Position,model,folder)", RUNTIME)
        self.assertIn("needsLOS=true", POLICY)
        self.assertIn("needsLOS=false", POLICY)

    def test_bounded_tick_and_castle_budget(self):
        self.assertIn("TICK_SECONDS=0.35", POLICY)
        self.assertIn("MAX_CASTLES=16", POLICY)
        self.assertIn("#session.roster<=Policy.MAX_CASTLES", RUNTIME)
        self.assertIn("last[id][kind]=now", RUNTIME)

    def test_no_untagged_shop_feature_or_durable_buff(self):
        self.assertIn("session.castleDefenseStop=stop", RUNTIME)
        self.assertIn("if folder.Parent then folder:Destroy() end", RUNTIME)
        self.assertIn("EGGRUMBLE_SlowExpiry", RUNTIME)
        self.assertIn("EGGRUMBLE_OriginalWalkSpeed", RUNTIME)

    def test_existing_bot_slow_contract_reused(self):
        self.assertIn('model:SetAttribute("EGGRUMBLE_SlowUntil"', RUNTIME)
        self.assertIn('player:GetAttribute("EGGRUMBLE_StealthUntil")', RUNTIME)

    def test_native_negative_cases_are_authored_not_passed(self):
        for case in ("allies must be safe", "unknown queue blocked",
                     "solid walls block turret", "trap cannot hit through walls",
                     "post-round turret blocked", "nan distance denied"):
            self.assertIn(case, NATIVE)

    def test_delayed_trap_cannot_overwrite_new_round_speed(self):
        self.assertIn("snare(session,closest.model,closest.hum", RUNTIME)
        self.assertIn('if session.rules.phase=="ACTIVE" and session.world.Parent', RUNTIME)

    def test_author_host_supports_one_safe_defense_hook(self):
        author = ROOT.parent / "P0D-PQG-SEVEN-HERO-PLAYABLE-20261116"
        rules = (author / "EGGRUMBLE_CastleMatchRules.luau").read_text(encoding="utf-8")
        host = (author / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
        project = (author / "EGGRUMBLE_V3_STUDIO.project.json").read_text(encoding="utf-8")
        for equipped in ("TURRET=4", "TRAP=3", "SENSOR=2"):
            self.assertIn(equipped, rules)
        self.assertEqual(host.count("BotActors.start(session,Rules)"), 1)
        self.assertEqual(host.count('if session.world.Parent then session.world:Destroy() end'), 1)
        self.assertIn("EGGRUMBLE_LobbyCastleModesPreview", project)
        self.assertIn("EGGRUMBLE_CastleMatchRules", project)

    def test_spec_has_no_ownership_overlap_files(self):
        paths = sorted(p.name for p in ROOT.glob("*.luau"))
        self.assertEqual(paths, ["EGGRUMBLE_CastleDefenseLive.luau",
                                 "EGGRUMBLE_CastleDefensePolicy.luau"])


if __name__ == "__main__":
    unittest.main()
