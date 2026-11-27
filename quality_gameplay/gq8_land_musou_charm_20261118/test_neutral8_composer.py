#!/usr/bin/env python3
"""Non-overlap and fail-closed source overlay tests for 8 *real* neutral rigs."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("neutral8",ROOT/"compose_neutral8_core36.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

SOURCE="""--!strict
local function soldier(parent:Instance,at:Vector3):Model
 local m=Instance.new("Model")
 m.Name="HordeSoldier";m:SetAttribute("EGGRUMBLE_Neutral",true);m.Parent=parent
 local root=piece(m,"HumanoidRootPart",at,Vector3.new(1,2,1),Color3.fromRGB(1,2,3))
 local head=piece(m,"Head",at,Vector3.new(1,1,1),Color3.fromRGB(1,2,3))
 piece(m,"Shield",at,Vector3.new(1,1,1),Color3.fromRGB(1,2,3))
 m.PrimaryPart=root
 local h=Instance.new("Humanoid");h.Parent=m
 return m
end
function Swarm.start(session:any)
 local function addEnemy(at:Vector3)
  local m=soldier(all,at)
 end
end
"""

class Neutral8Tests(unittest.TestCase):
    def test_8_real_archetypes_in_single_existing_actor(self):
        out=mod.transform(SOURCE)
        self.assertEqual(out.count('local function soldier('),1)
        self.assertEqual(out.count('local function addEnemy('),1)
        for species in mod.SPECIES:
            self.assertIn(species,out)
        self.assertIn('m:SetAttribute("EGGRUMBLE_Species",species)',out)
        self.assertIn('m:SetAttribute("EGGRUMBLE_NeutralId",actorId)',out)
        self.assertIn('nextNeutralActorId+=1',out)
        self.assertIn('local actorId="N"..tostring(nextNeutralActorId)',out)
        for marker in ("TakeDamage(","RemoteEvent","leaderstats","DataStoreService",
                       "session.botActors=","session.swarm="):
            self.assertEqual(out.count(marker),SOURCE.count(marker),marker)

    def test_repeated_overlay_is_red(self):
        with self.assertRaisesRegex(ValueError,"RED_DUPLICATE_NEUTRAL8"):
            mod.transform(mod.transform(SOURCE))

    def test_source_drift_is_red(self):
        changed=SOURCE.replace("local function soldier(parent:Instance,at:Vector3):Model","local function soldier(parent:Instance,at:Vector3,flag:boolean):Model")
        with self.assertRaisesRegex(ValueError,"RED_ORIGINAL_SWARM_SOURCE_CHANGED"):
            mod.transform(changed)

    def test_missing_sole_spawn_is_red(self):
        with self.assertRaisesRegex(ValueError,"RED_ORIGINAL_SWARM_SOURCE_CHANGED"):
            mod.transform(SOURCE.replace(" m.PrimaryPart=root"," m.PrimaryPart=body"))

    def test_stage_is_one_authority_not_8_spawners(self):
        out=mod.transform(SOURCE)
        self.assertEqual(out.count("local NEUTRAL_VISUALS="),1)
        self.assertIn('style=="GHOST"',out)
        self.assertIn('style=="SLIME"',out)
        self.assertIn('style=="SHIELD"',out)
        self.assertIn('style=="CAP"',out)
        self.assertIn('style=="SNOUT"',out)

if __name__=="__main__":
    unittest.main()
