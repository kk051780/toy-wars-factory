#!/usr/bin/env python3
"""Source safety plus genuine official RC57 artifact regression. No engine claim."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"src/WCS_Integrated.server.luau").read_text("utf8")
spec=importlib.util.spec_from_file_location("wcs_rc57_builder",ROOT/"tools/build_from_rc57.py")
B=importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
START="-- P0D World-Character Synergy F01+C01 (S2+ isolated candidate)"
END='world:SetAttribute("WCS_Stage", "SOURCE_CANDIDATE_ONLY")'

class WCSSafety(unittest.TestCase):
    def test_exact_new_source(self): self.assertEqual(B.blob(SOURCE.encode()),B.SOURCE_GIT_BLOB)
    def test_exact_author_gate_fix(self):
        i=SOURCE.index(START);j=SOURCE.index(END,i)+len(END)
        self.assertEqual(B.blob((SOURCE[i:j]+"\n").encode()),B.SAFE_AUTHOR_BLOB)
    def test_gate_close_zone_not_whole_bridge(self):
        self.assertIn("local function playerIsInGateClosureZone()",SOURCE)
        self.assertIn("math.abs(localPoint.X) <= 3.5",SOURCE)
        self.assertIn("math.abs(localPoint.Z) <= 8",SOURCE)
        self.assertNotIn("playerIsOnBridge()",SOURCE)
    def test_actual_close_begins_cooldown(self):
        self.assertIn("nextOpenAllowed = os.clock() + REOPEN_COOLDOWN",SOURCE)
        self.assertIn("if gateOpen and not open then",SOURCE)
    def test_original_studio_only_toggle_and_arena(self):
        for s in ['if not RunService:IsStudio() then','ServerStorage:GetAttribute("P0D_RC_ENABLE_WCS_F01_C01")==false','anchor.CFrame=CFrame.new(0,32,-23)','sky:WaitForChild("SKY_WALKWAY",12)']:
            self.assertIn(s,SOURCE)
    def test_equal_routes_safe_detour_two_npcs(self):
        for s in ('CANYON_ENTRY_RED','CANYON_ENTRY_BLUE','AlwaysOpenSafeRoute','makeMole("MoguronWest", -32)','makeMole("MoguronEast", 32)'):
            self.assertIn(s,SOURCE)
    def test_not_second_game_owner(self):
        for s in ("GetDataStore(","UpdateAsync(","OnServerEvent:Connect(","FireServer(","TakeDamage(","MarketplaceService"):
            self.assertNotIn(s,SOURCE)
    def test_authentic_rc57_plus_one(self):
        f=os.environ.get("P0D_RC57_ARTIFACT_ZIP")
        if not f:self.skipTest("Set P0D_RC57_ARTIFACT_ZIP; not an actual artifact validation")
        with tempfile.TemporaryDirectory() as temp:
            place=Path(temp)/"private58.rbxlx";receipt=Path(temp)/"receipt.json"
            B.build(Path(f),place,receipt)
            self.assertTrue(place.is_file())
            self.assertIn('"new_script_count": 58',receipt.read_text("utf8"))
    def test_corrupt_artifact_must_fail_closed(self):
        f=os.environ.get("P0D_RC57_ARTIFACT_ZIP")
        if not f:self.skipTest("Set P0D_RC57_ARTIFACT_ZIP")
        with tempfile.TemporaryDirectory() as temp:
            corrupt=Path(temp)/"wrong.zip"
            payload=Path(f).read_bytes()
            corrupt.write_bytes(payload[:-1]+bytes([payload[-1]^1]))
            with self.assertRaisesRegex(ValueError,"SHA_MISMATCH"):
                B.build(corrupt,Path(temp)/"bad.rbxlx",Path(temp)/"bad.json")
            self.assertFalse((Path(temp)/"bad.rbxlx").exists())

if __name__=="__main__":unittest.main()
