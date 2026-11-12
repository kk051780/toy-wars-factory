import copy
import hashlib
import json
import math
import pathlib
import re
import unittest

HERE=pathlib.Path(__file__).resolve()
ROOT=HERE.parents[1]
REPO=HERE.parents[3]
S1=REPO/"releases"/"P0D_S1_KIDS_RC01"
SPEC=json.loads((ROOT/"S1_SOURCE_WORLD_COMPAT.json").read_text(encoding="utf-8"))
NAMES=("RED","BLUE")
ROLES=("RAIDER","GUARDIAN")

def read_actual_source():
    result={}
    for item in SPEC["source_files"]:
        path=S1/item["file"]
        raw=path.read_bytes()
        assert hashlib.sha256(raw).hexdigest()==item["sha256"], ("pinned_source_sha_failed",str(path))
        result[item["file"]]=raw.decode("utf-8")
    return result

def must(text, pattern):
    assert re.search(pattern,text,re.MULTILINE), ("missing_canonical_source_rule",pattern)

def check_source_contract(sources):
    c=sources["src/shared/Config.luau"]
    g=sources["src/server/Game.server.luau"]
    h=sources["src/client/HUD.client.luau"]
    m=sources["src/server/MapBuilder.luau"]
    t=sources["src/server/S1TrapRules.luau"]
    r=sources["src/server/S1Rules.luau"]
    # Explicit two-role authority; proposed seven jobs must not be smuggled in.
    must(c,r"RoleHealth\s*=\s*\{RAIDER\s*=\s*100,\s*GUARDIAN\s*=\s*135\}")
    must(c,r"RoleWalkSpeed\s*=\s*\{RAIDER\s*=\s*19,\s*GUARDIAN\s*=\s*15\}")
    must(c,r"CombatDamage\s*=\s*\{RAIDER\s*=\s*24,\s*GUARDIAN\s*=\s*18\}")
    must(c,r"CastleAttackDamage\s*=\s*\{RAIDER\s*=\s*14,\s*GUARDIAN\s*=\s*10\}")
    role_block=g.split("local function applyRole(",1)[1].split("remote.OnServerEvent:",1)[0]
    must(role_block,r'if role ~= "RAIDER" and role ~= "GUARDIAN" then return end')
    must(g,r'roles\[player\]\s*=\s*"RAIDER"')
    must(h,r'button\(gui,\s*"RaiderRole"')
    must(h,r'button\(gui,\s*"GuardianRole"')
    assert not re.search(r'button\(gui,\s*"(MageRole|NinjaRole|BeastRole|ZombieRole|BuilderRole)"',h)
    # Out-of-map recovery *drops egg*. Cosmetic world cannot exceed these limits.
    recovery=g.split("-- Recovery uses the existing server-only authoritative tick",1)[1].split("task.spawn(function()",1)[0]
    must(recovery,r'position\.Y < -30')
    must(recovery,r'math\.abs\(position\.X\) > 130')
    must(recovery,r'math\.abs\(position\.Z\) > 76')
    must(recovery,r'dropEgg\(player\)')
    must(recovery,r'root\.CFrame\s*=\s*map\.teams\[team\]\.spawn')
    # Existing canonical egg/pad rules are server-only.
    must(r,r'function Rules\.canSteal')
    must(r,r'function Rules\.canScore')
    must(r,r'carriedEggTeam == Rules\.opponent\(team\) and ownEggAtBase')
    must(g,r'map\.teams\[team\]\.eggPrompt\.Triggered')
    must(g,r'map\.teams\[team\]\.scorePrompt\.Triggered')
    # Expected exact map anchors; proposal targets present actual castle assets only.
    must(m,r'GrassArena.*Vector3\.new\(250,\s*4,\s*142\)')
    must(m,r'Vector3\.new\(sign \* 98,\s*2\.5,\s*-20\)')
    must(m,r'Vector3\.new\(sign \* 82,\s*-\.5,\s*20\)')
    must(m,r'CFrame\.new\(sign \* 68,\s*5,\s*0\)')
    must(m,r'Vector3\.new\(sign \* 107,\s*6\.5,\s*0\)')
    # Guardian trap has strictly bounded legal zones and NO carrying.
    must(t,r's\.role ~= "GUARDIAN"')
    must(t,r's\.carrying == true')
    must(t,r'math\.abs\(s\.x\) > 116 or math\.abs\(s\.z\) > 55')
    must(t,r's\.y < 2 or s\.y > 8')
    must(t,r'TrapRules\.COOLDOWN = 20')
    must(t,r'TrapRules\.MAX_PER_TEAM = 2')
    must(t,r'TrapRules\.OBJECTIVE_CLEARANCE = 15')
    must(t,r's\.team == "RED" and s\.x > -9')
    must(t,r's\.team == "BLUE" and s\.x < 9')
    return True

