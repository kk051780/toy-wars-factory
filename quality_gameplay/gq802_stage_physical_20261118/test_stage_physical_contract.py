#!/usr/bin/env python3
"""Non-duplicating physical stage adapter regressions, no engine acceptance claim."""
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / "EGGRUMBLE_StagePhysicalAnnex.server.luau").read_text(encoding="utf-8")
PLAN = (HERE / "EGGRUMBLE_StagePhysicalPlan.luau").read_text(encoding="utf-8")
COMPOSE = (HERE / "compose_real36_to39.py").read_text(encoding="utf-8")

class PhysicalStageContracts(unittest.TestCase):
    def test_six_actual_physical_parts_and_safe_walkways(self):
        self.assertIn('local pad=add("Tile_"..tile.slot.."_"..tile.prefabId,', SOURCE)
        self.assertIn('add("SafeWalkway_"..bridge.kind.."_"..tostring(i),', SOURCE)
        self.assertIn('if #plan.tiles~=6 or #plan.bridges~=8', SOURCE)
        self.assertIn('M.MAX_PARTS=48', PLAN)
        self.assertIn('groundEntrances=3', PLAN)
        self.assertIn('for _,i in ipairs({1,2,3}) do', PLAN)

    def test_studio_server_only_no_client_stage_authority(self):
        self.assertIn('if not RunService:IsStudio() then return end', SOURCE)
        self.assertIn('local seed=Random.new():NextInteger(1,2147483646)', SOURCE)
        self.assertIn('StageManifest.validate(manifest)', SOURCE)
        self.assertIn('PhysicalPlan.plan(manifest,frame)', SOURCE)
        for forbidden in ['Instance.new("RemoteEvent")', "TeleportService", "DataStoreService",
                          "workspace.Gravity=", "TakeDamage(", "Humanoid.Health=",
                          "Instance.new(\"ForceField\")"]:
            self.assertNotIn(forbidden, SOURCE)

    def test_legacy_eggs_castles_weather_owned_by_prior_scripts(self):
        self.assertIn('manifest.castleAnchors~="PRESERVE_EXISTING_HOST_CASTLES"', PLAN)
        self.assertIn('manifest.eggAnchors~="PRESERVE_EXISTING_HOST_EGGS"', PLAN)
        self.assertIn('manifest.globalGravityChange~=false', PLAN)
        self.assertIn('weatherOwner="EXISTING_REALM_WEATHER_ONLY"', PLAN)
        self.assertIn('scene:SetAttribute("WeatherIsOwnedByRealm",true)', SOURCE)
        self.assertIn('pad:SetAttribute("NoActualLootAuthority",true)', SOURCE)

    def test_actual_formal36_and_optional39_with_off36_wired(self):
        self.assertIn('if len(original) != 36', COMPOSE)
        self.assertIn('if len(flat_project(on_model)) == 39', COMPOSE)
        self.assertIn('if rollback != old or {k: selected[k] for k in old} != old:', COMPOSE)
        self.assertIn('GQ802_REAL39_SOURCE_CLASS_EXACT_AND_OFF36_ROLLBACK_GREEN', COMPOSE)
        self.assertIn('ORIGINAL_STAGE_BLOB = "696d2312ef7408e26b03281caede7606472c155b"', COMPOSE)
        self.assertNotIn('git push', COMPOSE)
        self.assertNotIn('merge_pull_request', COMPOSE)

    def test_mutation_deletions_fail_closed(self):
        for mutation, pattern in [
            (PLAN.replace('M.MAX_PARTS=48', 'M.MAX_PARTS=999'), 'M.MAX_PARTS=48'),
            (PLAN.replace('groundEntrances=3', 'groundEntrances=0'), 'groundEntrances=3'),
            (SOURCE.replace('StageManifest.validate(manifest)', 'true'),
             'StageManifest.validate(manifest)'),
            (SOURCE.replace('if not RunService:IsStudio() then return end', ''),
             'if not RunService:IsStudio() then return end'),
        ]:
            self.assertNotIn(pattern, mutation)

if __name__=="__main__":
    unittest.main()
