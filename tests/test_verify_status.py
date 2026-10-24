import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from verify_status import status_ok
REPO = "kk051780/toy-wars-factory"

class AutonomousStatusTests(unittest.TestCase):
    def test_valid_stopped_states(self):
        for status in ("NOT_ACTIVE","NOT_ACTIVE_AI_INFERENCE_UNVERIFIED","BLOCKED_AUTH_AND_LOCK_NOT_ACTIVE"):
            self.assertTrue(status_ok({"status":status,"workflow_run_verified":False},REPO))
    def test_stopped_cannot_claim_execution(self):
        self.assertFalse(status_ok({"status":"NOT_ACTIVE_AI_INFERENCE_UNVERIFIED","workflow_run_verified":True},REPO))
    def test_unknown_status_fails(self):
        self.assertFalse(status_ok({"status":"HAPPY","workflow_run_verified":False},REPO))
    def test_active_requires_compiled_workflow(self):
        self.assertFalse(status_ok({"status":"ACTIVE_VERIFIED","workflow_run_verified":True,"agentic_workflow_compiled":False},REPO))
    def test_active_requires_real_url_shape(self):
        self.assertFalse(status_ok({"status":"ACTIVE_VERIFIED","workflow_run_verified":True,"agentic_workflow_compiled":True,"verified_agent_run_url":"https://github.com.attacker.invalid/"+REPO+"/actions/runs/1"},REPO))
    def test_active_requires_same_repo(self):
        self.assertFalse(status_ok({"status":"ACTIVE_VERIFIED","workflow_run_verified":True,"agentic_workflow_compiled":True,"verified_agent_run_url":"https://github.com/not-ours/repo/actions/runs/1"},REPO))
    def test_active_valid_shape_not_actual_proof(self):
        self.assertTrue(status_ok({"status":"ACTIVE_VERIFIED","workflow_run_verified":True,"agentic_workflow_compiled":True,"verified_agent_run_url":"https://github.com/"+REPO+"/actions/runs/123"},REPO))

if __name__=="__main__": unittest.main()