def check_route_spec(d):
    assert d["studio_qa"]=="NOT_TESTED" and d["s1_written"] is False and d["h1_actual_integrated"] is False
    assert d["source_commit"]=="3120b9d3c0a5ec58c9f2613c5d186f3493b54f83"
    assert set(d["implemented_roles"])==set(ROLES)
    assert d["future_roles_executable_in_s1"] is False
    assert len(d["conceptual_future_roles"])==7
    assert d["play_bounds"]["breaks_egg_on_out_of_bounds"] is True
    assert d["play_bounds"]["abs_x_recovery"]==130 and d["play_bounds"]["abs_z_recovery"]==76
    assert d["play_bounds"]["y_below_recovery"]==-30
    assert d["guardian_trap_limits"]["forbidden_when_carrying"] is True
    a=d["integration_policy"]
    for k in ("new_damage_or_round_owner","new_remote","new_client_position_or_score_selection","reward_or_purchase"):
        assert a[k] is False, k
    assert a["only_original_server_egg_and_score_pad"] and a["f2p_route_pair"]
    assert len(d["proposed_route_studies"])==4
    by_team={team:{} for team in NAMES}
    for way in d["proposed_route_studies"]:
        team,kind=way["team"],way["kind"]
        assert team in NAMES and kind in ("SEA","SKY")
        assert kind not in by_team[team]
        by_team[team][kind]=way
        assert way["stage"]=="STUDY_ONLY_NOT_PHYSICALLY_BUILT"
        for key in ("free_entry","raider_and_guardian_access","egg_carry_allowed","no_new_ability","no_portal_teleport","return_to_original_score_pad"):
            assert way[key] is True, (team,kind,key)
        opponent="BLUE" if team=="RED" else "RED"
        spawn=d["locations"][team]["spawn"]
        egg=d["locations"][opponent]["egg"]
        pad=d["locations"][team]["score_pad"]
        outbound=way["outbound_root_waypoints"]; back=way["return_root_waypoints"]
        assert len(outbound)>=5 and len(back)>=5
        assert outbound[0]==spawn
        assert outbound[-1][0]==egg[0] and outbound[-1][2]==egg[2]
        assert back[0][0]==egg[0] and back[0][2]==egg[2]
        assert back[-1][0]==pad[0] and back[-1][2]==pad[2]
        for pts in (outbound,back):
            for point in pts:
                assert all(isinstance(x,(int,float)) and math.isfinite(x) for x in point)
                x,y,z=point
                # Inside current field visual boundary, stricter than game recovery.
                assert abs(x)<=125 and abs(z)<=71 and y>=-30, (team,kind,point)
            for first,second in zip(pts,pts[1:]):
                assert math.dist(first,second)<=75, "no unmodeled long distance instantaneous teleport"
        assert len(way["required_real_studio_checks"])>=6
    for team in NAMES:
        assert set(by_team[team])=={"SEA","SKY"}
        sea=by_team[team]["SEA"]["outbound_root_waypoints"]
        sky=by_team[team]["SKY"]["outbound_root_waypoints"]
        assert sea[1:-1]!=sky[1:-1]
        for carrying in (False,True):
            for role in ROLES:
                for route_blocked in ("NONE","SEA","SKY"):
                    surviving=[w for k,w in by_team[team].items() if k!=route_blocked]
                    assert surviving and all(w["free_entry"] and w["egg_carry_allowed"] for w in surviving)
                    # No fabricated class-specific inaccessible route.
                    assert all(w["raider_and_guardian_access"] for w in surviving)
    return True

