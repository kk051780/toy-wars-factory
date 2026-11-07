"""Pure mock-host test cases. No real GitHub writer or authenticated run."""
import copy
import hashlib
import json
import threading
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from system_parallel_shadow_leases import claim, release, apply_once, KEY

REPO = "kk051780/toy-wars-factory"
MAIN = "a"*40
REF = "b"*40
NOW = "2026-11-08T00:00:00Z"
LATER = "2026-11-08T00:01:00Z"
END = "2026-11-08T00:20:00Z"
A = ("11111111-1111-4111-8111-111111111111",
     "22222222-2222-4222-8222-222222222222",
     "33333333-3333-4333-8333-333333333333")
B = ("44444444-4444-4444-8444-444444444444",
     "55555555-5555-4555-8555-555555555555",
     "66666666-6666-4666-8666-666666666666")
C = ("77777777-7777-4777-8777-777777777777",
     "88888888-8888-4888-8888-888888888888",
     "99999999-9999-4999-8999-999999999999")

def snap():
    return {"repository":REPO,"main_sha":MAIN,"ref_sha":REF,
            "state":{"schema":1,"epoch":100,"holder":None,"policy":{"keep":True}}}

def request(name="alpha-work", path="tools/alpha.py", ids=A):
    return {"scope":{"project_id":"toy-wars-factory","repository":REPO,
                     "work_id":name,"branch":"controller/"+name,
                     "base_sha":MAIN,"write_paths":[path],"read_paths":[],
                     "generated_paths":[],"shared_resources":[],"status":"ACTIVE"},
            "owner_id":ids[0],"run_id":ids[1],"nonce":ids[2],"expires_at":END}

def surrender(req):
    return {k:req[k] for k in ("owner_id","run_id","nonce")} | {"work_id":req["scope"]["work_id"]}

class FakeHost:
    def __init__(self, state):
        self.value=copy.deepcopy(state)
        self.mu=threading.Lock()
        self.count=0
    def read(self):
        with self.mu: return copy.deepcopy(self.value)
    def cas(self, old, new):
        with self.mu:
            self.count+=1
            if self.value["ref_sha"]!=old: return None
            blob=json.dumps(new,sort_keys=True).encode()
            ref=hashlib.sha1(blob).hexdigest()
            self.value["ref_sha"]=ref
            self.value["state"]=copy.deepcopy(new)
            return ref
    def apply(self, initial, plan, now=LATER):
        return apply_once(initial,plan,read=self.read,cas=self.cas,
                          clock=lambda:now,requested_at=NOW)

