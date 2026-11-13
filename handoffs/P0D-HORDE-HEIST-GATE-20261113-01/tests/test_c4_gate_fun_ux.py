"""C4 actual gate runtime renderer/telemetry and rollback invariants.

These are SOURCE checks, not claims of Roblox Studio simulation.
"""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
RUNTIME=(ROOT/"src/GateLiveRuntimeUXC4.luau").read_text("utf-8")
BUILDER=(ROOT/"tools/build_48_c4_gameplay_audit.py").read_text("utf-8")

class GateUXSafety(unittest.TestCase):
    def test_source_matches_real_author_runtime(self):
        self.assertIn('ORIGINAL_GATE_RUNTIME_GITBLOB="473d5c5e0bd24e2e663b2f22076cbae24a3e9030"',BUILDER)
    def test_gating_depends_on_existing_world_route_mount(self):
        self.assertIn("if route then",RUNTIME)
        self.assertIn("self.objective=createObjectiveBillboard(route.model)",RUNTIME)
        self.assertIn("GateRouteOverlay.create(self.arena,GateVisual)",RUNTIME)
    def test_late_spawn_through_existing_source_does_not_fake_a_gate(self):
        self.assertIn('SEA_SOURCE_NOT_READY',RUNTIME)
        self.assertIn("self.missingSceneNoted=true",RUNTIME)
        self.assertIn("if self.route==nil and safeToMount()",RUNTIME)
    def test_human_sign_has_limited_distance(self):
        self.assertIn('MaxDistance=145',RUNTIME)
        self.assertIn('TextWrapped=true',RUNTIME)
        self.assertIn('精鋭を倒そう',RUNTIME)
        self.assertIn('両チーム',RUNTIME) if '両チーム' in RUNTIME else self.assertIn('赤青どちらも通れる',RUNTIME)
    def test_armed_to_warning_to_open_to_wait_to_closed_message(self):
        for ph in ('phase=="WARNING"','phase=="OPEN"','phase=="WAIT_CLEAR"','phase=="CLOSED"','phase=="ROUND_END"'):
            self.assertIn(ph,RUNTIME)
    def test_server_only_actual_elite_ko_logged_once(self):
        self.assertIn("EliteKOBridge.didConfirmEliteKO(horde,receipt)",RUNTIME)
        self.assertIn("if accepted then",RUNTIME)
        self.assertIn("ELITE_KO_CONFIRMED",RUNTIME)
        self.assertNotIn("FireServer",RUNTIME)
    def test_only_one_print_per_phase(self):
        self.assertIn("if self.lastPhase~=snapshot.phase then",RUNTIME)
        self.assertIn("self.lastPhase=snapshot.phase",RUNTIME)
        self.assertIn("self.lastPhase=nil",RUNTIME)
    def test_expiry_occupancy_has_ten_stud_margin(self):
        self.assertIn("part.Size+Vector3.new(4,4,20)",RUNTIME)
        self.assertNotIn("part.Size+Vector3.new(4,4,4)",RUNTIME)
        self.assertIn("workspace:GetPartBoundsInBox",RUNTIME)
    def test_round_ended_door_stays_passable_and_honest(self):
        self.assertIn('GateRouteOverlay.render(self.route,GateVisual,{phase="OPEN",passable=true})',RUNTIME)
        self.assertIn('updateObjective(self.objective,"ROUND_END")',RUNTIME)
        self.assertIn("ROUND_END_SAFE_OPEN",RUNTIME)
    def test_no_second_authority_or_loop(self):
        for banned in ("RemoteEvent","OnServerEvent","DataStoreService","MarketplaceService",
                       "task.spawn","while true","TakeDamage"):
            self.assertNotIn(banned,RUNTIME)
    def test_missing_geometry_secrecy_guard(self):
        self.assertIn("RunService:IsStudio()",RUNTIME)
        self.assertNotIn('workspace:FindFirstChild("StaleGate")',RUNTIME)
    def test_no_second_game_during_build(self):
        self.assertIn('assert len(after)==48',BUILDER)
        self.assertIn('assert changed==["server/GateLiveRuntime.luau"]',BUILDER)
        self.assertIn('assert sum(k.endswith(".server.luau") for k in after)==2',BUILDER)
        self.assertIn('assert game.count("remote.OnServerEvent:Connect(")==1',BUILDER)
    def test_protected_inputs_only(self):
        self.assertIn('assert not dest.exists()',BUILDER)
        self.assertIn('assert not base.exists()',BUILDER)
        self.assertIn('original_b42v7',BUILDER.lower())
    def test_document_engine_not_tested(self):
        self.assertIn('"owner_studio_real_run":"NOT_TESTED"',BUILDER)
        self.assertIn('"no_official_rc":True',BUILDER)

if __name__=="__main__":
    unittest.main()
