"""Protected fail-first regression: appended integration must use distinct provider receipts.

Source baseline is original PR142 exact commit; these tests are not host identity
or GitHub-merge authority. A copied tail must never count as a new adoption.
"""
import copy
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "tests"))
from test_system_integration_contract import fixture
import system_integration_contract as guard

def candidate():
    before, after, comp = fixture()
    tail = copy.deepcopy(after["merged_prs"][-1])
    tail.update(pr=140, head="d"*40, merge_sha="e"*40,
                main_qa=1101, handoff=1102, main_after_handoff="f"*40)
    after["merged_prs"].append(tail)
    after["latest_review"] = {"pr":140,"head":tail["head"],"merge_sha":tail["merge_sha"]}
    after.update(merge_sha=tail["merge_sha"], main_after_merge=tail["merge_sha"],
                 main_after_handoff=tail["main_after_handoff"],
                 latest_main_sha=tail["main_after_handoff"])
    for field, num in (("main_qa",1101),("handoff",1102)):
        receipt=after[field]
        receipt.update(id=num,head=tail["merge_sha"],
                       url=f"https://github.com/owner/game-one/actions/runs/{num}")
        for job in (receipt["job_evidence"] if field=="main_qa" else receipt["jobs"]):
            job.update(id=job["id"]+100,head=tail["merge_sha"],run_id=num)
    comp["base_commit"]["sha"]=tail["merge_sha"]
    comp["commits"][-1]["sha"]=tail["main_after_handoff"]
    return before,after,comp

def check(b,a,c):
    result=guard.check_transition(b,a,repository="owner/game-one",comparison=c)
    assert result["verification"]=="NOT_VERIFIED"
    for flag in guard.FLAGS:assert result[flag] is False
    return result["status"]

def use_prior(before,after,comp,key):
    value=before["merged_prs"][-1][key]
    tail=after["merged_prs"][-1];tail[key]=value
    if key=="head":after["latest_review"]["head"]=value
    if key=="merge_sha":
        after["latest_review"]["merge_sha"]=value
        after["merge_sha"]=after["main_after_merge"]=comp["base_commit"]["sha"]=value
        for field in ("main_qa","handoff"):
            after[field]["head"]=value
            for job in (after[field]["job_evidence"] if field=="main_qa" else after[field]["jobs"]):
                job["head"]=value
    if key=="main_after_handoff":
        after["main_after_handoff"]=after["latest_main_sha"]=comp["commits"][-1]["sha"]=value
    if key in ("main_qa","handoff"):
        after[key]["id"]=value
        after[key]["url"]=f"https://github.com/owner/game-one/actions/runs/{value}"
        for job in (after[key]["job_evidence"] if key=="main_qa" else after[key]["jobs"]):
            job["run_id"]=value

class UniqueAdoptionTests(unittest.TestCase):
    def test_one_genuinely_fresh_tail_remains_accepted(self):
        b,a,c=candidate();self.assertEqual(check(b,a,c),"CONTRACT_PASS_UNTRUSTED_EVIDENCE")
    def test_same_record_no_append_remains_accepted(self):
        b,a,c=fixture();self.assertEqual(check(b,a,c),"CONTRACT_PASS_UNTRUSTED_EVIDENCE")
    def test_cloned_tail_does_not_create_fresh_adoption(self):
        b,a,c=fixture()
        clone=copy.deepcopy(a["merged_prs"][-1]);clone["pr"]=140
        a["merged_prs"].append(clone);a["latest_review"]["pr"]=140
        self.assertEqual(check(b,a,c),"BLOCKED_LEDGER_CONTRACT")
    def duplicate(self,key):
        b,a,c=candidate();use_prior(b,a,c,key)
        self.assertEqual(check(b,a,c),"BLOCKED_LEDGER_CONTRACT")
    def test_duplicate_head(self):self.duplicate("head")
    def test_duplicate_merge_sha(self):self.duplicate("merge_sha")
    def test_duplicate_posthandoff_sha(self):self.duplicate("main_after_handoff")
    def test_duplicate_main_qa_id(self):self.duplicate("main_qa")
    def test_duplicate_handoff_id(self):self.duplicate("handoff")
    def test_reused_qa_as_new_handoff(self):
        b,a,c=candidate();x=b["merged_prs"][-1]["main_qa"]
        a["merged_prs"][-1]["handoff"]=x
        a["handoff"]["id"]=x
        a["handoff"]["url"]=f"https://github.com/owner/game-one/actions/runs/{x}"
        a["handoff"]["jobs"][0]["run_id"]=x
        self.assertEqual(check(b,a,c),"BLOCKED_LEDGER_CONTRACT")
    def test_reused_handoff_as_new_qa(self):
        b,a,c=candidate();x=b["merged_prs"][-1]["handoff"]
        a["merged_prs"][-1]["main_qa"]=x
        a["main_qa"]["id"]=x
        a["main_qa"]["url"]=f"https://github.com/owner/game-one/actions/runs/{x}"
        for job in a["main_qa"]["job_evidence"]:job["run_id"]=x
        self.assertEqual(check(b,a,c),"BLOCKED_LEDGER_CONTRACT")
    def test_same_qa_and_handoff_in_new_tail(self):
        b,a,c=candidate();x=a["merged_prs"][-1]["handoff"]
        a["merged_prs"][-1]["main_qa"]=x
        a["main_qa"]["id"]=x
        a["main_qa"]["url"]=f"https://github.com/owner/game-one/actions/runs/{x}"
        for job in a["main_qa"]["job_evidence"]:job["run_id"]=x
        self.assertEqual(check(b,a,c),"BLOCKED_LEDGER_CONTRACT")
    def test_sparse_old_rows_preserved(self):
        b,a,c=candidate()
        b["merged_prs"][0]={"pr":124};a["merged_prs"][0]={"pr":124}
        self.assertEqual(check(b,a,c),"CONTRACT_PASS_UNTRUSTED_EVIDENCE")
    def test_reject_boolean_new_qa(self):
        b,a,c=candidate()
        a["merged_prs"][-1]["main_qa"]=True;a["main_qa"]["id"]=True
        self.assertEqual(check(b,a,c),"BLOCKED_LEDGER_CONTRACT")
    def test_do_not_change_inputs(self):
        b,a,c=candidate();saved=copy.deepcopy((b,a,c))
        check(b,a,c);self.assertEqual(saved,(b,a,c))
if __name__=="__main__":unittest.main()
