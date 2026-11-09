"""PR163: a GitHub Actions token denied POST /pulls may still have a
verified branch-only staging result, never a PR/approval/merge receipt.

Pure offline GitHub API mocks; no user credentials, network or actual Actions.
"""
import base64
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import system_actions_write_probe as probe

MAIN="a"*40
BRANCH_SHA="b"*40
RUN=41199998877
BRANCH=f"controller/gha-write-probe-{RUN}-a1"
SCOPE={"main":MAIN,"branch":BRANCH,"run_id":RUN,"attempt":1}
PATH=f"ops/probes/gha-write-{RUN}-a1.json"
BODY={"schema":1,"kind":"OWNER_MANUAL_GHA_CAPABILITY_PROBE_ONLY",
      "source_main_sha":MAIN,"github_run_id":RUN,"run_attempt":1,
      "status":"NO_AI_NO_GAME_CHANGE"}
RAW=(json.dumps(BODY,sort_keys=True)+"\n").encode()
BLOB=hashlib.sha1(b"blob "+str(len(RAW)).encode()+b"\0"+RAW).hexdigest()

class Provider:
    def __init__(self,pr_error="GITHUB_HTTP_403",tamper=None):
        self.pr_error=pr_error
        self.tamper=tamper
        self.requests=[]
    def call(self,method,path,body=None):
        self.requests.append((method,path))
        if method=="GET" and path=="/git/ref/heads/main":
            return {"object":{"sha":"c"*40 if self.tamper=="main" else MAIN}}
        if method=="GET" and path=="/git/ref/heads/"+BRANCH:
            return {"object":{"sha":BRANCH_SHA}}
        if method=="GET" and path=="/git/commits/"+BRANCH_SHA:
            return {"sha":BRANCH_SHA,"parents":[{"sha":MAIN}]}
        if method=="GET" and path==f"/compare/{MAIN}...{BRANCH_SHA}":
            files=[{"filename":PATH,"status":"added"}]
            if self.tamper=="extra_file":files.append({"filename":"src/backdoor.lua","status":"added"})
            return {"status":"ahead","ahead_by":1,"behind_by":0,
                    "total_commits":1,"files":files}
        if method=="GET" and path==f"/contents/{PATH}?ref={BRANCH_SHA}":
            raw=b"forged" if self.tamper=="file" else RAW
            return {"type":"file","encoding":"base64","size":len(raw),
                    "sha":BLOB,"content":base64.b64encode(raw).decode()}
        if method=="POST" and path=="/git/refs":
            if self.tamper=="branch_denied":raise probe.ProbeError("GITHUB_HTTP_403")
            return {"ref":body["ref"]}
        if method=="PUT" and path=="/contents/"+PATH:
            if self.tamper=="file_denied":raise probe.ProbeError("GITHUB_HTTP_403")
            return {"commit":{"sha":BRANCH_SHA}}
        if method=="POST" and path=="/pulls":
            raise probe.ProbeError(self.pr_error)
        raise AssertionError("unexpected simulated API call: "+method+" "+path)

class RestrictedHostFallbackTests(unittest.TestCase):
    def test_post_pulls_403_returns_branch_only_instead_of_false_total_failure(self):
        api=Provider()
        self.assertIsNone(probe.create_branch_probe(api,SCOPE))
        self.assertEqual(api.requests[-1],("POST","/pulls"))
        self.assertEqual(sum(method=="POST" and path=="/pulls" for method,path in api.requests),1)

    def test_post_pulls_500_is_not_downgraded_to_staged_success(self):
        api=Provider(pr_error="GITHUB_HTTP_500")
        with self.assertRaisesRegex(probe.ProbeError,"^GITHUB_HTTP_500$"):
            probe.create_branch_probe(api,SCOPE)

    def test_branch_creation_denial_does_not_claim_staging(self):
        api=Provider(tamper="branch_denied")
        with self.assertRaisesRegex(probe.ProbeError,"GITHUB_HTTP_403"):
            probe.create_branch_probe(api,SCOPE)
        self.assertNotIn(("POST","/pulls"),api.requests)

    def test_file_write_denial_does_not_claim_staging(self):
        api=Provider(tamper="file_denied")
        with self.assertRaisesRegex(probe.ProbeError,"GITHUB_HTTP_403"):
            probe.create_branch_probe(api,SCOPE)
        self.assertNotIn(("POST","/pulls"),api.requests)

    def test_staged_branch_requires_one_parent_exact_single_file_and_blob(self):
        api=Provider()
        self.assertEqual(probe.verify_staged_probe(api,SCOPE),BRANCH_SHA)
        self.assertEqual(api.requests[-2:],[("GET","/git/ref/heads/main"),("GET","/git/ref/heads/"+BRANCH)])

    def test_staged_branch_rejects_hidden_second_file(self):
        with self.assertRaisesRegex(probe.ProbeError,"BRANCH_DIFF_UNVERIFIED"):
            probe.verify_staged_probe(Provider(tamper="extra_file"),SCOPE)

    def test_staged_branch_rejects_untrusted_file_bytes(self):
        with self.assertRaisesRegex(probe.ProbeError,"PROBE_FILE_UNVERIFIED"):
            probe.verify_staged_probe(Provider(tamper="file"),SCOPE)

    def test_staged_branch_rejects_main_ref_drift(self):
        with self.assertRaisesRegex(probe.ProbeError,"MAIN_CHANGED_AFTER_WRITE"):
            probe.verify_staged_probe(Provider(tamper="main"),SCOPE)

if __name__=="__main__":
    unittest.main()
