"""Tests for process/assembly gate only; not Studio/runtime gameplay QA."""
import copy
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/"tools"))
from chat_rc_assemble import assemble, GateError, digest

PIN = "a" * 40
CAP = ["match_lifecycle","team_spawn","input_mobile","capture_objective","combat_damage","victory_defeat","client_hud","map_art","entrypoint"]

class Assembly(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name);self.src=self.root/"sources";self.src.mkdir()
        self.units=[]
        for n, role, family in [("round","round","none"),("event","event_chooser","d08_event"),("damage","damage","none"),("map","none","none")]:
            file=f"modules/{n}.luau";path=self.src/file;path.parent.mkdir(parents=True,exist_ok=True)
            b=f"return {{ name = '{n}' }}\n".encode();path.write_bytes(b)
            self.units.append({"unit_id":n,"source_commit":PIN,"source_path":file,"target_path":f"src/server/{n}.luau", "sha256":digest(b), "authority":role,"variant_family":family,"variant_kind":"original" if family!="none" else "new","depends_on":[]})
        project=b'{"name":"TRAP RAIDERS","tree":{"$className":"DataModel"}}\n'
        (self.src/"project.json").write_bytes(project)
        self.units.append({"unit_id":"project","source_commit":PIN,"source_path":"project.json","target_path":"default.project.json","sha256":digest(project),"authority":"none", "depends_on":[]})
        evidence=b'python unittest: 3 passed\n'
        (self.src/"qa.txt").write_bytes(evidence)
        self.plan={"format":"P0D_CHAT_RELEASE_PLAN_V1","game_id":"TRAP_RAIDERS","work_id":"p0d-siege-v19","release_id":"S1_PLAYABLE_RC_A","phase":"CHAT_BUILD_READY","units":self.units,"capabilities":CAP,"offline_checks":[{"test":"unit","status":"PASS","log_path":"qa.txt","sha256":digest(evidence)}],"studio_status":"NOT_TESTED","publish_approved":False}
    def run_plan(self,plan=None):
        p=self.root/"plan.json";p.write_text(json.dumps(plan or self.plan),encoding="utf-8")
        return assemble(p,self.src,self.root/"output")
    def rejection(self,modify,pattern):
        plan=copy.deepcopy(self.plan);modify(plan)
        with self.assertRaisesRegex(GateError,pattern):self.run_plan(plan)
        self.assertFalse((self.root/"output").exists())
    def test_valid_receipt(self):
        r=self.run_plan();self.assertEqual(len(r["contents"]),5)
        self.assertEqual(r["studio_status"],"NOT_TESTED")
        self.assertFalse(r["release_approved"])
        self.assertTrue((self.root/"output"/"src/server/round.luau").is_file())
    def test_identical_repeat_rejected_output(self):
        self.run_plan()
        with self.assertRaisesRegex(GateError,"OUTPUT_MUST_BE_NEW"):self.run_plan()
    def test_wrong_digest(self):self.rejection(lambda x:x["units"][0].update(sha256="f"*64),"SHA_MISMATCH")
    def test_missing_roles(self):self.rejection(lambda x:x["units"].pop(0),"MISSING_CANONICAL")
    def test_duplicate_authority(self):self.rejection(lambda x:x["units"][3].update(authority="damage"),"DUPLICATE_AUTHORITY")
    def test_duplicate_source_family(self):self.rejection(lambda x:x["units"][3].update(variant_family="d08_event",variant_kind="cleanroom"),"VARIANT_COLLISION")
    def test_bad_commit(self):self.rejection(lambda x:x["units"][1].update(source_commit="main"),"UNPINNED_SOURCE")
    def test_duplicate_target(self):self.rejection(lambda x:x["units"][3].update(target_path=x["units"][0]["target_path"]),"COLLIDING_DESTINATION")
    def test_parent_escaping(self):self.rejection(lambda x:x["units"][3].update(source_path="../secret"),"PATH_TRAVERSAL")
    def test_unknown_dependency(self):self.rejection(lambda x:x["units"][3].update(depends_on=["missing"]),"UNKNOWN_DEPENDENCY")
    def test_cyclic_dependency(self):
        self.rejection(lambda x:(x["units"][0].update(depends_on=["damage"]),x["units"][2].update(depends_on=["round"])),"CIRCULAR_DEPENDENCY")
    def test_no_capability(self):self.rejection(lambda x:x["capabilities"].remove("input_mobile"),"CAPABILITIES_MISSING")
    def test_no_evidence(self):self.rejection(lambda x:x.update(offline_checks=[]),"NO_OFFLINE_EVIDENCE")
    def test_false_evidence(self):self.rejection(lambda x:x["offline_checks"][0].update(status="NOT_TESTED"),"EVIDENCE_NOT_PASS")
    def test_wrong_evidence_sha(self):self.rejection(lambda x:x["offline_checks"][0].update(sha256="e"*64),"EVIDENCE_SHA_MISMATCH")
    def test_false_studio_claim(self):self.rejection(lambda x:x.update(studio_status="PASS"),"STUDIO_OR_RELEASE")
    def test_false_publish(self):self.rejection(lambda x:x.update(publish_approved=True),"STUDIO_OR_RELEASE")
    def test_project_missing(self):self.rejection(lambda x:x["units"].pop(),"NO_STUDIO_PROJECT")
    def test_project_bad_json(self):
        (self.src/"project.json").write_text("not json")
        self.plan["units"][-1]["sha256"]=digest(b"not json")
        with self.assertRaisesRegex(GateError,"INVALID_STUDIO_PROJECT_JSON"):self.run_plan()
    def test_empty_release(self):self.rejection(lambda x:x.update(release_id=""),"NOT_CHAT_BUILD_READY")
    def test_source_symlink(self):
        target=self.src/"modules"/"event.luau"
        target.unlink();target.symlink_to(self.src/"modules"/"round.luau")
        with self.assertRaisesRegex(GateError,"SYMLINK_FORBIDDEN"):self.run_plan()
    def test_duplicate_unit(self):self.rejection(lambda x:x["units"].append(copy.deepcopy(x["units"][0])),"DUPLICATE_UNIT")


    def combined_plan(self):
        plan=copy.deepcopy(self.plan)
        plan["units"][0].pop("authority")
        plan["units"][0]["authorities"]=["round","event_chooser","damage"]
        plan["units"][1]["authority"]="none"
        plan["units"][2]["authority"]="none"
        return plan

    def expect_bad_combined(self,mutate,match):
        p=self.combined_plan()
        mutate(p)
        self.rejection(lambda dest:(dest.clear(),dest.update(p)),match)

    def test_combined_source_three_roles_valid(self):
        r=self.run_plan(self.combined_plan())
        self.assertEqual(len(r["contents"]),5)
        got={x["unit_id"]:x["authorities"] for x in r["source_units"]}
        self.assertEqual(got["round"],["round","event_chooser","damage"])
        self.assertEqual(got["event"],[])
        self.assertEqual(r["studio_status"],"NOT_TESTED")

    def test_combined_cross_unit_duplicate(self):
        self.expect_bad_combined(lambda p:p["units"][1].update(authority="damage"),"DUPLICATE_AUTHORITY")

    def test_combined_internal_duplicate(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authorities=["round","round","damage"]),"DUPLICATE_AUTHORITY_IN_UNIT")

    def test_combined_both_schemas(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authority="none"),"AUTHORITY_AMBIGUOUS_FIELDS")

    def test_combined_empty_array(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authorities=[]),"INVALID_AUTHORITIES_LIST")

    def test_combined_string_not_array(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authorities="round"),"INVALID_AUTHORITIES_LIST")

    def test_combined_nonstring_role(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authorities=["round",4]),"INVALID_AUTHORITIES_LIST")

    def test_combined_none_mixed(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authorities=["round","none"]),"INVALID_AUTHORITY")

    def test_combined_unknown(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authorities=["round","fake_role"]),"INVALID_AUTHORITY")

    def test_combined_missing_one_canonical(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authorities=["round","damage"]),"MISSING_CANONICAL_SERVER_AUTHORITIES")

    def test_combined_too_many_roles(self):
        self.expect_bad_combined(lambda p:p["units"][0].update(authorities=["round","event_chooser","damage","persistence","reward","matchmaker","fake"]),"INVALID_AUTHORITY")

    def test_legacy_unchanged_source_roles_receipt(self):
        r=self.run_plan()
        got={x["unit_id"]:x["authorities"] for x in r["source_units"]}
        self.assertEqual(got["round"],["round"])
        self.assertEqual(got["project"],[])

if __name__ == "__main__":unittest.main()
