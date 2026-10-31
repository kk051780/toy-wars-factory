"""PR163: a lost CAS receipt must not strand a newly acquired coordinator lease.

Synthetic host callbacks only; not real host telemetry/authorization or GitHub traffic.
"""
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import system_actions_write_probe as target

MAIN="a"*40
OLD="b"*40
OWN="c"*40
FOREIGN="d"*40
OWNER="9da4af9c-0a89-49ea-a77e-8459eac6c65a"
OTHER="581c9d84-436e-422c-bc44-d06ff57f5924"
EPOCH=319
SCOPE={"main":MAIN,"branch":"controller/gha-write-probe-41199998877-a1",
       "run_id":41199998877,"attempt":1,"owner":OWNER}
ENV={"GITHUB_RUN_ID":"41199998877","PROBE_CONSENT":target.CONSENT}

def holder(who=OWNER):
    return {"kind":"CONTROLLER","owner_id":who,"epoch":EPOCH,
            "acquired_at":"2026-10-31T03:11:00+00:00",
            "expires_at":"2026-10-31T03:36:00+00:00"}

class FakeHost:
    def __init__(self,claim_effect="own",claim_error="ACK_LOST",source_error=""):
        self.initial={"schema":1,"epoch":EPOCH-1,"holder":None}
        self.plan=deepcopy(self.initial)
        self.plan["epoch"]=EPOCH
        self.plan["holder"]=holder()
        self.current=deepcopy(self.initial)
        self.claim_effect=claim_effect
        self.claim_error=claim_error
        self.source_error=source_error
        self.cas_calls=[]
        self.read_calls=0
        self.source_calls=0
        self.verifier_calls=0
        self.fail_current_read=False
    def sha(self,api,what):
        if what=="main":return MAIN
        if what==target.CONTROL_REF:
            if self.current["holder"] is None:return OLD if not self.cas_calls else FOREIGN
            return OWN if self.current["holder"]["owner_id"]==OWNER else FOREIGN
        raise AssertionError(what)
    def state(self,api,sha):
        self.read_calls+=1
        if self.fail_current_read and self.cas_calls:
            raise target.ProbeError("CURRENT_READ_UNAVAILABLE")
        return deepcopy(self.current)
    def cas(self,api,old,new):
        self.cas_calls.append((old,deepcopy(new)))
        if len(self.cas_calls)==1:
            if self.claim_effect=="own":self.current=deepcopy(new)
            if self.claim_effect=="foreign":
                self.current=deepcopy(self.plan)
                self.current["holder"]["owner_id"]=OTHER
            if self.claim_error=="UNEXPECTED_RUNTIME_ERROR":
                raise RuntimeError("test-only-transport-crash")
            if self.claim_error:
                raise target.ProbeError(self.claim_error)
            return OWN
        if self.current["holder"] is None or self.current["holder"]["owner_id"]!=OWNER:
            raise AssertionError("attempted foreign/unowned release")
        self.current=deepcopy(new)
        return FOREIGN
    def acquire(self,*args,**kwargs):
        return {"action":"ACQUIRE","write":True,"state":deepcopy(self.plan)}
    def owns(self,state,kind,owner,epoch,at):
        h=state.get("holder")
        return bool(h and kind=="CONTROLLER" and owner==OWNER and epoch==EPOCH
                    and (h["kind"],h["owner_id"],h["epoch"])==(kind,owner,epoch))
    def release(self,state,kind,owner,epoch,at):
        if not self.owns(state,kind,owner,epoch,at):
            raise AssertionError("must release own only")
        o=deepcopy(state);o["holder"]=None
        return o
    def create(self,api,scope):
        self.source_calls+=1
        if self.source_error:raise target.ProbeError(self.source_error)
        return 123
    def verify(self,api,scope,pr):
        self.verifier_calls+=1
        if self.source_error=="READBACK_FAILED":
            raise target.ProbeError("READBACK_FAILED")
        return pr
    def run(self):
        class API:
            def call(self,method,path,body=None):return {}
        with ExitStack() as stack:
            for name,fn in (("checked_context",lambda *a:deepcopy(SCOPE)),
                             ("sha_ref",self.sha),("state_at",self.state),
                             ("acquire",self.acquire),("cas_state",self.cas),
                             ("owns",self.owns),("release",self.release),
                             ("create_branch_probe",self.create),
                             ("verify_created_probe",self.verify),
                             ("now",lambda:"2026-10-31T03:11:00+00:00")):
                stack.enter_context(patch.object(target,name,fn))
            return target.run(API(),ENV)

