"""Original source contract + negative checks; does not run Roblox Studio."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
P=(ROOT/"src/G5StudioCheckpointPlan.luau").read_text(encoding="utf-8")
S=(ROOT/"src/WorldG5StudioEvidence.server.luau").read_text(encoding="utf-8")
PROJECT=json.loads((ROOT/"default.project.json").read_text(encoding="utf-8"))

class G5StandaloneContracts(unittest.TestCase):
    def test_source_and_safe_disabled(self):
        self.assertIn("ENABLE_G5_STUDIO_EVIDENCE = false",S)
        self.assertIn("if not ENABLE_G5_STUDIO_EVIDENCE then return end",S)
        self.assertIn("RunService:IsStudio()",S)
        self.assertIn('FindFirstChild("TRAP_RAIDERS_S1")',S)

    def test_all_five_studio_physical_roundtrips(self):
        ids=("SEA_BRIDGE","SEA_BUBBLE_A","SEA_BUBBLE_B","SKY_RAINBOW_A","SKY_RAINBOW_B")
        for name in ids:
            self.assertIn(name,P)
        self.assertIn("Plan.advance",P)
        self.assertIn("must begin and return",P)
        self.assertIn("Plan.validate",P)

    def test_actual_server_workspace_raycast_not_fake(self):
        self.assertIn("workspace:Raycast(",S)
        self.assertIn("RaycastParams.new()",S)
        self.assertIn("Enum.RaycastFilterType.Include",S)
        self.assertIn("hit.Instance==path",S)
        self.assertIn("hit.Normal.Y>=0.90",S)
        self.assertIn("physicalCount==#raySpecs",S)
        self.assertIn("real_workspace_raycast=",S)

    def test_actual_two_live_clients_and_physical_movement(self):
        self.assertIn("Players:GetPlayers()",S)
        self.assertIn("HumanoidRootPart",S)
        self.assertIn("human.Health<=0",S)
        self.assertIn("activeClientCount()<2",S)
        self.assertIn("uniqueWalkers<2",S)
        self.assertIn("allPhysical",S)
        self.assertIn("G5_REAL_STUDIO_LOCAL_EVIDENCE",S)
        self.assertIn("outbound_and_return=PASS",S)
        self.assertIn('emit("GATE",', S) # actual receipt marker is composed at runtime

    def test_no_trusting_user_network_remote(self):
        for name in ("RemoteEvent","OnServerEvent","FireServer","DataStoreService",
                     "MarketplaceService","TeleportService","SetNetworkOwner",
                     "workspace.Gravity","Humanoid:MoveTo","PublishAsync"):
            self.assertNotIn(name,S)

    def test_bounded_read_only_teleport_defense(self):
        self.assertIn("Plan.MAX_SPEED_STUDS_PER_SEC",S)
        self.assertIn("SUSPECT_MOVEMENT",S)
        self.assertIn("action=RESET_ROUTE_CHECKPOINTS",S)
        self.assertIn("lastByPlayer[player]",S)
        self.assertIn("PlayerRemoving",S)
        self.assertIn("CharacterRemoving:Connect",S)
        self.assertIn("Plan.LIMIT_PER_ROUTE_SECONDS",S)
        self.assertIn("ROUTE_TIMEOUT",S)
        self.assertIn("routeStartedAtByPlayer[player]",S)
        self.assertIn("Connect(function(dt)",S)

    def test_original_modules_reused_not_reimplemented(self):
        tree=PROJECT["tree"]["ServerScriptService"]
        self.assertEqual(set(tree),{"WorldLinkScene","WorldLinkRoutes",
                                    "G5StudioCheckpointPlan","WorldG5StudioEvidence","$className"})
        self.assertTrue(tree["WorldLinkScene"]["$path"].startswith("../P0D-WORLD-LINK-G5"))
        self.assertTrue(tree["WorldLinkRoutes"]["$path"].startswith("../P0D-WORLD-LINK-G5"))
        self.assertEqual(tree["G5StudioCheckpointPlan"]["$path"],
                         "src/G5StudioCheckpointPlan.luau")

    def test_negative_auto_enabled_detected(self):
        def guard(text):return "ENABLE_G5_STUDIO_EVIDENCE = false" in text
        self.assertTrue(guard(S))
        self.assertFalse(guard(S.replace("ENABLE_G5_STUDIO_EVIDENCE = false",
                                          "ENABLE_G5_STUDIO_EVIDENCE = true",1)))

    def test_negative_no_2clients_detected(self):
        def guard(text):return "activeClientCount()<2" in text
        self.assertTrue(guard(S))
        self.assertFalse(guard(S.replace("activeClientCount()<2","activeClientCount()<1",1)))

    def test_native_plan_rejects_invalid_input(self):
        self.assertIn("x==x",P)
        self.assertIn("stage % 1 ~= 0",P)
        self.assertIn("radius*current.radius",P)

if __name__=="__main__":
    unittest.main()
