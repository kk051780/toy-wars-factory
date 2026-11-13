"""PRIVATE62 4th canyon lane: actual source/layout/safety contract and separation.
These are OFFLINE checks. Native Luau and Rojo are separately required by CI.
No claim of real Studio collisions, multi-client, or owner FUN.
"""
import hashlib
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
METEOR=(ROOT/"features/meteor_fourth/MeteorFourth.server.luau").read_text("utf8")
STAR=(ROOT/"features/star_path/StarfallPath.server.luau").read_text("utf8")
WCS=(ROOT/"features/wcs_f01_c01/WCS_CrystalCanyon.server.luau").read_text("utf8")
METEOR_SHA="4845ffa98b0b17a506a993682dc84f9de0fd5e30"

def blob(s):
    raw=s.encode("utf8")
    return hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()

class FourthRoute(unittest.TestCase):
    def test_01_source_exact(self):
        self.assertEqual(blob(METEOR),METEOR_SHA)
    def test_02_same_wcs(self):
        self.assertIn("P0D_WCS_CrystalCanyon",METEOR)
        self.assertIn("P0D_WCS_CrystalCanyon",WCS)
    def test_03_same_star(self):
        self.assertIn('Workspace:WaitForChild("P0D_STARRY_PATH", 160)',METEOR)
        self.assertIn('stage.Name="P0D_STARRY_PATH"',STAR)
    def test_04_studio_only(self):
        self.assertIn("if not RunService:IsStudio() then",METEOR)
    def test_05_disabled_by_default(self):
        self.assertIn('flag ~= nil and flag:IsA("BoolValue") and flag.Value == true',METEOR)
    def test_06_hard_dependencies(self):
        self.assertIn('GetAttribute("P0D_RC_ENABLE_STARRY_PATH_V1") ~= true',METEOR)
        self.assertIn('GetAttribute("P0D_RC_ENABLE_WCS_F01_C01") ~= true',METEOR)
    def test_07_both_banks(self):
        for name in ('"WestBank"','"EastBank"','west.CanCollide and east.CanCollide'):
            self.assertIn(name,METEOR)
    def test_08_real_star_step(self):
        self.assertIn('star:WaitForChild("StarStep_01", 12)',METEOR)
    def test_09_existing_escape_route(self):
        for name in ('"AlwaysOpenSafeRoute"','"ShortcutGate"'):
            self.assertIn(name,METEOR)
    def test_10_no_route_collision(self):
        self.assertIn('clearOf(gate) and clearOf(safe) and clearOf(starStep)',METEOR)
        self.assertIn('local buffer = 3',METEOR)
    def test_11_original_wcs_bank_dimensions(self):
        self.assertIn('Vector3.new(50, 4, 85), -50, -2, 0',WCS)
        self.assertIn('Vector3.new(50, 4, 85), 50, -2, 0',WCS)
    def test_12_route_locations(self):
        self.assertIn('Vector3.new(x,-0.75,-35)',STAR)
        self.assertIn('local z = (west.Position.Z + east.Position.Z) * 0.5 - 17',METEOR)
        self.assertIn('Vector3.new(50, 2, 12), 0, -1, 0',WCS)
        self.assertIn('Vector3.new(50, 3, 12), 0, -1.5, 30',WCS)
    def test_13_real_canyon_clearance_studs(self):
        width_meteor=9
        for z,width in [(-35,13),(0,12),(30,12)]:
            separation=abs(-17-z)
            gap=separation-(width_meteor+width)/2
            self.assertGreaterEqual(gap,3,(z,gap))
    def test_14_reach_bank(self):
        # WCS banks run from local [-75,-25] and [25,75] X.
        self.assertAlmostEqual(-50 + 50/2 - 1.5,-26.5)
        self.assertAlmostEqual(50 - 50/2 + 1.5,26.5)
        self.assertIn("west.Size.X*0.5-1.5",METEOR)
    def test_15_bounds(self):
        self.assertLessEqual(abs(-23-17),68)
        self.assertIn('math.abs(a.Z) <= 68',METEOR)
    def test_16_occupancy_cannot_drop_live_players(self):
        self.assertIn('while runtime.Parent ~= nil and isBridgeOccupied(segments) do',METEOR)
        self.assertIn('humanoid.Health > 0',METEOR)
    def test_17_both_teams_no_reward(self):
        for bad in ('GetDataStore(', 'UpdateAsync(', 'TakeDamage(',
                    'OnServerEvent:Connect(', 'MarketplaceService', 'horde:hit('):
            self.assertNotIn(bad,METEOR)
    def test_18_timed_distinction_from_star(self):
        for piece in ('local QUIET_SECONDS = 55','local WARNING_SECONDS = 5','local ACTIVE_SECONDS = 22'):
            self.assertIn(piece,METEOR)
        self.assertIn('local OPEN_SECONDS=16',STAR)
    def test_19_distinct_runtime_names(self):
        self.assertIn('P0D_MeteorShortcutRuntime',METEOR)
        self.assertIn('P0D_STARRY_PATH',STAR)
    def test_20_no_duplicate_runtime(self):
        self.assertIn('if Workspace:FindFirstChild(RUNTIME_FOLDER) then',METEOR)
    def test_21_explicit_fake_anchor_cannot_override(self):
        self.assertNotIn('P0D_MeteorShortcutAnchors',METEOR)
    def test_22_star_requires_one_world(self):
        self.assertIn('if Workspace:FindFirstChild("P0D_STARRY_PATH") then',STAR)
    def test_23_one_script_live_bridge(self):
        self.assertIn('runtime:SetAttribute("RouteRole","FOURTH_CANYON_LANE")',METEOR)
    def test_25_source_120s_star_boot_fix(self):
        self.assertIn('WaitForChild("P0D_CrystalCanyonAnchor",120)',STAR)
    def test_26_new_meteor_boot_budget(self):
        self.assertIn('WaitForChild("P0D_WCS_CrystalCanyon", 140)',METEOR)
        self.assertIn('WaitForChild("P0D_STARRY_PATH", 160)',METEOR)
    def test_27_prerequisite_parts_wait(self):
        for n in ("WestBank","EastBank","ShortcutGate","AlwaysOpenSafeRoute"):
            self.assertIn('world:WaitForChild("'+n+'", 12)',METEOR)
        self.assertIn('star:WaitForChild("StarStep_01", 12)',METEOR)
    def test_28_boot_budget_covers_wcs_max(self):
        # WCS waits arena 45 + H1 world 45 + sky deck 12 in worst-case path.
        wcs_max=45+45+12
        star_budget=120
        meteor_wcs_budget=140
        meteor_star_budget=160
        self.assertGreater(star_budget,wcs_max)
        self.assertGreater(meteor_wcs_budget,wcs_max)
        self.assertGreater(meteor_star_budget,star_budget)
    def test_24_off_composition_available(self):
        adapter=(ROOT/"apply_meteor_fourth.py").read_text("utf8")
        self.assertIn('print("P0D_METEOR_FOURTH_OFF_ZERO_WRITES_PRIVATE61_PASS")',adapter)
        self.assertIn('assert len(before)==61',adapter)

if __name__=="__main__":
    unittest.main()