class ClaimReceiptTests(unittest.TestCase):
    def test_postclaim_ack_lost_recovers_only_own_active_epoch_and_reports_failure(self):
        x=FakeHost(claim_effect="own",claim_error="ACK_LOST")
        with self.assertRaisesRegex(target.ProbeError,"^ACK_LOST$"):
            x.run()
        self.assertEqual(len(x.cas_calls),2)
        self.assertIsNone(x.current["holder"])
        self.assertEqual(x.source_calls,0)
        self.assertEqual(x.verifier_calls,0)
        self.assertGreaterEqual(x.read_calls,2)

    def test_original_claim_rejected_without_write_never_mutates_on_cleanup(self):
        x=FakeHost(claim_effect="none",claim_error="CLAIM_DENIED")
        with self.assertRaisesRegex(target.ProbeError,"^CLAIM_DENIED$"):
            x.run()
        self.assertEqual(len(x.cas_calls),1)
        self.assertIsNone(x.current["holder"])
        self.assertEqual(x.source_calls,0)
        self.assertGreaterEqual(x.read_calls,2)

    def test_foreign_epoch_never_released_after_unknown_cas_receipt(self):
        x=FakeHost(claim_effect="foreign",claim_error="ACK_LOST")
        with self.assertRaisesRegex(target.ProbeError,"^ACK_LOST$"):
            x.run()
        self.assertEqual(len(x.cas_calls),1)
        self.assertEqual(x.current["holder"]["owner_id"],OTHER)
        self.assertEqual(x.source_calls,0)

    def test_unexpected_postclaim_runtime_failure_still_finally_releases(self):
        x=FakeHost(claim_effect="own",claim_error="UNEXPECTED_RUNTIME_ERROR")
        with self.assertRaisesRegex(RuntimeError,"test-only-transport-crash"):
            x.run()
        self.assertEqual(len(x.cas_calls),2)
        self.assertIsNone(x.current["holder"])
        self.assertEqual(x.source_calls,0)

    def test_unknown_receipt_and_current_read_failure_fails_closed(self):
        x=FakeHost(claim_effect="own",claim_error="ACK_LOST")
        x.fail_current_read=True
        with self.assertRaisesRegex(target.ProbeError,"^RELEASE_UNCONFIRMED$"):
            x.run()
        self.assertEqual(len(x.cas_calls),1)
        self.assertEqual(x.source_calls,0)

    def test_healthy_source_failure_still_releases(self):
        x=FakeHost(claim_effect="own",claim_error=None,source_error="BRANCH_DENIED")
        with self.assertRaisesRegex(target.ProbeError,"^BRANCH_DENIED$"):
            x.run()
        self.assertEqual(len(x.cas_calls),2)
        self.assertIsNone(x.current["holder"])
        self.assertEqual(x.source_calls,1)

    def test_healthy_source_readback_failure_still_releases(self):
        x=FakeHost(claim_effect="own",claim_error=None,source_error="READBACK_FAILED")
        with self.assertRaisesRegex(target.ProbeError,"READBACK_FAILED"):
            x.run()
        self.assertEqual(len(x.cas_calls),2)
        self.assertIsNone(x.current["holder"])
        self.assertEqual(x.source_calls,1)
        self.assertEqual(x.verifier_calls,1)

    def test_normal_claim_write_verify_release_remains_success(self):
        x=FakeHost(claim_effect="own",claim_error=None)
        self.assertEqual(x.run(),{"status":"DRAFT_PR_CREATED_NOT_MERGED","pr":123,"wrote":True})
        self.assertEqual(len(x.cas_calls),2)
        self.assertIsNone(x.current["holder"])
        self.assertEqual(x.source_calls,1)
        self.assertEqual(x.verifier_calls,1)

if __name__=="__main__":
    unittest.main()
