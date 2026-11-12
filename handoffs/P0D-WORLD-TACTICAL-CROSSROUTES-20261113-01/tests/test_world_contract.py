import copy, json, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/"world_contract.json").read_text(encoding="utf-8"))
REALMS={"LAND","SEA","SKY","COSMIC","CELESTIAL","EMBER","ECLIPSE"}
ROLES={"戦士","魔法使い","忍者","トラッパー","建築士","魔獣使い","ゾンビ使い"}
def reachable(edges,start,target,team,carrying,disabled=None):
    frontier=[start]; seen={start}
    while frontier:
        here=frontier.pop()
        if here==target: return True
        for e in edges:
            if e["id"]==disabled or e["from"]!=here: continue
            if e["access"]!="FREE" or team not in e["teams"]: continue
            if not e["passable_without_class"] or (carrying and not e["carry_allowed"]): continue
            if e["to"] not in seen: seen.add(e["to"]); frontier.append(e["to"])
    return False
def validate(d, outages=True):
    assert d["stage"]=="S2_PLUS_OPTIONAL"
    assert d["studio_qa"]=="NOT_TESTED" and d["actual_scene_geometry"]=="NOT_CREATED"
    assert d["published"]=="NOT_AUTHORIZED"
    assert set(d["roles"])==ROLES and len(d["roles"])==7
    assert set(d["worlds"])==REALMS and len(d["routes"])==7
    cards=d["cards"]; assert len(cards)==6
    assert {c["field_id"] for c in cards}=={f"WF-{i}" for i in range(25,31)}
    for c in cards:
        for key in ["name","child_one_action","three_second_cue","free_alternate",
                    "defender_telegraph","defender_counterplay","fail_safe",
                    "egg_carry_strategy","class_combo_examples","promo_7s",
                    "promo_15s","h0","h1"]:
            assert len(c[key])>=8, (c["field_id"],key)
        assert c["no_class_or_purchase_required"] is True
        assert set(c["class_archetypes"])==ROLES
        assert c["warning_before_s"]>=2 and c["max_closed_s"]<=12 and c["recovery_within_s"]<=8
        assert c["adoption"]=="PARK_S2_PLUS" and c["studio_qa"]=="NOT_TESTED"
    ids=[e["id"] for e in d["edges"]]; assert len(ids)==len(set(ids))
    assert len(d["edges"])==56
    for e in d["edges"]:
        assert e["access"]=="FREE" and set(e["teams"])=={"RED","BLUE"}
        assert e["carry_allowed"] and e["passable_without_class"]
        assert e["recovery_pad"]=="HUB" and e["max_wait_s"]<=12
    for r in d["routes"]:
        assert r["realm"] in REALMS
        assert r["route_a"]!=r["route_b"]
        for team in ("RED","BLUE"):
            for carry in (False,True):
                blocked=[None]+ids if outages else [None]
                for one in blocked:
                    assert reachable(d["edges"],"HUB",r["target"],team,carry,one), (r["realm"],team,carry,one,"in")
                    assert reachable(d["edges"],r["target"],"HUB",team,carry,one), (r["realm"],team,carry,one,"out")
    return True
class TestWorldContract(unittest.TestCase):
    def test_original_contract(self): self.assertTrue(validate(DATA))
    def test_exact_six_mechanics(self): self.assertEqual(len(DATA["cards"]),6)
    def test_seven_class_archetypes(self): self.assertEqual(set(DATA["roles"]),ROLES)
    def test_seven_worlds(self): self.assertEqual(set(DATA["worlds"]),REALMS)
    def test_double_free_access_all_worlds(self):
        self.assertEqual(len(DATA["edges"]),56)
        self.assertTrue(validate(DATA))
    def test_no_magic_studio_pass(self): self.assertEqual(DATA["studio_qa"],"NOT_TESTED")
    def test_no_paid_route(self):
        d=copy.deepcopy(DATA); d["edges"][0]["access"]="VIP"
        with self.assertRaises(AssertionError): validate(d,False)
    def test_red_team_cannot_get_advantage(self):
        d=copy.deepcopy(DATA); d["edges"][0]["teams"]=["RED"]
        with self.assertRaises(AssertionError): validate(d,False)
    def test_carrying_egg_must_remain_possible(self):
        d=copy.deepcopy(DATA); d["edges"][0]["carry_allowed"]=False
        with self.assertRaises(AssertionError): validate(d,False)
    def test_no_class_lock(self):
        d=copy.deepcopy(DATA); d["edges"][0]["passable_without_class"]=False
        with self.assertRaises(AssertionError): validate(d,False)
    def test_no_indefinite_gate_closure(self):
        d=copy.deepcopy(DATA); d["cards"][0]["max_closed_s"]=999
        with self.assertRaises(AssertionError): validate(d,False)
    def test_recovery_not_missing(self):
        d=copy.deepcopy(DATA); d["edges"][0]["recovery_pad"]=""
        with self.assertRaises(AssertionError): validate(d,False)
    def test_break_both_routes_detected(self):
        d=copy.deepcopy(DATA)
        d["edges"]=[e for e in d["edges"] if not (e["realm"]=="SEA" and e["from"]=="HUB")]
        with self.assertRaises(AssertionError): validate(d,False)
    def test_one_way_escape_detected(self):
        d=copy.deepcopy(DATA)
        d["edges"]=[e for e in d["edges"] if not (e["realm"]=="SKY" and e["from"]=="SKY_CASTLE")]
        with self.assertRaises(AssertionError): validate(d,False)
    def test_fake_studio_pass_rejected(self):
        d=copy.deepcopy(DATA); d["studio_qa"]="PASS"
        with self.assertRaises(AssertionError): validate(d,False)
    def test_duplicate_wf_card_rejected(self):
        d=copy.deepcopy(DATA); d["cards"][0]["field_id"]="WF-26"
        with self.assertRaises(AssertionError): validate(d,False)
if __name__=="__main__": unittest.main()
