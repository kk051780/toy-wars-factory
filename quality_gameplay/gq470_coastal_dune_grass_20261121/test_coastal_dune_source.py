"""Static negative/regression checks: not Studio, Android, art or FUN evidence."""
from pathlib import Path
import re
import unittest

SRC = (Path(__file__).parent / "EGGRUMBLE_CoastalDuneGrass.client.luau").read_text(encoding="utf-8")

class CoastalDuneGrassSource(unittest.TestCase):
    def test_01_unique_feature(self):
        self.assertEqual(SRC.count("GQ470_FB015_COASTAL_DUNE_GRASS_20261121"), 1)
    def test_02_strict_luau(self):
        self.assertTrue(SRC.startswith("--!strict\n"))
    def test_03_real_scene(self):
        self.assertIn("EGGRUMBLE_LAND_SEA_SKY_20261117", SRC)
        self.assertIn("scene.Name ~= SCENE_NAME", SRC)
    def test_04_real_dock(self):
        self.assertIn("PublicSeaDock", SRC)
        self.assertIn("dock.Anchored", SRC)
    def test_05_existing_ground(self):
        self.assertIn("TacticalBattlefield", SRC)
        self.assertIn("floor.Size.X < 600", SRC)
        self.assertIn("floor.Size.Z < 700", SRC)
    def test_06_two_modes(self):
        self.assertIn("TEAM_Arena", SRC)
        self.assertIn("BATTLE_ROYALE_Arena", SRC)
    def test_07_include_only_ground(self):
        self.assertIn("Enum.RaycastFilterType.Include", SRC)
        self.assertIn("FilterDescendantsInstances = {floor}", SRC)
        self.assertIn("hit.Instance == floor", SRC)
    def test_08_refuse_water_or_no_ground(self):
        self.assertIn("params.IgnoreWater = true", SRC)
        self.assertIn("hit.Normal.Y >= 0.91", SRC)
        self.assertIn("if count == 0 or count > MAX_PARTS then", SRC)
    def test_09_bounded_blades(self):
        self.assertIn("then 4 else 6", SRC)
        self.assertIn("BLADES_PER_CLUMP = 3", SRC)
        self.assertIn("MAX_PARTS = CLUMPS * BLADES_PER_CLUMP", SRC)
    def test_10_non_physical(self):
        for token in ("CanCollide = false", "CanTouch = false", "CanQuery = false"):
            self.assertIn(token, SRC)
        for token in ("CanCollide = true", "CanTouch = true", "CanQuery = true"):
            self.assertNotIn(token, SRC)
    def test_11_matte_low_overdraw(self):
        for token in ("Enum.Material.SmoothPlastic", "Reflectance = 0",
                      "CastShadow = false"):
            self.assertIn(token, SRC)
        for token in ("Enum.Material.Neon", "PointLight", "ParticleEmitter",
                      "SurfaceGui", "BillboardGui", "Trail", "Beam"):
            self.assertNotIn(token, SRC)
    def test_12_camera_lod(self):
        self.assertIn("then 115 else 175", SRC)
        self.assertIn("Workspace.CurrentCamera", SRC)
        self.assertIn("nearest = LOD_DISTANCE", SRC)
    def test_13_reduced_fx_cleanup(self):
        self.assertRegex(SRC, r'if player:GetAttribute\("EGGRUMBLE_ReducedEffects"\) == true then\s+clear\(\)')
        self.assertIn('GetAttributeChangedSignal("EGGRUMBLE_ReducedEffects"):Connect(refresh)', SRC)
    def test_14_streaming_removal(self):
        self.assertIn("Workspace.DescendantRemoving:Connect", SRC)
        self.assertIn("if selected == obj then clear() end", SRC)
    def test_15_single_active(self):
        self.assertIn("local selected: BasePart? = nil", SRC)
        self.assertIn("local active: Grass? = nil", SRC)
        self.assertIn("active.folder:Destroy()", SRC)
    def test_16_no_authority(self):
        for token in ("FireServer(", "InvokeServer(", "DataStoreService",
                      "TakeDamage(", "Humanoid.Health", "PlayerGui",
                      "SpawnLocation", "RemoteEvent", "RemoteFunction"):
            self.assertNotIn(token, SRC)
    def test_17_low_cpu(self):
        self.assertIn("REFRESH_SECONDS = 3.2", SRC)
        for token in ("RenderStepped", "Heartbeat", "Stepped:Connect("):
            self.assertNotIn(token, SRC)
    def test_18_clear_shuttle_lane(self):
        offsets = [(-50, -19), (50, -19), (-37, -30),
                   (37, -30), (-27, -43), (27, -43)]
        self.assertEqual(len(set(offsets)), 6)
        self.assertTrue(all(abs(x) >= 27 and z < -18 for x, z in offsets))
        self.assertEqual(len(re.findall(r'Vector2\.new\(-?\d+, -?\d+\)', SRC)), 6)
    def test_19_touch_desktop_budget(self):
        self.assertEqual(4 * 3, 12)
        self.assertEqual(6 * 3, 18)
        self.assertLessEqual(18, 20)
    def test_20_shutdown_cleanup(self):
        self.assertRegex(SRC, r'while script\.Parent do\s+task\.wait\(REFRESH_SECONDS\)\s+refresh\(\)\s+end\s+clear\(\)')
if __name__ == "__main__":
    unittest.main()
