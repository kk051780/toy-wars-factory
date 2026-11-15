"""EGGRUMBLE V3 Studio-only preview: regression tests for physically grounded bots.

These source checks are NOT Luau native compile or Roblox Studio/runtime proof.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def spatial_problems(preview: str, actors: str) -> list[str]:
    errors = []
    if 'local BotActors=require(script.Parent:WaitForChild("EGGRUMBLE_BotActors"))' not in preview:
        errors.append("bot module not required")
    if preview.count("BotActors.start(session,Rules)") != 1:
        errors.append("exactly one grounded bot loop required")
    if "task.wait(2.4)" in preview or "Rules.damageCastle(session.rules,target.id,bot.id,18)" in preview:
        errors.append("ghost AI damage/egg timer is forbidden")
    if "Rules.takeEggs(session.rules,bot.id" in preview:
        errors.append("ghost AI egg pickup is forbidden")
    if 'params.FilterDescendantsInstances={actorFolder}' not in actors:
        errors.append("raycast must see solid castle parts")
    if "params.RespectCanCollide=true" not in actors:
        errors.append("noncollidable cosmetics must not hide solid obstacles")
    if "steeringStep(actor,goal,AI_TICK,actors)" not in actors:
        errors.append("steering may only ignore bot model collection")
    if 'local raidTarget=enemyLoc+Vector3.new(18,3,9)' not in actors:
        errors.append("raid must target outside the solid castle core")
    if "elseif hasEgg then raidTarget" not in actors:
        errors.append("egg action must use the reached exterior location")
    if "actualDist<=ACTION_DISTANCE" not in actors:
        errors.append("egg/siege/deposit action must have physical distance gate")
    if "lastSiege[id]=now" not in actors:
        errors.append("siege rate limit missing")
    if "if not RunService:IsStudio() then return end" not in preview:
        errors.append("studio-only preview guard removed")
    return errors


class SpatialBotSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.preview = (ROOT / "EGGRUMBLE_LobbyCastleModesPreview.server.luau").read_text(encoding="utf-8")
        cls.actors = (ROOT / "EGGRUMBLE_BotActors.luau").read_text(encoding="utf-8")

    def test_current_sources_pass(self):
        self.assertEqual([], spatial_problems(self.preview, self.actors))

    def test_old_ghost_siege_regression_rejected(self):
        bad = self.preview + '\n-- regression: task.wait(2.4) Rules.damageCastle(session.rules,target.id,bot.id,18)'
        self.assertIn("ghost AI damage/egg timer is forbidden", spatial_problems(bad, self.actors))

    def test_ghost_egg_pickup_rejected(self):
        bad = self.preview + '\nRules.takeEggs(session.rules,bot.id,1,target.id)'
        self.assertIn("ghost AI egg pickup is forbidden", spatial_problems(bad, self.actors))

    def test_missing_bot_module_rejected(self):
        bad = self.preview.replace('local BotActors=require(script.Parent:WaitForChild("EGGRUMBLE_BotActors"))', '-- removed')
        self.assertIn("bot module not required", spatial_problems(bad, self.actors))

    def test_duplicate_ai_loop_rejected(self):
        bad = self.preview + '\nBotActors.start(session,Rules)'
        self.assertIn("exactly one grounded bot loop required", spatial_problems(bad, self.actors))

    def test_castle_is_not_excluded_from_raycast(self):
        bad = self.actors.replace("params.FilterDescendantsInstances={actorFolder}",
                                  "params.FilterDescendantsInstances={folder,model}")
        self.assertIn("raycast must see solid castle parts", spatial_problems(self.preview, bad))

    def test_noncollidable_visuals_do_not_mask_wall(self):
        bad = self.actors.replace("params.RespectCanCollide=true", "")
        self.assertIn("noncollidable cosmetics must not hide solid obstacles", spatial_problems(self.preview, bad))

    def test_bot_cannot_trigger_siege_remotely(self):
        bad = self.actors.replace("actualDist<=ACTION_DISTANCE", "true")
        self.assertIn("egg/siege/deposit action must have physical distance gate",
                      spatial_problems(self.preview, bad))

    def test_core_blocked_raid_waypoint_rejected(self):
        bad = self.actors.replace("local raidTarget=enemyLoc+Vector3.new(18,3,9)",
                                  "local raidTarget=enemyLoc+Vector3.new(0,3,6)")
        self.assertIn("raid must target outside the solid castle core",
                      spatial_problems(self.preview, bad))


if __name__ == "__main__":
    unittest.main()
