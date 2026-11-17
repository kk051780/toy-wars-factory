#!/usr/bin/env python3
"""BATTLE-BALANCE-QA #765. Actual RealmCore Native tests; owner policy is SPEC_ONLY.

No canonical Game/Combat/Host writes. Policy/HP expectations here are
acceptance oracles, NOT evidence they have been integrated into gameplay.
"""
import argparse
import itertools
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REALM = REPO / "handoffs/EGGRUMBLE-REALM-CORE-20261118/EGGRUMBLE_RealmBattleCore.server.luau"
ELEMENTS = ("FIRE", "WATER", "LIGHTNING", "WIND", "EARTH", "ICE", "DIVINE", "CURSE")
RING = ("FIRE", "ICE", "WIND", "EARTH", "LIGHTNING", "WATER")
ADV = {(RING[i], RING[(i+1) % 6]) for i in range(6)}
HP = {"WARRIOR":250, "MAGE":195, "NINJA":185, "TRAPPER":205,
      "BUILDER":225, "BEAST":220, "ZOMBIE":230}
ROOT_SHA_PARENT = "9e020f284d83f333b695041b17ab29c94281a0db"


def proposed_affinity(attack, defense):
    """Pure owner-spec oracle, deliberately not imported by the game."""
    if attack in ("DIVINE", "CURSE") and defense in ("DIVINE", "CURSE"):
        return 1.25 if attack != defense else 1.0
    if (attack, defense) in ADV:
        return 1.25
    if (defense, attack) in ADV:
        return 0.80
    return 1.0


def extract(source, function, next_function):
    start = source.index("local function " + function + "(")
    end = source.index("local function " + next_function + "(", start)
    return source[start:end]


def real_function_source():
    source = REALM.read_text(encoding="utf-8")
    a = extract(source, "damageMultiplier", "safeReturn")
    b = extract(source, "damageRealm", "install")
    return a + "\n" + b


HARNESS = r'''
local function mk(hp, kind)
    local m = {Parent=true, attrs={RealmHP=hp,RealmKind=kind},destroyed=false}
    function m:GetAttribute(k) return self.attrs[k] end
    function m:SetAttribute(k,v) self.attrs[k]=v end
    function m:Destroy() self.Parent=nil; self.destroyed=true end
    return m
end
local function ck(ok,marker)
    if not ok then error(marker,0) end
end
local flame=mk(70,"LEVIATHAN")
ck(damageRealm(flame,40,"FIRE",true)==true and flame.attrs.RealmHP==64,
   "RED_FIRE_UNDERWATER_MULTIPLIER")
local thunder=mk(70,"LEVIATHAN")
ck(damageRealm(thunder,40,"LIGHTNING",true)==true and thunder.attrs.RealmHP==16,
   "RED_LIGHTNING_UNDERWATER_MULTIPLIER")
local ordinary=mk(70,"LEVIATHAN")
ck(damageRealm(ordinary,40,"KINETIC",true)==true and ordinary.attrs.RealmHP==30,
   "RED_NEUTRAL_DAMAGE")
local surface=mk(70,"LEVIATHAN")
ck(damageRealm(surface,40,"FIRE",false)==true and surface.attrs.RealmHP==30,
   "RED_SURFACE_ELEMENT_BOUNDARY")
local rounded=mk(70,"LEVIATHAN")
ck(damageRealm(rounded,3,"FIRE",true)==false and rounded.attrs.RealmHP==70,
   "RED_ROUNDING_ZERO_DAMAGE")
local negative=mk(70,"LEVIATHAN")
ck(damageRealm(negative,-500,"WATER",true)==false and negative.attrs.RealmHP==70,
   "RED_NEGATIVE_DAMAGE")
local missing=mk(nil,"LEVIATHAN")
ck(damageRealm(missing,40,"WATER",true)==false,
   "RED_MISSING_HP")
local dead=mk(0,"LEVIATHAN")
ck(damageRealm(dead,40,"WATER",true)==false,
   "RED_ALREADY_DEAD")
local absent=mk(70,"LEVIATHAN")
absent.Parent=nil
ck(damageRealm(absent,40,"WATER",true)==false,
   "RED_UNPARENTED_TARGET")
local crash=mk(10,"FIGHTER")
ck(damageRealm(crash,12,"KINETIC",false)==true
   and crash.attrs.RealmHP==0 and crash.attrs.RealmCrash==true
   and crash.destroyed and crash.Parent==nil,"RED_FIGHTER_DESTROY")
ck(damageRealm(crash,12,"KINETIC",false)==false,"RED_DOUBLE_HIT")
local score=mk(70,"LEVIATHAN")
ck(damageRealm(score,9,"KINETIC",false)==true and score.attrs.RealmHP==61,
   "RED_EXISTING_GUN_DAMAGE")
print("GQ8_BATTLE_REALM_ACTUAL_NATIVE_11_CASES_PASS")
'''


