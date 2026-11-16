"""No duplicate Game/Remote/Store, and source-only BUILDER scope checks."""
import json,re,subprocess,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
SRC=(HERE/"EGGRUMBLE_BuilderConstruction.luau").read_text(encoding="utf-8")
POL=(HERE/"EGGRUMBLE_BuilderPlacementPolicy.luau").read_text(encoding="utf-8")
class BuilderSourceTests(unittest.TestCase):
 def test_default_off(self):
  self.assertIn("Build.DEFAULT_ENABLED=false",SRC)
  self.assertIn('if serverEnabled~=true',SRC)
 def test_original_never_modified_by_own_module(self):
  self.assertNotIn('SetAttribute("EGGRUMBLE_Role"',SRC)
  self.assertNotRegex(SRC,r'Instance\.new\("(?:RemoteEvent|Script|LocalScript|ModuleScript|Humanoid)"\)')
 def test_unique_server_role_and_membership(self):
  for k in ["EGGRUMBLE_Role","BUILDER","EGGRUMBLE_QueuedMode","session.roster","session.rules.castles","session.rules.winner","owner.heldEggs"]:
   self.assertIn(k,SRC)
 def test_no_authority_fork(self):
  for k in ["DataStore","MarketplaceService","TakeDamage","SetAsync","PublishAsync"]:
   self.assertNotIn(k,SRC)
 def test_both_physical_constructions(self):
  for k in ['"WALL"','"BRIDGE"',"part.CanCollide=true","CFrame.lookAt","part.Parent=session.world"]:
   self.assertIn(k,SRC)
 def test_no_cross_arena_ray(self):
  for k in ["FilterType=Enum.RaycastFilterType.Include","FilterDescendantsInstances={session.world}","TacticalBattlefield"]:
   self.assertIn(k,SRC)
 def test_objective_and_collision_fence(self):
  for k in ["GetPartBoundsInRadius","GetPartBoundsInBox","OBSTACLE_OR_CONSTRUCT","OBJECTIVE_BLOCK","FIELD_BOUNDS","UNSAFE_SLOPE"]:
   self.assertIn(k,SRC)
 def test_bounded_lifetime_and_cleanup(self):
  for k in ["Policy.capacity","Policy.cooldown","task.delay(Policy.LIFETIME","function Build.clear","entry.part:Destroy()"]:
   self.assertIn(k,SRC)
 def test_runtime_limits(self):
  for k in ["MAX_PER_HERO=2","MAX_PER_SESSION=12","LIFETIME=9","WALL=13","BRIDGE=17"]:
   self.assertIn(k,POL)
 def test_native_scenarios_present(self):
  t=(HERE/"EGGRUMBLE_BuilderPlacementPolicy.spec.luau").read_text()
  self.assertGreaterEqual(len(re.findall(r'check\(',t)),25)
 def test_read_only_parent_diff(self):
  r=subprocess.run(["git","diff","--name-only","fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9","HEAD"],cwd=ROOT,text=True,capture_output=True)
  if r.returncode: self.skipTest("source-branch parent ref not present offline")
  for path in r.stdout.splitlines():
   self.assertTrue(path.startswith("quality_gameplay/v3_builder_construction_20261116/") or path==".github/workflows/p0d-gq-builder-wall-bridge.yml",path)
if __name__=="__main__": unittest.main()
