"""C5 never equates authored code or a nearby teleport with real engine gate PASS."""
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"src/OwnerGateRealPlayObserverC5.client.luau").read_text("utf8")
B=(ROOT/"tools/build_49_c5_owner_engine_observer.py").read_text("utf8")

class C5ActualOwnerQA(unittest.TestCase):
    def test_private_studio_only(self): self.assertIn('if not RunService:IsStudio() then return end',S)
    def test_real_server_snapshot_only(self):
        self.assertIn('originalRemote.OnClientEvent:Connect(',S)
        self.assertIn('packet.kind ~= "SNAPSHOT"',S)
        self.assertIn('packet.serial',S)
    def test_never_fabricate_server_request(self):
        for banned in ("FireServer(","InvokeServer(","OnServerEvent:Connect("):
            self.assertNotIn(banned,S)
    def test_cannot_mutate_gameplay(self):
        for banned in ('Instance.new(','DataStore','MarketplaceService','TakeDamage(',
                       'Humanoid:MoveTo','player:LoadCharacter','SetAsync(','UpdateAsync('):
            self.assertNotIn(banned,S)
    def test_source_matched_actual_world_and_gates(self):
        for x in ("TRAP_RAIDERS_S1","P0D_S2_NeutralShortcut_ReviewOnly",
            "RED_SHARED_SEA_GATE","BLUE_SHARED_SEA_GATE","PhysicalDoor"):
            self.assertIn(x,S)
    def test_no_early_mount_pass(self):
        self.assertIn("ACTIVE_12S_NO_PHYSICAL_SEA_GATES",S)
        self.assertIn("BOTH_PHYSICAL_GATE_PARTS_FOUND",S)
        self.assertIn("local doors = getDoorModels()",S)
    def test_real_open_physics_both_keys(self):
        self.assertIn("part.CanCollide == false and part.CanQuery == false",S)
        self.assertIn("BOTH_DOORS_ACTUALLY_NONCOLLIDING_NONQUERYING",S)
    def test_real_avatar_must_move_through_door(self):
        self.assertIn('part.CFrame:PointToObjectSpace(location)',S)
        self.assertIn("previous",S)
        self.assertIn("(position-previous).Magnitude <= 5.0",S)
        self.assertIn("started.side ~= currentSide",S)
        self.assertIn("REAL_AVATAR_CROSSED_OPEN_",S)
    def test_blocking_walls_are_not_a_gate_cross(self):
        self.assertIn('part.Size.X/2 - 0.65',S)
        self.assertIn('part.Size.Y/2 - 0.15',S)
        self.assertIn('math.abs(localPos.Z) > 7.0',S)
    def test_player_must_be_alive(self):
        self.assertIn('humanoid.Health <= 0',S)
        self.assertIn('HumanoidRootPart',S)
    def test_no_teleport_false_positive(self):
        self.assertIn("now-previousAt <= 0.35",S)
        self.assertIn("(position-previous).Magnitude <= 5.0",S)
        self.assertIn("visits = {} end",S)
    def test_egg_is_a_server_snapshot_not_claimed_score(self):
        self.assertIn('packet.carrying',S)
        self.assertIn('packet.eggId',S)
        self.assertIn('lastServerSnapshotAt <= 2.0',S)
        self.assertIn('serverEggSnapshotRecent=',S)
        for s in ('SCORE_CONFIRMED','DEPOSIT_CONFIRMED','XP_AWARDED'):
            self.assertNotIn(s,S)
    def test_state_restarted_at_round_and_respawn(self):
        self.assertIn("if epoch ~= packet.serial then",S)
        self.assertIn("resetObservations()",S)
        self.assertIn("if previousCharacter ~= character then",S)
    def test_no_closure_exploitable_live(self):
        self.assertNotIn('task.wait(',S)
        self.assertIn("if phase ~= \"ACTIVE\"",S)
    def test_byte_exact_unmodified_game_loop(self):
        self.assertIn('assert len(before)==48',B)
        self.assertIn('assert all(before[k]==now[k] for k in before)',B)
        self.assertIn('assert len(now)==49',B)
        self.assertIn('g.count(\'remote.OnServerEvent:Connect(\')==1',B)
    def test_no_owner_branch_overwrite(self):
        self.assertIn("C5_OUTPUT_EXISTS_REFUSE_OVERWRITE",B)
        self.assertIn('"owner_studio":"NOT_TESTED"',B)
        self.assertIn('"official_RC_adopted":False',B)

if __name__=="__main__":unittest.main()
