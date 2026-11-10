import unittest,re,pathlib
BASE=pathlib.Path(__file__).parents[1]/'luau'
class LuauStaticTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.policy=(BASE/'GoroganVisualPolicy.luau').read_text()
  cls.prefab=(BASE/'GoroganVisualPrefab.luau').read_text()
  cls.adapter=(BASE/'GoroganClientAdapter.client.luau').read_text()
 def test_modules_exist(self):self.assertEqual(len(list(BASE.glob('*.luau'))),3)
 def test_model_client_only(self):self.assertIn('Model',self.prefab);self.assertIn('LocalScript',self.adapter)
 def test_all_anchored(self):self.assertIn('part.Anchored = true',self.prefab)
 def test_no_physics_collision(self):self.assertIn('part.CanCollide = false',self.prefab)
 def test_no_touch_events(self):self.assertIn('part.CanTouch = false',self.prefab)
 def test_no_queries(self):self.assertIn('part.CanQuery = false',self.prefab)
 def test_no_forced_camera(self):self.assertNotIn('CurrentCamera',self.prefab+self.adapter)
 def test_no_damage(self):self.assertNotIn('TakeDamage(',self.policy+self.prefab+self.adapter)
 def test_no_server_remote(self):self.assertNotIn(':FireServer(',self.policy+self.prefab+self.adapter)
 def test_no_spawn_scheduling(self):self.assertNotIn('math.random(',self.policy+self.prefab+self.adapter)
 def test_no_buy(self):self.assertNotIn('MarketplaceService',self.policy+self.prefab+self.adapter)
 def test_no_save(self):self.assertNotIn('DataStoreService',self.policy+self.prefab+self.adapter)
 def test_no_humanoid(self):self.assertNotIn('Instance.new("Humanoid")',self.prefab)
 def test_no_unauthorized_sfx(self):self.assertNotIn('rbxassetid:',self.prefab+self.adapter)
 def test_reduced_motion(self):self.assertIn('TRAP_ReducedMotion',self.adapter)
 def test_low_detail(self):self.assertIn('TRAP_LowDetail',self.adapter)
 def test_local_lifecycle(self):self.assertIn('script.Destroying:Connect',self.adapter)
 def test_throttle(self):self.assertIn('tickBudget < .1',self.adapter)
 def test_server_remote_condition(self):self.assertIn('TRAP_BossVisualEvent',self.adapter)
 def test_stomp_limit(self):self.assertIn('MAX_STOMP_COUNT = 3',self.policy)
 def test_boss_once(self):self.assertIn('state.seenStart = true',self.policy)
 def test_visual_ttl(self):self.assertIn('MAX_LIFETIME = 14',self.policy)
 def test_moss_core(self):self.assertIn('GlowingChestRune',self.prefab);self.assertIn('MossCrown',self.prefab)
 def test_root_pivot(self):self.assertIn('model.PrimaryPart = root',self.prefab)
 def test_isolated_names(self):self.assertIn('Gorogan_ClientVisualOnly',self.prefab)
 def test_no_real_combat(self):
  src=self.policy+self.prefab+self.adapter
  self.assertNotIn('Humanoid.Health',src);self.assertNotIn('WalkSpeed =',src)
if __name__=='__main__':unittest.main()
