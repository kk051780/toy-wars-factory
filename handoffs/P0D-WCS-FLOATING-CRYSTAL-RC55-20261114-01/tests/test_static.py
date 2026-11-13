#!/usr/bin/env python3
"""Reproducible source checks. Not Roblox-engine/physical gameplay certification.
Set P0D_RC55_ARTIFACT_ZIP to authenticate and rebuild the actual 56-source Place.
"""
from pathlib import Path
import importlib.util, math, os, tempfile, unittest
ROOT=Path(__file__).resolve().parents[1]
S=(ROOT/"src/WCS_Integrated.server.luau").read_text("utf8")
spec=importlib.util.spec_from_file_location("wcs_builder",ROOT/"tools/build_from_rc55.py")
B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)

class WCSNativeSourceGate(unittest.TestCase):
    def test_original_author_gitblob_retained(self):
        p=S.index("-- P0D World-Character Synergy F01+C01 (S2+ isolated candidate)")
        q=S.index('world:SetAttribute("WCS_Stage", "SOURCE_CANDIDATE_ONLY")',p)
        body=(S[p:q+len('world:SetAttribute("WCS_Stage", "SOURCE_CANDIDATE_ONLY")')]+"\n").encode("utf8")
        self.assertEqual(B.blob(body),B.ORIGINAL_AUTHOR_BLOB)
    def test_single_final_script_source_hash(self):
        self.assertEqual(B.blob(S.encode("utf8")),B.NEW_SOURCE_BLOB)
    def test_source_anchor_and_game_bounds(self):
        self.assertIn("anchor.CFrame=CFrame.new(0,32,-23)",S)
        self.assertIn("|Z|>76, |X|>130",S)
        self.assertTrue(abs(-23-42.5)<76)
        self.assertTrue(abs(-23+42.5)<76)
        self.assertLess(75,130)
    def test_equal_red_blue_ground_route(self):
        self.assertIn('makeRoute("CANYON_ENTRY_RED",Vector3.new(-30,16,18),Vector3.new(-55,31,-15)',S)
        self.assertIn('makeRoute("CANYON_ENTRY_BLUE",Vector3.new(30,16,18),Vector3.new(55,31,-15)',S)
        self.assertLess(15/math.hypot(25,33),0.55)
    def test_can_only_start_with_real_h1_sky_approach(self):
        self.assertIn('arena:WaitForChild("H1_FUN_WORLD",45)',S)
        self.assertIn('sky:WaitForChild("SKY_WALKWAY",12)',S)
    def test_studio_only_feature_off(self):
        self.assertIn("if not RunService:IsStudio() then",S)
        self.assertIn('ServerStorage:GetAttribute("P0D_RC_ENABLE_WCS_F01_C01")==false',S)
        self.assertIn('anchor:SetAttribute("P0DWorldOptIn",true)',S)
    def test_two_gates_and_open_routes(self):
        self.assertIn('makeMole("MoguronWest", -32)',S)
        self.assertIn('makeMole("MoguronEast", 32)',S)
        self.assertIn('"AlwaysOpenSafeRoute"',S)
        self.assertIn("OPEN_SECONDS = 14",S)
        self.assertIn("REOPEN_COOLDOWN = 4",S)
        self.assertIn("not playerIsOnBridge()",S)
    def test_no_secondary_game_authority(self):
        meaningful="\n".join(line.split("--",1)[0] for line in S.splitlines())
        for bad in ("UpdateAsync(", "GetDataStore(", "FireServer(", "OnServerEvent:Connect(",
                    "MarketplaceService", "TakeDamage(", "leaderstats", "PromptProductPurchase("):
            self.assertNotIn(bad, meaningful)
    def test_entrance_guardrails_and_no_teleport(self):
        self.assertIn('entries:SetAttribute("GuardRails",4)',S)
        self.assertIn("rail.CanCollide=true",S)
        self.assertNotIn("PivotTo(",S)
    def test_authentic_binary_optional(self):
        z=os.environ.get("P0D_RC55_ARTIFACT_ZIP")
        if not z:self.skipTest("Set P0D_RC55_ARTIFACT_ZIP for genuine binary build")
        with tempfile.TemporaryDirectory() as t:
            out=Path(t)/"trial.rbxlx"
            B.build(Path(z),out)
            self.assertEqual(B.sha(out.read_bytes()),B.EXPECTED_PRIVATE_SHA)
if __name__=="__main__":unittest.main()