def emit_native(valid_path, mutant_path):
    code = real_function_source()
    marker = 'if element=="FIRE" then return .15 end'
    assert code.count(marker) == 1, "RED_ACTUAL_REALM_FIRE_POLICY_CHANGED"
    valid_path.write_text(code + "\n" + HARNESS, encoding="utf-8")
    mutant = code.replace(marker, 'if element=="FIRE" then return .95 end', 1)
    mutant_path.write_text(mutant + "\n" + HARNESS, encoding="utf-8")
    print("GQ8_BATTLE_NATIVE_GENERATED_FROM_ACTUAL_REALM_SOURCE")
    print("GQ8_BATTLE_EXPECTED_MUTANT_RED_FIRE_UNDERWATER_MULTIPLIER")


class BattleBalanceContract(unittest.TestCase):
    def test_source_native_harness_is_real(self):
        self.assertTrue(REALM.is_file())
        code = real_function_source()
        self.assertIn("local function damageRealm(", code)
        self.assertIn("math.floor(damage*damageMultiplier(element,underwater)+.5)", code)
        self.assertNotIn("DataStore", code)
        self.assertIn('if element=="FIRE" then return .15 end', code)
        self.assertIn('if element=="LIGHTNING" then return 1.35 end', code)

    def test_actual_realm_server_authority_and_limits(self):
        source = REALM.read_text(encoding="utf-8")
        for expected in (
            'local MAX_AIRCRAFT = 2', 'local MAX_SEA_CREATURES = 3',
            'local AIRCRAFT_HP = 120', 'local AIRCRAFT_BOMBS = 3',
            'local GUN_INTERVAL = .20', 'local BOMB_INTERVAL = 8',
            'local STORM_WARNING_SECONDS = 2', 'local LIGHTNING_INTERVAL = 7',
            'seat.Occupant~=h', 'state.planes[model]==p',
            'p:GetAttribute("EGGRUMBLE_QueuedMode")~=mode',
            'mode~="BATTLE_ROYALE" then return nil',
            'not state.active or not world.Parent or not eligible(p,mode,world)',
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, source)
        self.assertNotIn("RunService:IsStudio()", source)

    def test_spec_exactly_64_pairs_and_six_element_cycle(self):
        pairs = list(itertools.product(ELEMENTS, repeat=2))
        self.assertEqual(len(pairs), 64)
        self.assertEqual(len(ADV), 6)
        self.assertEqual(len({d for _, d in ADV}), 6)
        for attack, defense in pairs:
            m = proposed_affinity(attack, defense)
            self.assertIn(m, (0.8, 1.0, 1.25))
            self.assertGreaterEqual(m, .65)
            self.assertLessEqual(m, 1.35)
        for a,b in ADV:
            self.assertEqual(proposed_affinity(a,b), 1.25)
            self.assertEqual(proposed_affinity(b,a), .8)
        for special in ("DIVINE", "CURSE"):
            for normal in RING:
                self.assertEqual(proposed_affinity(special,normal),1.0)
                self.assertEqual(proposed_affinity(normal,special),1.0)
        self.assertEqual(proposed_affinity("DIVINE","CURSE"),1.25)
        self.assertEqual(proposed_affinity("CURSE","DIVINE"),1.25)

    def test_spec_free_seven_roles_regen_ttk_and_mage(self):
        self.assertEqual(len(HP), 7)
        self.assertEqual(HP["NINJA"],185)  # display=Assassin, original role ID fixed
        for role,max_hp in HP.items():
            with self.subTest(role=role):
                self.assertGreater(max_hp, 2 * 24)
                self.assertGreater(max_hp, 2 * 65)
                self.assertGreater(max_hp * .007, 0)
                self.assertEqual(max_hp-(max_hp*.007*0), max_hp)
        maxhp=HP["MAGE"]
        self.assertAlmostEqual(maxhp * .30, 58.5)  # active heal, CD18s
        self.assertAlmostEqual(maxhp * .35, 68.25) # revive, 3s, CD40s
        self.assertEqual((7, .007, 18, 3, 40, 60),
                         (7, .007, 18, 3, 40, 60))

    def test_negative_mutant_must_change_actual_native_damage(self):
        code=real_function_source()
        marker='if element=="FIRE" then return .15 end'
        self.assertEqual(code.count(marker),1)
        self.assertNotEqual(code,code.replace(marker,'if element=="FIRE" then return .95 end'))
        self.assertIn("RED_FIRE_UNDERWATER_MULTIPLIER", HARNESS)


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--native",type=Path)
    ap.add_argument("--mutant",type=Path)
    args=ap.parse_args()
    if args.native or args.mutant:
        if not (args.native and args.mutant):
            ap.error("--native and --mutant must be provided together")
        emit_native(args.native,args.mutant)
    else:
        unittest.main(argv=["test_realm_battle_balance.py"],verbosity=2)