class ShadowLeaseTests(unittest.TestCase):
    def setUp(self):
        self.s=snap()
        self.a=request()
        self.b=request("beta-work","tests/beta.py",B)
        self.c=request("gamma-work","tools/gamma.py",C)
    def proposed(self, snap, req):
        v=claim(snap,req,NOW)
        self.assertEqual(v["decision"],"SHADOW_CLAIM_CAS_PROPOSAL",v)
        self.assertFalse(v["may_write"])
        return v
    def two(self):
        host=FakeHost(self.s)
        host.apply(self.s,self.proposed(self.s,self.a))
        s=host.read()
        host.apply(s,self.proposed(s,self.b))
        return host

    def test_first_advisory_no_permission(self):
        p=self.proposed(self.s,self.a)
        self.assertFalse(p["github_authenticated"])
        self.assertFalse(p["may_dispatch"])
        self.assertFalse(p["parallel_real"])
        self.assertEqual(p["state"]["epoch"],101)
        self.assertEqual(p["state"]["policy"],self.s["state"]["policy"])
    def test_two_distinct_mock_writers(self):
        h=self.two()
        self.assertEqual(len(h.read()["state"][KEY]["entries"]),2)
        self.assertEqual(h.count,2)
    def test_two_stale_cas_same_predecessor(self):
        h=FakeHost(self.s)
        pa=self.proposed(self.s,self.a)
        pb=self.proposed(self.s,self.b)
        self.assertEqual(h.apply(self.s,pa)["status"],"MOCK_CAS_READBACK_ONLY_NO_AUTHORITY")
        self.assertEqual(h.apply(self.s,pb)["status"],"WAIT_PRECAS_UNCONFIRMED")
        self.assertEqual(h.count,1)
        fresh=h.read()
        self.assertEqual(h.apply(fresh,self.proposed(fresh,self.b))["status"],
                         "MOCK_CAS_READBACK_ONLY_NO_AUTHORITY")
    def test_same_work_join(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        self.assertEqual(claim(h.read(),self.a,NOW)["decision"],"JOIN_UNVERIFIED")
    def test_same_work_other_identity_denied(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        forged=copy.deepcopy(self.a);forged.update(dict(zip(("owner_id","run_id","nonce"),B)))
        self.assertEqual(claim(h.read(),forged,NOW)["decision"],"WAIT_WORK_ID_OWNED")
    def test_same_actor_second_work_denied(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        self.b["owner_id"]=self.a["owner_id"]
        self.assertTrue(claim(h.read(),self.b,NOW)["decision"].startswith("WAIT_INVALID"))
    def test_same_file_denied(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        self.b["scope"]["write_paths"]=["tools/alpha.py"]
        self.assertEqual(claim(h.read(),self.b,NOW)["decision"],"WAIT_WRITE_COLLISION")
    def test_case_alias_denied(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        self.b["scope"]["write_paths"]=["TOOLS/ALPHA.PY"]
        self.assertEqual(claim(h.read(),self.b,NOW)["decision"],"WAIT_WRITE_COLLISION")
    def test_shared_semantic_resource_denied(self):
        h=FakeHost(self.s)
        self.a["scope"]["shared_resources"]=["toy:world-state"]
        self.b["scope"]["shared_resources"]=["toy:world-state"]
        h.apply(self.s,self.proposed(self.s,self.a))
        self.assertEqual(claim(h.read(),self.b,NOW)["decision"],"WAIT_SEMANTIC_COLLISION")
    def test_protected_path_denied_even_no_writers(self):
        self.a["scope"]["write_paths"]=[".github/workflows/main.yml"]
        self.assertTrue(claim(self.s,self.a,NOW)["decision"].startswith("WAIT_INVALID"))
    def test_legacy_holder_prevents_shadow(self):
        self.s["state"]["holder"]={"kind":"META"}
        self.assertTrue(claim(self.s,self.a,NOW)["decision"].startswith("WAIT_INVALID"))
    def test_three_slots_denied(self):
        h=self.two()
        self.assertEqual(claim(h.read(),self.c,NOW)["decision"],"WAIT_CAPACITY")
    def test_main_base_drift_denied(self):
        self.a["scope"]["base_sha"]="c"*40
        self.assertTrue(claim(self.s,self.a,NOW)["decision"].startswith("WAIT_INVALID"))
    def test_foreign_repository_denied(self):
        self.a["scope"]["repository"]="other/project"
        self.assertTrue(claim(self.s,self.a,NOW)["decision"].startswith("WAIT_INVALID"))
    def test_nonce_not_uuid_denied(self):
        self.a["nonce"]="fake-chat-run"
        self.assertTrue(claim(self.s,self.a,NOW)["decision"].startswith("WAIT_INVALID"))
    def test_expired_incumbent_not_taken_over(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        self.b["expires_at"]="2026-11-08T00:51:00Z"
        self.assertTrue(claim(h.read(),self.b,"2026-11-08T00:31:00Z")["decision"].startswith("WAIT_INVALID"))
    def test_release_foreign_denied(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        self.assertTrue(release(h.read(),surrender(self.b),NOW)["decision"].startswith("WAIT_INVALID"))
    def test_release_own_preserves_other(self):
        h=self.two()
        original=h.read()
        p=release(original,surrender(self.a),NOW)
        self.assertEqual(p["decision"],"SHADOW_RELEASE_CAS_PROPOSAL")
        self.assertEqual(h.apply(original,p)["status"],"MOCK_CAS_READBACK_ONLY_NO_AUTHORITY")
        self.assertEqual(h.read()["state"][KEY]["entries"][0]["scope"]["work_id"],"beta-work")
    def test_expired_own_release_requires_proof(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        self.assertTrue(release(h.read(),surrender(self.a),"2026-11-08T00:30:00Z")["decision"].startswith("WAIT_INVALID"))
    def test_ack_failure_no_retry(self):
        p=self.proposed(self.s,self.a)
        res=apply_once(self.s,p,read=lambda:self.s,
                       cas=lambda a,b:None,clock=lambda:LATER,requested_at=NOW)
        self.assertEqual(res["status"],"WAIT_CAS_CONFLICT_OR_BAD_ACK")
    def test_exception_no_retry(self):
        p=self.proposed(self.s,self.a)
        def fail(a,b):raise RuntimeError("lost ack")
        res=apply_once(self.s,p,read=lambda:self.s,cas=fail,
                       clock=lambda:LATER,requested_at=NOW)
        self.assertEqual(res["status"],"WAIT_CAS_ACK_UNKNOWN")
    def test_fake_ack_without_readback_not_accepted(self):
        p=self.proposed(self.s,self.a)
        res=apply_once(self.s,p,read=lambda:self.s,cas=lambda a,b:"c"*40,
                       clock=lambda:LATER,requested_at=NOW)
        self.assertEqual(res["status"],"WAIT_CAS_READBACK_UNKNOWN")
    def test_clock_drift_no_cas(self):
        h=FakeHost(self.s)
        res=h.apply(self.s,self.proposed(self.s,self.a),"2026-11-08T03:00:00Z")
        self.assertEqual(res["status"],"WAIT_PRECAS_UNCONFIRMED")
        self.assertEqual(h.count,0)
    def test_malformed_entry_denied(self):
        self.s["state"][KEY]={"schema":1,"entries":[{"fake":1}]}
        self.assertTrue(claim(self.s,self.a,NOW)["decision"].startswith("WAIT_INVALID"))
    def test_proposal_cannot_mutate_security_policy(self):
        p=self.proposed(self.s,self.a)
        p["state"]["policy"]={"keep":False}
        h=FakeHost(self.s)
        self.assertEqual(h.apply(self.s,p)["status"],"WAIT_PRECAS_UNCONFIRMED")
        self.assertEqual(h.count,0)
    def test_proposal_cannot_mutate_other_lease(self):
        h=FakeHost(self.s)
        h.apply(self.s,self.proposed(self.s,self.a))
        fresh=h.read()
        p=self.proposed(fresh,self.b)
        p["state"][KEY]["entries"][0]["nonce"]=C[2]
        self.assertEqual(h.apply(fresh,p)["status"],"WAIT_PRECAS_UNCONFIRMED")

if __name__=="__main__": unittest.main()
