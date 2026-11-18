"""Append-only Core36 post-CAS source-adoption truth, not engine validation."""
import copy
import json
import re
import unittest
from pathlib import Path

HEAD="f77b4d4393d9e9b19b65566413432a7a9f13962b"
RUN=44232589275
ARTIFACT_ID=14396515259
ZIP_BYTES=366128

def validate(active, core, receipt):
    assert active["active_profile"]=="rich51"
    assert active["source_profiles"]["eggrumble_v3_core36"]["source_count"]==36
    assert active["source_profiles"]["eggrumble_v3_core36"]["status"]=="CANDIDATE_PRIVATE_RC_SOURCE_SELECTION_PENDING_SAME_HEAD_CI"
    assert core["source_count"]==36 and core["baseline_source_count"]==31
    assert core["source_profile"]=="eggrumble_v3_core36"
    assert core["primary_s1_profile_unchanged"]=="rich51"
    assert core["production_published"] is False
    frozen=core["acceptance"]
    assert frozen["same_head_source_compiler"]=="PENDING_CANDIDATE"
    assert frozen["same_head_rojo_source_class"]=="PENDING_CANDIDATE"
    assert frozen["off31"]=="PENDING_CANDIDATE"
    assert frozen["official_nonforce_expected_sha_cas"] is False
    assert receipt["frozen_original_core36_manifest_status"]==active["source_profiles"]["eggrumble_v3_core36"]["status"]
    assert receipt["frozen_original_core36_acceptance"]=={
        k:frozen[k] for k in ("same_head_source_compiler","same_head_rojo_source_class","off31","official_nonforce_expected_sha_cas")}
    assert receipt["schema"]=="P0D_GQ8_CORE36_POSTCAS_ADOPTION_RECEIPT_V1"
    assert receipt["scope"]=="HISTORICAL_FORMAL_PRIVATE_RC_SOURCE_ADOPTION_ONLY"
    assert re.fullmatch("[0-9a-f]{40}",receipt["observed_formal_rc_sha"])
    assert receipt["observed_formal_rc_sha"]==receipt["source_qa"]["source_head_sha"]==HEAD
    assert receipt["source_qa"]["github_actions_run_id"]==RUN
    assert receipt["source_qa"]["reported_conclusion"]=="completed_success"
    for key in ("same_head_native","same_head_rojo_source_class","off31"):
        assert receipt["source_qa"][key]=="SUCCESS"
    assert receipt["artifact"]["type"]=="GITHUB_ACTIONS_ZIP"
    assert receipt["artifact"]["id"]==ARTIFACT_ID
    assert receipt["artifact"]["zip_size_in_bytes"]==ZIP_BYTES
    assert receipt["artifact"]["studio_rbxlx_bytes"]=="UNKNOWN_NOT_MEASURED"
    source=receipt["original_author_selection"]
    assert source["base_source_count"]==31 and source["selected_private_source_count"]==36
    assert source["added_realm_sources"]==3 and source["added_regen_sources"]==2
    assert source["singleton_host"] and source["singleton_combat"] and source["singleton_swarm"]
    assert receipt["default_s1_profile"]=="rich51"
    for key in ("studio_2client","android_15min","human_fun"):
        assert receipt[key]=="NOT_TESTED"
    assert receipt["art_quality"]=="NO_GO"
    assert receipt["owner_accepted"] is False and receipt["roblox_published"] is False
    return True

class Core36ReceiptRegression(unittest.TestCase):
    def setUp(self):
        root=Path(__file__).resolve().parents[2]
        self.active=json.loads((root/"rc_fastlane/ACTIVE.json").read_text())
        self.core=json.loads((root/"rc_fastlane/EGGRUMBLE_V3_CORE36.json").read_text())
        self.receipt=json.loads((root/"rc_fastlane/EGGRUMBLE_V3_CORE36_POSTCAS_RECEIPT_20261118.json").read_text())
    def test_historical_receipt_consistent(self):
        self.assertTrue(validate(self.active,self.core,self.receipt))
    def test_reject_fake_studio_art_fun(self):
        for key,bad in (("studio_2client","PASS"),("android_15min","PASS"),("human_fun","PASS"),("art_quality","PASS"),("owner_accepted",True)):
            r=copy.deepcopy(self.receipt);r[key]=bad
            with self.assertRaises(AssertionError,msg=key):
                validate(self.active,self.core,r)
    def test_reject_false_zip_place_size_or_identity(self):
        for chain,bad in ((("artifact","type"),"STUDIO_RBXLX"),(("artifact","studio_rbxlx_bytes"),366128),(("artifact","zip_size_in_bytes"),366129),(("artifact","id"),0),(("source_qa","github_actions_run_id"),1234),(("source_qa","source_head_sha"),"0"*40)):
            r=copy.deepcopy(self.receipt);r[chain[0]][chain[1]]=bad
            with self.assertRaises(AssertionError,msg=str(chain)):
                validate(self.active,self.core,r)
    def test_do_not_rewrite_frozen_selector_or_live_profile(self):
        a=copy.deepcopy(self.active);a["active_profile"]="eggrumble_v3_core36"
        with self.assertRaises(AssertionError):
            validate(a,self.core,self.receipt)
        c=copy.deepcopy(self.core);c["acceptance"]["official_nonforce_expected_sha_cas"]=True
        with self.assertRaises(AssertionError):
            validate(self.active,c,self.receipt)
    def test_do_not_claim_game_source_adoption_for_this_pr(self):
        r=copy.deepcopy(self.receipt);r["original_author_selection"]["selected_private_source_count"]=37
        with self.assertRaises(AssertionError):
            validate(self.active,self.core,r)
        r=copy.deepcopy(self.receipt);r["roblox_published"]=True
        with self.assertRaises(AssertionError):
            validate(self.active,self.core,r)

if __name__=="__main__":
    unittest.main()