class TestPinnedActualS1(unittest.TestCase):
    def test_genuine_original_source_hashes(self): self.assertEqual(len(read_actual_source()),6)
    def test_original_two_role_and_map_contract(self): self.assertTrue(check_source_contract(read_actual_source()))
    def test_proposal_within_current_engine_bounds(self): self.assertTrue(check_route_spec(SPEC))
    def test_not_7_s1_roles(self): self.assertEqual(set(SPEC["implemented_roles"]),{"RAIDER","GUARDIAN"})
    def test_red_blue_mirror_points(self):
        for name in NAMES:
            d=SPEC["locations"][name]
            s=-1 if name=="RED" else 1
            self.assertEqual(d["spawn"][0],s*68)
            self.assertEqual(d["egg"][0],s*98)
            self.assertEqual(d["score_pad"][0],s*82)
    def test_bad_unchecked_magic_role_rejected(self):
        d=copy.deepcopy(SPEC);d["future_roles_executable_in_s1"]=True
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_bad_7_new_role_executable_rejected(self):
        d=copy.deepcopy(SPEC);d["implemented_roles"]["NINJA"]={"health":99}
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_fake_actual_studio_pass_rejected(self):
        d=copy.deepcopy(SPEC);d["studio_qa"]="PASS"
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_egg_teleport_rejected(self):
        d=copy.deepcopy(SPEC);d["proposed_route_studies"][0]["no_portal_teleport"]=False
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_out_of_bounds_route_rejected(self):
        d=copy.deepcopy(SPEC);d["proposed_route_studies"][0]["return_root_waypoints"][2][0]=200
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_egg_carry_blocked_rejected(self):
        d=copy.deepcopy(SPEC);d["proposed_route_studies"][1]["egg_carry_allowed"]=False
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_faked_one_free_route_rejected(self):
        d=copy.deepcopy(SPEC);d["proposed_route_studies"]=[r for r in d["proposed_route_studies"] if r["id"]!="RED_SKY"]
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_paywall_rejected(self):
        d=copy.deepcopy(SPEC);d["proposed_route_studies"][0]["free_entry"]=False
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_second_game_authority_rejected(self):
        d=copy.deepcopy(SPEC);d["integration_policy"]["new_damage_or_round_owner"]=True
        with self.assertRaises(AssertionError):check_route_spec(d)
    def test_disabled_egg_reset_rejected(self):
        s=read_actual_source()
        f="src/server/Game.server.luau"
        s[f]=s[f].replace("dropEgg(player)\n                    restoreSlow(player)","restoreSlow(player)")
        with self.assertRaises(AssertionError):check_source_contract(s)
    def test_guardian_carry_trap_mutant_rejected(self):
        s=read_actual_source()
        f="src/server/S1TrapRules.luau"
        s[f]=s[f].replace("or s.carrying == true","")
        with self.assertRaises(AssertionError):check_source_contract(s)
    def test_fake_7_roles_source_mutant_rejected(self):
        s=read_actual_source()
        f="src/server/Game.server.luau"
        s[f]=s[f].replace('if role ~= "RAIDER" and role ~= "GUARDIAN" then return end','if type(role) ~= "string" then return end')
        with self.assertRaises(AssertionError):check_source_contract(s)
    def test_bad_border_forgery_rejected(self):
        s=read_actual_source()
        f="src/server/Game.server.luau"
        s[f]=s[f].replace("math.abs(position.X) > 130","math.abs(position.X) > 9999")
        with self.assertRaises(AssertionError):check_source_contract(s)
    def test_wrong_egg_position_source_mutant_rejected(self):
        s=read_actual_source()
        f="src/server/MapBuilder.luau"
        s[f]=s[f].replace("sign * 98, 2.5, -20","sign * 999, 2.5, -20")
        with self.assertRaises(AssertionError):check_source_contract(s)
if __name__=="__main__": unittest.main()
