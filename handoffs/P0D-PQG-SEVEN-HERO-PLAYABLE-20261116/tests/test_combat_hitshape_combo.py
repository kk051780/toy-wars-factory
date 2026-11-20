"""SOURCE-only contract that shape differences and authentic KO momentum stay fair."""
from pathlib import Path
import unittest
R=Path(__file__).resolve().parents[1]
G=(R/"EGGRUMBLE_AttackGeometry.luau").read_text(encoding="utf-8")
H=(R/"EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8")
S=(R/"EGGRUMBLE_SwarmCombat.luau").read_text(encoding="utf-8")
F=(R/"EGGRUMBLE_SkillFX.luau").read_text(encoding="utf-8")

class HitGeometryAndKOCombo(unittest.TestCase):
 def test_shape_is_real_hit_geometry_for_all_actor_types(self):
  self.assertIn("function Geometry.allowed(",G)
  self.assertIn("LANE={RAIL=true,LANCE=true}",G)
  self.assertIn("BLADE=true",G)
  self.assertIn("local forward=deltaX*ux+deltaZ*uz",G)
  self.assertIn("if forward<1 or forward>range+radius then return false end",G)
  self.assertIn("if LANE[shape] then",G)
  self.assertIn("if cross<=laneWidth",G) if "if cross<=laneWidth" in G else self.assertIn("return cross<=laneWidth",G)
  self.assertGreaterEqual(H.count("AttackGeometry.allowed("),4)
  self.assertIn("AttackGeometry.allowed(origin,at,m.PrimaryPart.Position,radius,shape)",S)
  self.assertIn('local AttackGeometry=require(script.Parent:WaitForChild("EGGRUMBLE_AttackGeometry"))',H)
 def test_combo_is_from_real_enemy_deaths_only_and_cap_is_small(self):
  self.assertIn("h.Died:Connect(function()",S)
  died=S.index("h.Died:Connect(function()")
  self.assertIn("credit(id)",S[died:died+350])
  self.assertIn("comboById[id]=combo",S)
  self.assertIn('p:SetAttribute("EGGRUMBLE_Combo",combo)',S)
  self.assertIn('p:SetAttribute("EGGRUMBLE_BestCombo",bestCombo[id])',S)
  self.assertIn("if combo%25==0 then",S)
  self.assertIn('txt.Text=tostring(combo).." COMBO!"',S)
  self.assertIn("currentCombo>=60 then 1.12 elseif currentCombo>=20 then 1.06 else 1",S)
  self.assertIn("damage*bonus",S)
  self.assertNotIn("damage*bonus",H)
 def test_no_large_blocking_hud_or_unbounded_particle_spam(self):
  self.assertIn('gui.AlwaysOnTop=false',S)
  self.assertIn('Debris:AddItem(gui,.95)',S)
  self.assertIn("ACTIVE_LIMIT=72",F)
  self.assertIn("MAX_NEW_PER_PULSE=6",F)
  self.assertNotIn("PointLight",F)
  for text in (S,G,H,F):
   self.assertNotIn("MarketplaceService",text)
   self.assertNotIn("DataStoreService",text)
if __name__=="__main__":
 unittest.main()
