from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]

class StaticContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=(ROOT/'src/LigardoVisualPolicy.luau').read_text()
        cls.builder=(ROOT/'src/LigardoVisualBuilder.luau').read_text()
        cls.controller=(ROOT/'src/LigardoClientController.luau').read_text()

    def test_client_only_remote_direction(self):
        self.assertIn('.OnClientEvent:Connect',self.controller)
        self.assertNotIn('.OnServerEvent',self.controller)
    def test_no_new_server_scheduler(self):
        for script in [self.policy,self.builder,self.controller]:
            self.assertNotIn('DataStoreService',script)
            self.assertNotIn('MarketplaceService',script)
            self.assertNotIn('TeleportService',script)
    def test_no_damage(self):
        self.assertNotIn('TakeDamage(',self.builder+self.controller)
        self.assertNotIn('Humanoid.Health',self.builder+self.controller)
    def test_no_server_spawn(self):
        self.assertNotIn('ServerScriptService',self.builder+self.controller)
        self.assertNotIn('FireServer(',self.builder+self.controller)
    def test_anchored(self):
        self.assertIn('p.Anchored = true',self.builder)
    def test_noncolliding(self):
        self.assertIn('p.CanCollide = false',self.builder)
    def test_cannot_query(self):
        self.assertIn('p.CanQuery = false',self.builder)
    def test_cannot_touch(self):
        self.assertIn('p.CanTouch = false',self.builder)
    def test_client_instance_cap(self):
        self.assertIn('lowDetail and 4 or 6',self.builder)
        self.assertIn('lowDetail and 2 or 4',self.builder)
    def test_low_motion(self):
        self.assertIn('reducedMotion',self.builder)
    def test_cleanup(self):
        self.assertIn('view.model:Destroy()',self.builder)
        self.assertIn('conn.message:Disconnect()',self.controller)
        self.assertIn('conn.frame:Disconnect()',self.controller)
    def test_stage_gating(self):
        self.assertIn('p.stage ~= 2 and p.stage ~= 4',self.policy)
    def test_event_gating(self):
        self.assertIn('p.boss ~= "LIGARDO"',self.policy)
    def test_seq_gating(self):
        self.assertIn('p.seq <= s.lastSeq',self.policy)
    def test_no_arbitrary_teleport(self):
        self.assertNotIn(':PivotTo(',self.builder+self.controller)
        self.assertNotIn('BodyVelocity',self.builder+self.controller)
    def test_bound_update_frequency(self):
        self.assertIn('accumulator < 0.08',self.controller)
    def test_position_guard(self):
        self.assertIn('math.abs(p.X) > 4096',self.controller)
    def test_close_visual_only(self):
        self.assertIn('Policy.close(state)',self.controller)
        self.assertNotIn(':Destroy()',self.controller)
    def test_single_event_policy(self):
        self.assertIn('ALREADY_USED_THIS_ROUND',self.policy)
    def test_no_external_asset(self):
        self.assertNotIn('InsertService',self.builder)
        self.assertNotIn('HttpService',self.builder)
    def test_readme_scope_warning(self):
        self.assertIn('NOT gameplay AI', (ROOT/'README.md').read_text())

if __name__ == '__main__': unittest.main()
