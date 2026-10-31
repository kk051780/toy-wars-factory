"""Read-only original GitHub PR inventory collector, provider-independent regressions."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from system_parallel_pr_github_collector import (
    ROOT as API, REPO, REPO_ID, MAIN_REF, OPEN_PRS,
    GitHubGet, NoRedirect, CollectorHold, collect, parse_json, main,
)

MAIN = 'a' * 40
HEAD = 'b' * 40

def pr_row(n=147, head=HEAD, base='main', base_sha=MAIN):
    return {'number':n,'state':'open',
            'head':{'sha':head,'repo':{'full_name':REPO}},
            'base':{'ref':base,'sha':base_sha,'repo':{'full_name':REPO}}}

def fixture():
    urls = {
        API:{'id':REPO_ID,'full_name':REPO,'private':True},
        MAIN_REF:{'ref':'refs/heads/main','object':{'type':'commit','sha':MAIN}},
        OPEN_PRS:[pr_row()],
        API + '/pulls/147/files?per_page=100&page=1':[
            {'filename':'tools/existing.py','status':'modified'}],
    }
    return urls

class FakeOriginalGET:
    def __init__(self, urls):
        self.urls = urls
        self.reads = []
        self.twice = {}

    def __call__(self, url):
        self.reads.append(url)
        if url not in self.urls:
            raise CollectorHold('MISSING_ORIGINAL_GET')
        value = self.urls[url]
        if url in self.twice and self.reads.count(url) > 1:
            return deepcopy(self.twice[url])
        return deepcopy(value)


def candidate(path='tools/new_audit.py'):
    return {'branch':'controller/readonly-collector','paths':[path]}

class PrCollectorTests(unittest.TestCase):
    def test_changed_stacked_parent_sha_rejected_even_if_main_head_stable(self):
        row=pr_row(base='controller/parent', base_sha='d'*40)
        f=fixture();f[OPEN_PRS]=[row]
        q=FakeOriginalGET(f)
        q.twice[OPEN_PRS]=[pr_row(base='controller/parent', base_sha='e'*40)]
        with self.assertRaisesRegex(CollectorHold, 'ORIGINAL_SNAPSHOT_MISMATCH'):
            collect(q,candidate())

    def test_absent_base_sha_rejected_by_reader(self):
        f=fixture()
        del f[OPEN_PRS][0]['base']['sha']
        with self.assertRaisesRegex(CollectorHold, 'ORIGINAL_SNAPSHOT_MISMATCH'):
            collect(FakeOriginalGET(f),candidate())

    def test_main_sha_drift_inside_pr_record_rejected(self):
        f=fixture()
        f[OPEN_PRS][0]['base']['sha']='c'*40
        with self.assertRaisesRegex(CollectorHold, 'ORIGINAL_SNAPSHOT_MISMATCH'):
            collect(FakeOriginalGET(f),candidate())

    def test_unchanged_stacked_parent_sha_advisory_only(self):
        f=fixture();f[OPEN_PRS]=[pr_row(base='controller/parent',base_sha='d'*40)]
        report=collect(FakeOriginalGET(f),candidate())
        self.assertEqual(report['decision'],'CLEAR_ADVISORY')
        self.assertFalse(report['may_write'])

    def test_clear_is_only_advisory_not_permission(self):
        read=FakeOriginalGET(fixture())
        x=collect(read,candidate())
        self.assertEqual(x['decision'],'CLEAR_ADVISORY')
        for key in ('may_write','may_merge','may_dispatch','may_publish_roblox','provider_authenticated'):
            self.assertIs(x[key],False)
        self.assertEqual(x['host_provider_authentication'],'NOT_ATTESTED')
        self.assertEqual(x['get_count'],6)
        self.assertEqual(len(read.reads),6)
        self.assertEqual(read.reads[0],API)
        self.assertEqual(read.reads[-1],MAIN_REF)

    def test_exact_path_conflict(self):
        f=fixture()
        f[API+'/pulls/147/files?per_page=100&page=1']=[{'filename':'tools/new_audit.py','status':'added'}]
        x=collect(FakeOriginalGET(f),candidate())
        self.assertEqual(x['decision'],'BLOCK_OVERLAP')
        self.assertEqual(x['collisions'][0]['kind'],'EXACT')

    def test_prefix_path_conflict(self):
        f=fixture()
        f[API+'/pulls/147/files?per_page=100&page=1']=[{'filename':'tools','status':'modified'}]
        x=collect(FakeOriginalGET(f),candidate())
        self.assertEqual(x['decision'],'BLOCK_OVERLAP')
        self.assertEqual(x['collisions'][0]['kind'],'PATH_PREFIX')

    def test_changed_main_ref_rejected(self):
        r=FakeOriginalGET(fixture())
        r.twice[MAIN_REF]={'ref':'refs/heads/main','object':{'type':'commit','sha':'c'*40}}
        with self.assertRaisesRegex(CollectorHold,'ORIGINAL_SNAPSHOT_MISMATCH'):
            collect(r,candidate())

    def test_changed_pr_head_rejected(self):
        r=FakeOriginalGET(fixture())
        r.twice[OPEN_PRS]=[pr_row(head='c'*40)]
        with self.assertRaisesRegex(CollectorHold,'ORIGINAL_SNAPSHOT_MISMATCH'):
            collect(r,candidate())

    def test_added_pr_rejected(self):
        r=FakeOriginalGET(fixture())
        r.twice[OPEN_PRS]=[pr_row(),pr_row(n=148)]
        with self.assertRaisesRegex(CollectorHold,'ORIGINAL_SNAPSHOT_MISMATCH'):
            collect(r,candidate())

    def test_repo_private_and_id_required(self):
        for key,value in [('id',REPO_ID+1),('private',False),('full_name','bad/repo')]:
            with self.subTest(key=key):
                f=fixture();f[API][key]=value
                with self.assertRaisesRegex(CollectorHold,'REPOSITORY_ID_MISMATCH'):
                    collect(FakeOriginalGET(f),candidate())

    def test_pagination_pr_page_100_fails_closed(self):
        f=fixture();f[OPEN_PRS]=[pr_row(n=n) for n in range(1,101)]
        with self.assertRaisesRegex(CollectorHold,'PR_LIST_PAGINATION_REQUIRED'):
            collect(FakeOriginalGET(f),candidate())

    def test_pagination_files_page_100_fails_closed(self):
        f=fixture()
        f[API+'/pulls/147/files?per_page=100&page=1']=[
            {'filename':f'tools/file{n}.py','status':'added'} for n in range(100)]
        with self.assertRaisesRegex(CollectorHold,'FILE_LIST_PAGINATION_OR_MISSING'):
            collect(FakeOriginalGET(f),candidate())

    def test_missing_files_page_fails_closed(self):
        f=fixture();f.pop(API+'/pulls/147/files?per_page=100&page=1')
        with self.assertRaisesRegex(CollectorHold,'MISSING_ORIGINAL_GET'):
            collect(FakeOriginalGET(f),candidate())

    def test_duplicate_pr_number_does_not_call_files(self):
        f=fixture();f[OPEN_PRS].append(pr_row())
        q=FakeOriginalGET(f)
        with self.assertRaisesRegex(CollectorHold,'INVALID_PR_NUMBER'):
            collect(q,candidate())
        self.assertNotIn(API+'/pulls/147/files?per_page=100&page=1',q.reads)

    def test_foreign_pr_repo_rejected(self):
        f=fixture();f[OPEN_PRS][0]['head']['repo']['full_name']='evil/fork'
        with self.assertRaisesRegex(CollectorHold,'ORIGINAL_SNAPSHOT_MISMATCH'):
            collect(FakeOriginalGET(f),candidate())

    def test_rename_old_path_included(self):
        f=fixture()
        f[API+'/pulls/147/files?per_page=100&page=1']=[{
            'filename':'tools/new_name.py','previous_filename':'tools/new_audit.py','status':'renamed'}]
        x=collect(FakeOriginalGET(f),candidate())
        self.assertEqual(x['decision'],'BLOCK_OVERLAP')

    def test_stacked_pr_preserved(self):
        f=fixture();f[OPEN_PRS][0]['base']['ref']='controller/parent'
        x=collect(FakeOriginalGET(f),candidate())
        self.assertEqual(x['stacked_prs_checked'],1)

    def test_wrong_main_ref_shape_rejected(self):
        f=fixture();f[MAIN_REF]['object']['type']='blob'
        with self.assertRaisesRegex(CollectorHold,'INVALID_MAIN_REF'):
            collect(FakeOriginalGET(f),candidate())

    def test_invalid_candidate_does_not_read_api(self):
        f=FakeOriginalGET(fixture())
        with self.assertRaisesRegex(CollectorHold,'INVALID_CANDIDATE'):
            collect(f,{'branch':'controller/test','paths':['../secret']})
        self.assertEqual(f.reads,[])

    def test_get_url_allowlist(self):
        yes=[API,MAIN_REF,OPEN_PRS,API+'/pulls/1/files?per_page=100&page=1']
        no=[API+'/issues',API+'/pulls/1',API+'/pulls/0/files?per_page=100&page=1',
            API+'/pulls/1/files?per_page=100&page=2',
            API+'/pulls/1/files?per_page=100&page=1&secret=x',
            'https://evil.example.com/',API+'/git/ref/heads/other',
            API+'/contents/secret',123,None]
        for url in yes:self.assertTrue(GitHubGet.allowed_url(url),url)
        for url in no:self.assertFalse(GitHubGet.allowed_url(url),url)

    def test_token_required(self):
        for token in ('',None,123):
            with self.assertRaisesRegex(CollectorHold,'TOKEN_NOT_AVAILABLE'):
                GitHubGet(token)

    def test_parser_rejects_duplicate_fields_and_nonfinite(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',b'{', b'\xff'):
            with self.assertRaises(CollectorHold, msg=repr(raw)):
                parse_json(raw)
        self.assertEqual(parse_json(b'{"x":[1]}'),{'x':[1]})

    def test_http_transport_get_only_no_redirect(self):
        self.assertIsNone(NoRedirect().redirect_request(None,None,None,None,None,None,None))
        class Resp:
            def __enter__(self):return self
            def __exit__(self,*_):pass
            def getcode(self):return 200
            def read(self,n):return b'{"ok":true}'
        calls=[]
        def opener(req,timeout):
            calls.append((req.get_method(),req.full_url,timeout,req.headers))
            return Resp()
        g=GitHubGet('dummy-token',opener=opener)
        self.assertEqual(g(API),{'ok':True})
        self.assertEqual(calls[0][0],'GET')
        self.assertEqual(calls[0][1],API)
        self.assertEqual(calls[0][2],12)
        self.assertNotIn('dummy-token',repr(g(API)))
        with self.assertRaisesRegex(CollectorHold,'URL_NOT_ALLOWLISTED'):
            g('https://attacker.example/')

    def test_empty_pr_inventory_is_only_advisory(self):
        f=fixture();f[OPEN_PRS]=[]
        q=FakeOriginalGET(f)
        x=collect(q,candidate())
        self.assertEqual(x['checked_open_prs'],0)
        self.assertEqual(x['decision'],'CLEAR_ADVISORY')
        self.assertEqual(x['get_count'],5)
        self.assertFalse(x['may_write'])

    def test_fifty_three_prs_bounded_fifty_eight_gets(self):
        f=fixture()
        f[OPEN_PRS]=[pr_row(n=n) for n in range(1,54)]
        f.pop(API+'/pulls/147/files?per_page=100&page=1')
        for n in range(1,54):
            f[f'{API}/pulls/{n}/files?per_page=100&page=1']=[
                {'filename':f'tools/unrelated_{n}.py','status':'modified'}]
        q=FakeOriginalGET(f)
        x=collect(q,candidate())
        self.assertEqual(x['checked_open_prs'],53)
        self.assertEqual(x['get_count'],58)
        self.assertEqual(len(q.reads),58)
        self.assertFalse(x['grant_write_authority'])

    def test_changed_pr_base_branch_rejected(self):
        r=FakeOriginalGET(fixture())
        r.twice[OPEN_PRS]=[pr_row(base='controller/other-parent')]
        with self.assertRaisesRegex(CollectorHold,'ORIGINAL_SNAPSHOT_MISMATCH'):
            collect(r,candidate())

    def test_alias_candidate_rejected_before_any_get(self):
        r=FakeOriginalGET(fixture())
        with self.assertRaisesRegex(CollectorHold,'INVALID_CANDIDATE'):
            collect(r,{'branch':'controller/readonly',
                       'paths':['tools/new_audit.py','Tools/New_Audit.py']})
        self.assertEqual(r.reads,[])

if __name__=='__main__':
    unittest.main()
