"""WF-13 source-only regression and negative-mutation tests. Not Roblox physics tests."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = (ROOT / "src/WF13Policy.luau").read_text(encoding="utf-8")
C = (ROOT / "src/WF13ZoneController.luau").read_text(encoding="utf-8")
S = (ROOT / "src/WF13Scene.luau").read_text(encoding="utf-8")
B = (ROOT / "src/WF13Demo.server.luau").read_text(encoding="utf-8")

def no_global_gravity_assignment(text):
    return re.search(r"\b(?:workspace|Workspace|self\.workspace)\s*\.\s*Gravity\s*=(?!=)", text) is None

class WF13Tests(unittest.TestCase):
    def test_luau_files_present_and_original(self):
        for text in (P, C, S, B):
            self.assertIn("--!strict", text)
            self.assertGreater(len(text), 400)

    def test_gravity_not_changed_for_world(self):
        for text in (P, C, S, B):
            self.assertTrue(no_global_gravity_assignment(text))

    def test_negative_global_gravity_mutation_rejected(self):
        for bad in ["workspace.Gravity = 5", "self.workspace.Gravity=20",
                    "Workspace . Gravity = 0"]:
            self.assertFalse(no_global_gravity_assignment(C + "\n" + bad))

    def test_numeric_ellipsoid_and_invalid_fail_closed(self):
        self.assertIn("nx * nx + ny * ny + nz * nz <= 1", P)
        self.assertIn("if sx <= 0 or sy <= 0 or sz <= 0 then return false end", P)
        self.assertIn("n == n", P)
        self.assertIn("n < math.huge", P)

    def test_gravity_equation_bounded(self):
        self.assertIn("mass * gravity * (1 - ratio)", P)
        self.assertIn("ratio < 0.2 or ratio > 0.85", P)
        self.assertIn("Policy.GRAVITY_RATIO = 0.35", P)
        self.assertIn("Policy.MAX_DWELL = 18", P)

    def test_vertical_and_horizontal_clamping(self):
        self.assertIn("Policy.MAX_HORIZONTAL = 48", P)
        self.assertIn("Policy.MAX_FALL = 34", P)
        self.assertIn("Policy.MAX_RISE = 30", P)
        self.assertIn("Policy.clampVelocity", C)
        self.assertIn("root.AssemblyLinearVelocity", C)

    def test_requires_authoritative_character_state(self):
        self.assertIn('FindFirstChild("HumanoidRootPart")', C)
        self.assertIn('FindFirstChildOfClass("Humanoid")', C)
        self.assertIn("humanoid.Health <= 0", C)
        self.assertIn("not root or not root:IsA", C)
        self.assertIn("root.Anchored", C)

    def test_no_client_packet_or_trusted_touch(self):
        for forbidden in ("RemoteEvent", "OnServerEvent", "FireServer", "GetTouchingParts",
                          ".Touched:Connect", "DataStoreService", "MarketplaceService"):
            self.assertNotIn(forbidden, C)
        self.assertIn("self:_inside(root)", C)
        self.assertIn("self.players:GetPlayers()", C)
        self.assertIn("PointToObjectSpace", C)

    def test_exclusive_owner_and_force_components(self):
        self.assertIn("WF13GravityOwner", C)
        self.assertIn("root:GetAttribute(OWNER_ATTRIBUTE) ~= nil", C)
        self.assertIn("root:SetAttribute(OWNER_ATTRIBUTE, self.token)", C)
        self.assertIn('Instance.new("VectorForce")', C)
        self.assertIn('Instance.new("Attachment")', C)
        self.assertIn("ApplyAtCenterOfMass = true", C)
        self.assertIn("Enum.ActuatorRelativeTo.World", C)

    def test_negative_client_owner_mutation_rejected(self):
        def safe(s):
            return "root:SetNetworkOwner(nil)" in s and "root:SetNetworkOwner(player)" not in s
        self.assertTrue(safe(C))
        self.assertFalse(safe(C.replace("root:SetNetworkOwner(nil)", "root:SetNetworkOwner(player)")))

    def test_owner_restored_and_cleaned(self):
        for phrase in ("root:SetNetworkOwnershipAuto()", "root:SetNetworkOwner(entry.oldOwner)",
                       "entry.force:Destroy()", "entry.attachment:Destroy()",
                       "root:SetAttribute(OWNER_ATTRIBUTE, nil)", "PlayerRemoving", "CharacterRemoving"):
            self.assertIn(phrase, C)

    def test_single_controller_shutdown_lifecycle(self):
        for phrase in ("function Controller:start()", "function Controller:stop()",
                       "self.destroyed = true", "self:_clear(player)", "conn:Disconnect()"):
            self.assertIn(phrase, C)

    def test_expiring_gravity_and_safe_fallback(self):
        for phrase in ("Policy.LANDING_SECONDS = 2.0", "Policy.landingForce",
                       "Policy.SAFETY_DEPTH", "char:PivotTo(CFrame.new(self.safePad.Position",
                       "root.AssemblyLinearVelocity = Vector3.zero"):
            self.assertIn(phrase, P + C)

    def test_safe_noncombat_scene_and_stairs(self):
        self.assertIn('WF13LocalGravityBubble', S)
        self.assertIn('NoPayFreeGround', S)
        self.assertIn('FreeStair%02d', S)
        self.assertIn('WF13SafeRecoveryPad', S)
        self.assertIn('SkyCastleDeck', S)
        self.assertIn('ふわっと宇宙', S)
        self.assertIn('p.CanCollide = collidable', S)

    def test_avoid_duplicate_and_hazardous_scene(self):
        self.assertIn('WF13 duplicate scene', S)
        self.assertIn('p.CanTouch = collidable', S)
        self.assertIn('p.CanQuery = collidable', S)
        self.assertIn('zone.Shape = Enum.PartType.Ball', S)

    def test_disabled_and_isolated_opt_in(self):
        self.assertIn("ENABLE_WF13_ISOLATED_DEMO = false", B)
        self.assertIn("if not ENABLE_WF13_ISOLATED_DEMO then return end", B)
        self.assertIn('workspace:FindFirstChild("TRAP_RAIDERS_S1")', B)
        self.assertIn("controller:stop()", B)
        self.assertNotIn("PublishAsync", B)

    def test_negative_auto_enable_mutation_rejected(self):
        def disabled(s):
            return "ENABLE_WF13_ISOLATED_DEMO = false" in s
        self.assertTrue(disabled(B))
        self.assertFalse(disabled(B.replace("ENABLE_WF13_ISOLATED_DEMO = false",
                                            "ENABLE_WF13_ISOLATED_DEMO = true")))

    def test_no_egg_combat_or_shared_authority(self):
        for fragment in ("score =", "award", "damage(", "match.serial", "S1Rules =",
                         "SetNetworkOwnershipAuto(player)"):
            self.assertNotIn(fragment, C)
        self.assertNotIn("S1CanonicalRoundHost", B)

if __name__ == "__main__":
    unittest.main()
