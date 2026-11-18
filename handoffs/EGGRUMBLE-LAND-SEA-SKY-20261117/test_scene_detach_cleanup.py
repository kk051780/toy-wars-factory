#!/usr/bin/env python3
"""Regress scene lifecycle cleanup without touching canonical31 gameplay."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

ROOT=Path(__file__).resolve().parent
SRC=(ROOT/"EGGRUMBLE_LandSeaSkyTraversal.server.luau").read_text(encoding="utf-8")
spec=importlib.util.spec_from_file_location("detach_native",ROOT/"make_scene_detach_native.py")
native=importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)

class SceneDetachTest(unittest.TestCase):
 def test_true_original_owner_remains_one(self):
  self.assertIn("if not RunService:IsStudio() then return end",SRC)
  self.assertNotIn('Instance.new("RemoteEvent")',SRC)
  self.assertIn('local MAX_CRAFT = 4',SRC)
  self.assertIn('local MAX_PARTS_PER_WORLD = 95',SRC)
  self.assertIn('local function emptyCraftLease(',SRC)
  self.assertIn("if not hum and v.lastPilot then",SRC)

 def test_disposal_reuses_single_cleanup_for_both_paths(self):
  self.assertEqual(SRC.count("local function retireScene(removeVisual)"),1)
  self.assertEqual(SRC.count("retireScene(true)"),1)
  self.assertEqual(SRC.count("retireScene(false)"),1)
  self.assertIn("if not active then return end -- idempotent",SRC)
  self.assertIn("world.Destroying:Connect(function() retireScene(false) end)",SRC)
  self.assertIn("if removeVisual and scene.Parent then scene:Destroy() end",SRC)
  for needle in ("entered:Disconnect()","exited:Disconnect()",
   "for player in pairs(combatConnections) do unwatchCombo(player) end",
   "table.clear(publicTravelAt)","scenes[world]=nil"):
   self.assertIn(needle,SRC)

 def test_detachment_is_checked_every_heartbeat(self):
  self.assertEqual(SRC.count("shouldRetireDetachedScene(\n"),1)
  self.assertIn("world:IsDescendantOf(Workspace),scene.Parent==world",SRC)
  self.assertNotIn("if not active or not world.Parent or not scene.Parent then",SRC)

 def test_actual_native_helper_source_bound_and_mutants(self):
  helper=native.actual_helper()
  self.assertIn("not sceneIsChild",helper)
  with TemporaryDirectory() as d:
   native.generate(Path(d))
   h=(Path(d)/"good.luau").read_text(encoding="utf-8")
   self.assertIn(helper,h)
   for i,p in enumerate(native.PREDICATES):
    x=(Path(d)/f"mutant{i}.luau").read_text(encoding="utf-8")
    self.assertNotIn(p,x)
    self.assertIn("HEALTHY_SCENE_RETAINS",x)

 def test_no_false_report_if_critical_guard_is_removed(self):
  for p in native.PREDICATES:
   with self.assertRaisesRegex(ValueError,"RED_DETACH_PREDICATE_DRIFT"):
    native.actual_helper(SRC.replace(p,"false",1))
  with self.assertRaisesRegex(ValueError,"RED_DETACH_NOT_WIRED_TO_HEARTBEAT"):
   native.actual_helper(SRC.replace("shouldRetireDetachedScene(\n","false(\n",1))

if __name__=="__main__":
 unittest.main()
