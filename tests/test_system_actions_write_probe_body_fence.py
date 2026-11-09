"""PR163: strict per-mutation request body, no network or production credentials.

These original-source adversarial controls must fail on the former path-only
fence and pass only when exact operation payloads are checked pre-write.
"""
import base64
import copy
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import system_actions_write_probe as p

MAIN = "a" * 40
CLAIM = "b" * 40
OWNER = "2fc73166-aceb-47ab-bb29-e355c3a3bda4"
RUN = 41199998877
SCOPE = {"owner":OWNER, "main":MAIN,
         "branch":f"controller/gha-write-probe-{RUN}-a1",
         "run_id":RUN, "attempt":1}
PATH = f"/contents/ops/probes/gha-write-{RUN}-a1.json"
PR_BODY = ("Non-production, no game files, no AI inference, no merge authorization. "
           "Confirm separate reviewer and delete only by authorized owner after audit.")


def canonical():
    probe = {"schema":1,"kind":"OWNER_MANUAL_GHA_CAPABILITY_PROBE_ONLY",
             "source_main_sha":MAIN,"github_run_id":RUN,
             "run_attempt":1,"status":"NO_AI_NO_GAME_CHANGE"}
    content=base64.b64encode((json.dumps(probe,sort_keys=True)+"\n").encode()).decode()
    return [
        {"ref":"refs/heads/"+SCOPE["branch"],"sha":MAIN},
        {"message":"probe: isolated owner-manual write only",
         "branch":SCOPE["branch"],"content":content},
        {"title":"[PROBE ONLY] Owner-manual GitHub Actions branch/PR permission",
         "head":SCOPE["branch"],"base":"main","draft":True,
         "body":PR_BODY},
    ]


class FakeAPI:
    def __init__(self):
        self.calls=[]
    def call(self, method, path, body=None):
        self.calls.append((method,path,copy.deepcopy(body)))
        return {"number":7} if method=="POST" and path=="/pulls" else {}


class StrictRequestBodyTests(unittest.TestCase):
    def setUp(self):
        self.api=FakeAPI()
        s={"epoch":396,"holder":{"kind":"CONTROLLER","owner_id":OWNER,
           "epoch":396,"task_id":None,"work_branch":SCOPE["branch"],"base_main_sha":MAIN}}
        ps=[
            patch.object(p,"sha_ref",side_effect=lambda api,name:MAIN if name=="main" else CLAIM),
            patch.object(p,"state_at",return_value=s),
            patch.object(p,"owns",return_value=True),
            patch.object(p,"now",return_value="2026-11-02T00:15:00Z"),
        ]
        for x in ps:x.start();self.addCleanup(x.stop)

    def new(self):
        return p._PerWriteLeaseFence(self.api,SCOPE,396,CLAIM)

    def at(self,stage):
        w=self.new()
        bodies=canonical()
        ops=[("POST","/git/refs"),("PUT",PATH),("POST","/pulls")]
        for i in range(stage):
            w.call(*ops[i],bodies[i])
        self.api.calls.clear()
        return w,ops[stage],bodies[stage]

    def reject_at(self,stage,modifier):
        fence,op,b=self.at(stage)
        b=copy.deepcopy(b)
        modifier(b)
        with self.assertRaisesRegex(p.ProbeError,"BODY"):
            fence.call(*op,b)
        self.assertEqual(self.api.calls,[],"invalid body must not hit transport")

    def test_legitimate_canonical_writer_still_valid(self):
        w=self.new()
        self.assertEqual(p.create_branch_probe(w,SCOPE),7)
        self.assertEqual([(method,path) for method,path,_ in self.api.calls],
            [("POST","/git/refs"),("PUT",PATH),("POST","/pulls")])
        self.assertEqual([b for _,_,b in self.api.calls],canonical())

    def test_create_main_ref_denied(self):
        self.reject_at(0,lambda b:b.update(ref="refs/heads/main"))

    def test_create_wrong_source_sha_denied(self):
        self.reject_at(0,lambda b:b.update(sha="c"*40))

    def test_create_extra_key_denied(self):
        self.reject_at(0,lambda b:b.update(force=True))

    def test_create_wrong_ref_type_denied(self):
        self.reject_at(0,lambda b:b.update(ref=["refs/heads/main"]))

    def test_create_empty_body_denied(self):
        self.reject_at(0,lambda b:b.clear())

    def test_put_on_main_denied(self):
        self.reject_at(1,lambda b:b.update(branch="main"))

    def test_put_foreign_content_denied(self):
        self.reject_at(1,lambda b:b.update(content=base64.b64encode(b"UNREVIEWED").decode()))

    def test_put_extra_key_denied(self):
        self.reject_at(1,lambda b:b.update(sha="d"*40))

    def test_put_wrong_commit_message_denied(self):
        self.reject_at(1,lambda b:b.update(message="edit source"))

    def test_put_untyped_content_denied(self):
        self.reject_at(1,lambda b:b.update(content={"base64":"invalid"}))

    def test_pr_not_draft_denied(self):
        self.reject_at(2,lambda b:b.update(draft=False))

    def test_pr_bool_spoof_denied(self):
        self.reject_at(2,lambda b:b.update(draft=1))

    def test_pr_foreign_head_denied(self):
        self.reject_at(2,lambda b:b.update(head="foreign-branch"))

    def test_pr_wrong_base_denied(self):
        self.reject_at(2,lambda b:b.update(base="release"))

    def test_pr_extra_key_denied(self):
        self.reject_at(2,lambda b:b.update(maintainer_can_modify=True))

    def test_pr_modified_body_denied(self):
        self.reject_at(2,lambda b:b.update(body="please merge urgently"))

    def test_denied_body_does_not_consume_one_shot(self):
        fence,op,body=self.at(0)
        invalid=copy.deepcopy(body);invalid["ref"]="refs/heads/main"
        with self.assertRaises(p.ProbeError):fence.call(*op,invalid)
        self.assertEqual(self.api.calls,[])
        fence.call(*op,body)
        self.assertEqual(len(self.api.calls),1)

if __name__=="__main__":unittest.main()
