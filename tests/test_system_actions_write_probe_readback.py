"""Exact-ref readback required after isolated GitHub Actions branch and draft PR creation.

Synthetic GET results are not provider attestation; this is fail-closed contract QA.
"""
from __future__ import annotations
import base64
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1] / "tools"))
import system_actions_write_probe as target

MAIN="a"*40
HEAD="b"*40
SCOPE={"main":MAIN,"branch":"controller/gha-write-probe-41199998877-a1",
       "run_id":41199998877,"attempt":1}
FILENAME="ops/probes/gha-write-41199998877-a1.json"
PAYLOAD={"schema":1,"kind":"OWNER_MANUAL_GHA_CAPABILITY_PROBE_ONLY",
         "source_main_sha":MAIN,"github_run_id":SCOPE["run_id"],
         "run_attempt":1,"status":"NO_AI_NO_GAME_CHANGE"}
RAW=(json.dumps(PAYLOAD,sort_keys=True)+"\n").encode()
BLOB=hashlib.sha1(b"blob "+str(len(RAW)).encode()+b"\0"+RAW).hexdigest()

class API:
    def __init__(self):
        self.calls=[]
        self.main_reads=0
        self.main=MAIN
        self.branch=HEAD
        self.commit={"sha":HEAD,"parents":[{"sha":MAIN}]}
        self.compare={"status":"ahead","ahead_by":1,"behind_by":0,"total_commits":1,
                      "files":[{"filename":FILENAME,"status":"added"}]}
        self.file={"type":"file","encoding":"base64","content":base64.b64encode(RAW).decode(),
                   "size":len(RAW),"sha":BLOB}
        self.pr={"number":123,"state":"open","draft":True,
                 "head":{"ref":SCOPE["branch"],"sha":HEAD,"repo":{"full_name":target.REPO}},
                 "base":{"ref":"main","sha":MAIN,"repo":{"full_name":target.REPO}}}
        self.change_after_first_main=False
    def call(self,method,path,body=None):
        self.calls.append((method,path,deepcopy(body)))
        if (method,path)==("GET","/git/ref/heads/main"):
            self.main_reads+=1
            sha="f"*40 if self.change_after_first_main and self.main_reads>1 else self.main
            return {"object":{"sha":sha}}
        if (method,path)==("GET","/git/ref/heads/"+SCOPE["branch"]):
            return {"object":{"sha":self.branch}}
        if (method,path)==("GET","/git/commits/"+self.branch):
            return deepcopy(self.commit)
        if (method,path)==("GET","/compare/"+MAIN+"..."+self.branch):
            return deepcopy(self.compare)
        if (method,path)==("GET","/contents/"+FILENAME+"?ref="+self.branch):
            return deepcopy(self.file)
        if (method,path)==("GET","/pulls/123"):
            return deepcopy(self.pr)
        if (method,path)==("POST","/git/refs"):
            return {"ref":body["ref"]}
        if (method,path)==("PUT","/contents/"+FILENAME):
            return {"commit":{"sha":HEAD}}
        if (method,path)==("POST","/pulls"):
            return {"number":123}
        raise AssertionError("unexpected method/path: "+str((method,path)))

class ReadbackTests(unittest.TestCase):
    def setUp(self):
        self.api=API()
    def check(self):
        return target.verify_created_probe(self.api,SCOPE,123)
    def deny(self):
        with self.assertRaises(target.ProbeError):
            self.check()
    def test_exact_readback_returns_verified_number(self):
        self.assertEqual(self.check(),123)
        self.assertEqual(self.api.main_reads,2)
        self.assertTrue(all(call[0]=="GET" for call in self.api.calls))
    def test_wrong_branch_head(self):
        self.api.branch=MAIN
        self.deny()
    def test_unverified_parent(self):
        self.api.commit["parents"]=[{"sha":"c"*40}]
        self.deny()
    def test_multi_parent_commit(self):
        self.api.commit["parents"]=[{"sha":MAIN},{"sha":"c"*40}]
        self.deny()
    def test_commit_sha_mismatch(self):
        self.api.commit["sha"]="d"*40
        self.deny()
    def test_extra_changed_file(self):
        self.api.compare["files"].append({"filename":"src/Main.lua","status":"modified"})
        self.deny()
    def test_compare_not_single_commit(self):
        self.api.compare["total_commits"]=2
        self.deny()
    def test_compare_not_ahead(self):
        self.api.compare["status"]="diverged"
        self.deny()
    def test_content_modified(self):
        raw=RAW+b"extra"
        self.api.file["content"]=base64.b64encode(raw).decode()
        self.api.file["size"]=len(raw)
        self.deny()
    def test_content_blob_hash_spoofed(self):
        self.api.file["sha"]="e"*40
        self.deny()
    def test_content_encoding_invalid(self):
        self.api.file["encoding"]="utf-8"
        self.deny()
    def test_content_missing_invalid_base64(self):
        self.api.file["content"]="@@@"
        self.deny()
    def test_head_repository_foreign(self):
        self.api.pr["head"]["repo"]["full_name"]="foreign/repo"
        self.deny()
    def test_pr_not_draft(self):
        self.api.pr["draft"]=False
        self.deny()
    def test_wrong_base_or_pr_head(self):
        for key in ("base","head"):
            with self.subTest(key=key):
                a=API(); a.pr[key]["sha"]="f"*40
                with self.assertRaises(target.ProbeError):
                    target.verify_created_probe(a,SCOPE,123)
    def test_main_moved_during_readback(self):
        self.api.change_after_first_main=True
        self.deny()
    def test_api_inconsistent_pr_number(self):
        self.api.pr["number"]=124
        self.deny()
    def test_bool_pr_number_rejected(self):
        with self.assertRaises(target.ProbeError):
            target.verify_created_probe(self.api,SCOPE,True)
    def test_actual_create_branch_probe_requires_readback(self):
        self.assertEqual(target.create_branch_probe(self.api,SCOPE),123)
        self.assertIn(("GET","/pulls/123",None),self.api.calls)
        self.assertIn(("GET","/contents/"+FILENAME+"?ref="+HEAD,None),self.api.calls)

if __name__=="__main__":unittest.main()
