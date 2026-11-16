"""EGGRUMBLE V3 neutral-horde wall-occlusion source regression.

This checks the candidate source structure, not Roblox Studio or Android gameplay.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SWARM = ROOT / "EGGRUMBLE_SwarmCombat.luau"
PREVIEW = ROOT / "EGGRUMBLE_LobbyCastleModesPreview.server.luau"


class TestNeutralSwarmLineOfSight(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SWARM.read_text(encoding="utf-8")
        cls.preview = PREVIEW.read_text(encoding="utf-8")

    def test_neutral_aoe_checks_solid_castle_walls(self):
        s = self.source
        self.assertIn("local function lineOfSightToNeutral(", s)
        self.assertIn("params.RespectCanCollide=true", s)
        self.assertIn("params.FilterDescendantsInstances={attacker,target}", s)
        self.assertIn("return workspace:Raycast(origin,delta,params)==nil", s)
        self.assertNotIn("FilterDescendantsInstances={session.world}", s)

    def test_only_visible_targets_receive_damage_and_ko_credit(self):
        s = self.source
        line = s.index("and lineOfSightToNeutral(origin,attacker,model)")
        credit = s.index('h:SetAttribute("LastAttackerId",id)', line)
        hit = s.index("h:TakeDamage(damage)", line)
        self.assertLess(line, credit)
        self.assertLess(credit, hit)
        self.assertNotIn("local hits=math.min(MAX_HITS,#nearest)", s)
        # VFX/hit reaction may be inserted after real damage; count must be inside
        # the same LOS-guarded hit branch, not within an arbitrary char window.
        guard_end = s.index(chr(10) + "   end" + chr(10) + "  end" + chr(10) + "  return hits", hit)
        self.assertIn("hits+=1", s[hit:guard_end])
        self.assertLess(hit, s.index("hits+=1", hit))
        self.assertIn("MAX_LOS_RAYS_PER_ATTACK=48", s)
        self.assertIn("if hits>=MAX_HITS or rays>=MAX_LOS_RAYS_PER_ATTACK then break end", s)

    def test_player_aoe_origin_is_real_live_character(self):
        s = self.source
        self.assertIn('local root=character and character:FindFirstChild("HumanoidRootPart")', s)
        self.assertIn("humanoid.Health<=0 then return 0", s)
        self.assertIn("if (at-root.Position).Magnitude>36 then return 0", s)
        self.assertIn("root.Position+Vector3.new(0,1,0),character,shape or \"CIRCLE\")", s)

    def test_bot_aoe_origin_is_real_live_bot(self):
        s = self.source
        self.assertIn("local actor=session.botActors and session.botActors[botId]", s)
        self.assertIn("if not actor or not root or not h or h.Health<=0 then return 0", s)
        self.assertIn("if (root.Position-at).Magnitude>5 then return 0", s)
        self.assertIn("local center=root.Position+root.CFrame.LookVector*3", s)
        self.assertIn("root.Position+Vector3.new(0,1,0),actor,\"FANG\")", s)

    def test_neutral_navigation_never_forces_through_solid_wall(self):
        s = self.source
        self.assertIn("params.FilterDescendantsInstances={all}", s)
        self.assertIn("params.RespectCanCollide=true", s)
        self.assertIn("return workspace:Raycast(origin,step+step.Unit*.35,params)==nil", s)
        self.assertIn("if free(forward) then", s)
        self.assertIn("if free(sideways) then chosen=sideways", s)
        self.assertIn("elseif free(-sideways) then chosen=-sideways", s)
        self.assertIn("if chosen then", s)
        self.assertNotIn("local next=at+near.Unit*math.min(NEUTRAL_SPEED*.38,best)", s)

    def test_studio_only_and_existing_ko_pipeline_preserved(self):
        s = self.source
        self.assertIn('assert(RunService:IsStudio()', s)
        self.assertIn('h.Died:Connect(function()', s)
        self.assertIn('h:GetAttribute("LastAttackerId")', s)
        self.assertIn("credit(id)", s)
        self.assertIn("session.swarm=api", s)
        self.assertIn("session.swarm.damageFromPlayer(", (ROOT / "EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8"))
        for forbidden in ("RemoteEvent", "MarketplaceService", "DataStoreService", "TeleportService"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, s)


if __name__ == "__main__":
    unittest.main()
