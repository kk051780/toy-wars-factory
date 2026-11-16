"""EGGRUMBLE seven-class balance and VFX contract, not a device FPS claim."""
import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
BAL=(ROOT/"EGGRUMBLE_CombatBalance.luau").read_text(encoding="utf-8")
HERO=(ROOT/"EGGRUMBLE_SevenRoleCombat.luau").read_text(encoding="utf-8")
FX=(ROOT/"EGGRUMBLE_SkillFX.luau").read_text(encoding="utf-8")
ROLES=("WARRIOR","MAGE","NINJA","TRAPPER","BUILDER","BEAST","ZOMBIE")
SKILL=re.compile(r'^  ([ABC])=\{damage=(\d+),reach=(\d+),radius=(\d+),cooldown=([.\d]+),shape="([A-Z_]+)",effect="([A-Z_0-9]+)"',re.M)

def profiles():
    found={}
    for role in ROLES:
        m=re.search(r'\n '+role+r'=\{(.*?)\n \},',BAL,re.S)
        if m is None:
            raise AssertionError(f"no complete profile for {role}")
        rows={}
        for slot,dmg,reach,radius,cd,shape,effect in SKILL.findall(m.group(1)):
            rows[slot]={"dmg":int(dmg),"reach":int(reach),"radius":int(radius),
                        "cd":float(cd),"shape":shape,"effect":effect}
        found[role]=rows
    return found

class CombatBalanceAndArtGate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.profiles=profiles()

    def test_all_21_actual_profiles_and_bounds(self):
        self.assertEqual(len(self.profiles),7)
        for role,row in self.profiles.items():
            with self.subTest(role=role):
                self.assertEqual(set(row),{"A","B","C"})
                for slot,spec in row.items():
                    self.assertGreaterEqual(spec["dmg"],20)
                    self.assertLessEqual(spec["dmg"],60)
                    self.assertLessEqual(spec["reach"],32)
                    self.assertGreaterEqual(spec["radius"],4)
                    self.assertLessEqual(spec["radius"],22)
                    self.assertGreaterEqual(spec["cd"],.6)
                    self.assertLessEqual(spec["cd"],18)
                    self.assertTrue(spec["effect"])
        self.assertIn("assert(count==21",BAL)
        self.assertIn("return Balance",BAL)

    def test_all_classes_genuinely_different_combat_tradeoffs(self):
        p=self.profiles
        self.assertEqual(len({(p[r]["A"]["dmg"],p[r]["A"]["reach"],
                               p[r]["A"]["radius"],p[r]["A"]["cd"]) for r in ROLES}),7)
        self.assertGreater(p["WARRIOR"]["A"]["dmg"]/p["WARRIOR"]["A"]["cd"]*1.25,
                           p["NINJA"]["A"]["dmg"]/p["NINJA"]["A"]["cd"])
        self.assertGreater(p["BUILDER"]["A"]["reach"],p["WARRIOR"]["A"]["reach"])
        self.assertLess(p["BUILDER"]["A"]["dmg"],p["WARRIOR"]["A"]["dmg"])
        self.assertGreaterEqual(p["MAGE"]["B"]["radius"],20)
        self.assertLessEqual(p["NINJA"]["A"]["reach"],10)
        self.assertEqual(p["TRAPPER"]["B"]["effect"],"SLOW_3S")
        self.assertEqual(p["BEAST"]["B"]["effect"],"GIANT_FEED")
        self.assertEqual(p["BEAST"]["C"]["effect"],"THREE_SPLITS")
        self.assertEqual(p["ZOMBIE"]["B"]["effect"],"SLOW_3S")
        for role in ROLES:
            self.assertGreater(p[role]["C"]["cd"],p[role]["A"]["cd"])

    def test_numbers_are_actually_used_for_hits_and_cooldowns(self):
        for token in ('CombatBalance=require(', 'CombatBalance.skill(role,slot)',
                      'local cd=spec.cooldown','local forward=distance or spec.reach',
                      'local area=radius or spec.radius',
                      'local amount=damage or spec.damage',
                      'secondaryEffect(session,p,root,char,center,area,spec.effect,spec.shape)',
                      'SkillFX.emit(session.world,role,slot,',
                      'AttackGeometry.allowed(root.Position,center,er.Position,range,shape)'):
            with self.subTest(token=token):
                self.assertIn(token,HERO)
        self.assertNotIn('local COOLDOWNS={A=.52,B=5.5,C=13}',HERO)

    def test_statuses_affect_hp_or_movement_not_just_vfx(self):
        for token in ('EGGRUMBLE_SlowUntil','h.WalkSpeed=math.max(',
                      'h:SetAttribute("EGGRUMBLE_BurnUntil"', 'h:TakeDamage(tick)',
                      'EGGRUMBLE_MarkedUntil','h:TakeDamage(damage*duel*mark)',
                      'EGGRUMBLE_GiantFeedUntil','EGGRUMBLE_KamiUntil',
                      'or not owner.alive'):
            with self.subTest(token=token):
                self.assertIn(token,HERO)
        self.assertIn('session.mode~="TEAM" or target.team~=state.team',HERO)

    def test_strong_unique_mobile_safe_vfx_grammar(self):
        for role in ROLES:
            self.assertIn(role+'=',FX)
        for token in ('ACTIVE_LIMIT=72','MAX_NEW_PER_PULSE=6',
                      'p.CanCollide=false','p.CanQuery=false','p.CastShadow=false',
                      'TweenService:Create(', 'ParticleEmitter',
                      'WarGod_FlyingSlash','Mage_CrystalStorm',
                      'Assassin_ShadowAfterimage','Esper_PsiOrbit',
                      'MadScientist_RailShot','Beast_FangClaw',
                      'CurseMaster_SoulFlame'):
            with self.subTest(token=token):
                self.assertIn(token,FX)
        self.assertNotIn("PointLight",FX)
        self.assertNotIn("MarketplaceService",FX+HERO+BAL)
        self.assertNotIn("DataStoreService",FX+HERO+BAL)

if __name__=="__main__":
    unittest.main()
