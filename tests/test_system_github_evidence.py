"""Actual collector, two synthetic games, adversarial provider responses.

No fixture/transport flag is a live authentication receipt. Tests do not use
network access, credentials, real dispatch, accepted test changes or PR #51.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))
import system_github_evidence as target

NOW = "2026-10-27T11:50:00Z"
RUN = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
MAIN, COORD, HEAD, MTREE, CTREE = (c * 40 for c in "abcde")


def fixtures(second=False):
    project = json.loads((ROOT / "studio_autopilot/projects/toy_wars.json").read_text())
    project["game_id"] = "orbit-parkour" if second else "clockwork-pve"
    project["repository"] = "example/orbit" if second else "example/clockwork"
    project["coordination_ref"] = "orbit-coordinator" if second else "clock-coordinator"
    project["roles"] = {"author": ("4" if second else "1") * 32,
                        "reviewer": ("5" if second else "2") * 32,
                        "meta": ("6" if second else "3") * 32}
    repo = project["repository"]
    rolemap = {"WORKER": project["roles"]["author"], "META": project["roles"]["meta"],
               "REVIEWER": project["roles"]["reviewer"]}
    policy = {"repository": repo, "queue_version": 4, "task_id": rolemap["WORKER"],
              "branch_prefix": "auto/game-", "system_review": {"task_id": rolemap["META"],
              "branch_prefix": "auto/system-"}, "integration": {"task_id": rolemap["REVIEWER"]}}
    state = {"schema": 1, "task_id": rolemap["WORKER"], "epoch": 7,
             "authorized_tasks": rolemap, "holder": None}
    data = {}
    def put(path, obj):
        data[path] = target.Response(200, json.dumps(obj))
    def blob(obj):
        raw = json.dumps(obj, sort_keys=True)
        digest = hashlib.sha1(b"blob " + str(len(raw.encode())).encode() + b"\0" + raw.encode()).hexdigest()
        data["/git/blobs/" + digest] = target.Response(200, raw)
        return digest
    msha, psha, csha = blob(project), blob(policy), blob(state)
    def entry(path, digest):
        return {"path": path, "mode": "100644", "type": "blob", "sha": digest}
    put("", {"full_name": repo, "fork": False})
    for branch, digest in (("main", MAIN), (project["coordination_ref"], COORD)):
        put("/git/ref/heads/" + branch, {"ref": "refs/heads/" + branch,
                                        "object": {"sha": digest, "type": "commit"}})
    put("/git/commits/" + MAIN, {"sha": MAIN, "tree": {"sha": MTREE}})
    put("/git/commits/" + COORD, {"sha": COORD, "tree": {"sha": CTREE}})
    manifest = "studio_autopilot/projects/game.json"
    put("/git/trees/" + MTREE + "?recursive=1", {"sha": MTREE, "truncated": False,
        "tree": [entry(manifest, msha), entry("config/autonomous_repair.json", psha), entry(".github/workflows/qa.yml", "9"*40)]})
    put("/git/trees/" + CTREE + "?recursive=1", {"sha": CTREE, "truncated": False,
        "tree": [entry("ops/REPAIR_COORDINATOR.json", csha)]})
    headref = "auto/system-" + RUN
    pr = {"number": 9, "state": "open", "merged": False,
          "head": {"sha": HEAD, "ref": headref, "repo": {"full_name": repo, "fork": False}},
          "base": {"sha": MAIN, "ref": "main", "repo": {"full_name": repo, "fork": False}}}
    put("/pulls/9", pr)
    put("/actions/workflows/qa.yml", {"id": 23, "path": ".github/workflows/qa.yml", "state": "active"})
    def run(i, head, branch, event):
        return {"id": i, "workflow_id": 23, "path": ".github/workflows/qa.yml", "head_sha": head, "head_branch": branch,
            "run_attempt": 1, "repository": {"full_name": repo},
            "head_repository": {"full_name": repo, "fork": False}, "event": event,
            "created_at": "2026-10-27T11:00:00Z", "updated_at": "2026-10-27T11:02:00Z",
            "status": "completed", "conclusion": "success",
            "pull_requests": [] if event == "push" else [
                {"number": 9, "head": {"sha": HEAD}, "base": {"sha": MAIN}}]}
    r, mr = run(101, HEAD, headref, "pull_request"), run(100, MAIN, "main", "push")
    put("/actions/runs/101", r)
    put("/actions/runs?head_sha=" + HEAD + "&event=pull_request&per_page=100",
        {"total_count": 1, "workflow_runs": [r]})
    put("/actions/runs?branch=main&event=push&per_page=100",
        {"total_count": 1, "workflow_runs": [mr]})
    for runobj in (r, mr):
        put(f"/actions/runs/{runobj['id']}/attempts/1/jobs?per_page=100", {"total_count": 2, "jobs": [
            {"id": runobj["id"] * 10 + n, "name": name, "run_id": runobj["id"], "run_attempt": 1,
             "head_sha": runobj["head_sha"], "status": "completed", "conclusion": "success",
             "started_at": "2026-10-27T11:00:10Z", "completed_at": "2026-10-27T11:01:59Z"}
            for n, name in enumerate(("offline", "compile_hold"))]})
    pins = {"game_id": project["game_id"], "manifest_path": manifest, "main_sha": MAIN,
            "coordinator_sha": COORD, "coordinator_blob_sha": csha, "coordinator_epoch": 7,
            "pr_number": 9, "pr_head_sha": HEAD, "pr_base_sha": MAIN, "author_role": "meta",
            "author_run_id": RUN, "ci_run_id": 101, "ci_attempt": 1, "workflow_file": "qa.yml", "workflow_id": 23}
    return project, pins, data


class FakeGET:
    def __init__(self, project, data, drift=None):
        self.prefix = "https://api.github.com/repos/" + project["repository"]
        self.data, self.calls, self.drift, self.count = data, [], drift or {}, {}

    def __call__(self, url):
        if not url.startswith(self.prefix):
            raise AssertionError("foreign URL")
        self.calls.append(url)
        path = url[len(self.prefix):]
        self.count[path] = self.count.get(path, 0) + 1
        row = deepcopy(self.data[path])
        if path in self.drift and self.count[path] >= 2:
            obj = json.loads(row.text)
            self.drift[path](obj)
            row = target.Response(200, json.dumps(obj))
        return row


def mutate(data, path, fn):
    obj = json.loads(data[path].text)
    fn(obj)
    data[path] = target.Response(200, json.dumps(obj))


class EvidenceTests(unittest.TestCase):
    def run_fixture(self, project, pins, data, *, projects=None, drift=None):
        get = FakeGET(project, data, drift)
        result = target.collect(projects or [project], pins, get, lambda: NOW)
        self.assertTrue(all(u.startswith(get.prefix) for u in get.calls))
        return result

    def rejected(self, data_path, mutation):
        p, b, d = fixtures()
        mutate(d, data_path, mutation)
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p, b, d)

    def test_two_games_use_real_collector_and_existing_planners(self):
        p, b, d = fixtures()
        q, c, e = fixtures(True)
        original = deepcopy([p, q])
        for project, pins, data in ((p, b, d), (q, c, e)):
            result = self.run_fixture(project, pins, data, projects=[p, q])
            self.assertEqual(result["verification"], "NOT_VERIFIED")
            self.assertEqual(result["main_ci"]["qa"], "PASS")
            self.assertEqual(result["pr"]["ci"]["qa"], "PASS")
            self.assertTrue(any('/git/blobs/' in row['url'] for row in result['trace']))
            self.assertTrue(any('/attempts/1/jobs' in row['url'] for row in result['trace']))
            advised = target.advisory([p, q], result)
            self.assertFalse(any(result["authority"].values()))
            self.assertFalse(any(advised["authority"].values()))
            self.assertFalse(advised["core"]["dispatch_allowed"])
            self.assertFalse(advised["scheduler"]["execution"]["dispatch_allowed"])
            self.assertIn("VERIFY_LIVE_GITHUB_EVIDENCE", advised["scheduler"]["candidates"][0]["issues"])
            self.assertEqual(advised["triage"]["state"], "INDETERMINATE")
        self.assertEqual([p, q], original)

    def test_reused_cross_game_task_is_rejected(self):
        p, b, d = fixtures()
        q, _, _ = fixtures(True)
        for role in q["roles"]:
            broken = deepcopy(q)
            broken["roles"][role] = p["roles"][role]
            with self.subTest(role=role), self.assertRaises(target.EvidenceError):
                self.run_fixture(p, b, d, projects=[p, broken])

    def test_other_game_response_cannot_be_reused(self):
        p, b, _ = fixtures()
        _, _, d = fixtures(True)
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p, b, d)

    def test_forged_authority_or_provider_label_cannot_upgrade_binding(self):
        for key in ("provider", "provider_verified", "authorization", "dispatch_allowed", "token"):
            p, b, d = fixtures()
            b[key] = True
            with self.subTest(key=key), self.assertRaises(target.EvidenceError):
                self.run_fixture(p, b, d)

    def test_same_author_reviewer_manifest_rejected(self):
        p, b, d = fixtures()
        p["roles"]["reviewer"] = p["roles"]["meta"]
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p, b, d)

    def test_unbound_manifest_rejected(self):
        p, b, d = fixtures()
        p["phase"] = "UNBOUND_TEMPLATE"
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p, b, d)

    def test_foreign_repo_and_fork_pr(self):
        for side in ("head", "base"):
            for key, val in (("full_name", "foreign/repo"), ("fork", True)):
                with self.subTest(side=side, key=key):
                    self.rejected("/pulls/9", lambda x: x[side]["repo"].update({key: val}))

    def test_wrong_repo_metadata(self):
        self.rejected("", lambda x: x.update(full_name="foreign/repo"))

    def test_closed_merged_and_wrong_pr(self):
        for field, val in (("state", "closed"), ("merged", True), ("number", 10)):
            with self.subTest(field=field):
                self.rejected("/pulls/9", lambda x: x.update({field: val}))

    def test_old_head_or_base(self):
        for side in ("head", "base"):
            with self.subTest(side=side):
                self.rejected("/pulls/9", lambda x: x[side].update(sha="f" * 40))

    def test_wrong_branch_or_service_run(self):
        self.rejected("/pulls/9", lambda x: x["head"].update(ref="auto/system-" + RUN.replace("a", "b")))

    def test_missing_duplicate_and_extra_jobs(self):
        path = "/actions/runs/101/attempts/1/jobs?per_page=100"
        for change in (lambda x: x["jobs"].pop(), lambda x: x["jobs"].append(x["jobs"][0]),
                       lambda x: x["jobs"][1].update(name="offline"),
                       lambda x: x["jobs"][1].update(id=x["jobs"][0]["id"])):
            with self.subTest(change=change):
                self.rejected(path, change)

    def test_wrong_job_id_attempt_head(self):
        for field, val in (("run_id", 102), ("run_attempt", 2), ("head_sha", "f"*40), ("id", True)):
            with self.subTest(field=field):
                self.rejected("/actions/runs/101/attempts/1/jobs?per_page=100",
                              lambda x: x["jobs"][0].update({field: val}))

    def test_unknown_job_state_or_conclusion_is_rejected(self):
        for field,val in (('status','unknown'),('conclusion','provider_says_safe')):
            with self.subTest(field=field):
                self.rejected('/actions/runs/101/attempts/1/jobs?per_page=100',
                              lambda x:x['jobs'][0].update({field:val}))

    def test_mismatched_run_details(self):
        self.rejected("/actions/runs/101", lambda x: x.update(run_attempt=2))

    def test_wrong_workflow_or_old_run_or_attempt(self):
        path = "/actions/runs?head_sha="+HEAD+"&event=pull_request&per_page=100"
        for field, val in (("id", 102), ("run_attempt", 2), ("head_sha", "f"*40), ("workflow_id", 24)):
            with self.subTest(field=field):
                self.rejected(path, lambda x: x["workflow_runs"][0].update({field: val}))

    def test_self_consistent_foreign_run_and_weak_workflow_rejected(self):
        for field, val in (("workflow_id",24),("head_sha","f"*40),
                           ("event","workflow_dispatch"),("head_branch","foreign")):
            p,b,d=fixtures()
            path='/actions/runs?head_sha='+HEAD+'&event=pull_request&per_page=100'
            mutate(d,'/actions/runs/101',lambda x:x.update({field:val}))
            mutate(d,path,lambda x:x['workflow_runs'][0].update({field:val}))
            with self.subTest(field=field),self.assertRaises(target.EvidenceError):
                self.run_fixture(p,b,d)
        self.rejected('/git/trees/'+MTREE+'?recursive=1',lambda x:x['tree'][2].update(mode='120000'))

    def test_missing_duplicate_and_out_of_order_run_list(self):
        path='/actions/runs?head_sha='+HEAD+'&event=pull_request&per_page=100'
        for change in (lambda x:x.update(workflow_runs=[]),
                       lambda x:x['workflow_runs'].append(x['workflow_runs'][0]),
                       lambda x:x['workflow_runs'].append(dict(x['workflow_runs'][0],id=102,created_at=NOW))):
            with self.subTest(change=change):
                self.rejected(path,change)

    def test_branch_path_injection_and_bool_numeric_pins_rejected(self):
        for field,val in (('manifest_path','../config.json'),('workflow_file','../evil.yml'),
                          ('ci_run_id',True),('ci_attempt',False),('coordinator_epoch',True)):
            p,b,d=fixtures();b[field]=val
            with self.subTest(field=field),self.assertRaises(target.EvidenceError):
                self.run_fixture(p,b,d)

    def test_manifest_roles_must_match_provider_main(self):
        p,b,d=fixtures()
        p['roles']['meta']='7'*32
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p,b,d)

    def test_queued_ci_is_pending_not_success(self):
        p,b,d=fixtures()
        path='/actions/runs?head_sha='+HEAD+'&event=pull_request&per_page=100'
        mutate(d,'/actions/runs/101',lambda x:x.update(status='queued',conclusion=None))
        mutate(d,path,lambda x:x['workflow_runs'][0].update(status='queued',conclusion=None))
        result=self.run_fixture(p,b,d)
        self.assertEqual(result['pr']['ci']['qa'],'PENDING')
        self.assertFalse(any(result['authority'].values()))

    def test_failed_job_cannot_be_green(self):
        p,b,d=fixtures()
        mutate(d,'/actions/runs/101/attempts/1/jobs?per_page=100',lambda x:x['jobs'][0].update(conclusion='failure'))
        self.assertEqual(self.run_fixture(p,b,d)['pr']['ci']['qa'],'FAIL')

    def test_injected_credential_is_not_logged(self):
        p,b,d=fixtures()
        mutate(d,'/pulls/9',lambda x:x.update(body='token=NEVER_EMIT_ME'))
        result=self.run_fixture(p,b,d)
        self.assertNotIn('NEVER_EMIT_ME',json.dumps(result))

    def test_duplicate_json_keys_and_nonfinite_rejected(self):
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":Infinity}'):
            with self.subTest(raw=raw),self.assertRaises(target.EvidenceError):
                target.loads(raw)

    def test_pr_run_binding_is_exact(self):
        path = "/actions/runs?head_sha="+HEAD+"&event=pull_request&per_page=100"
        # Change list AND run detail so a superficial equality check cannot hide the defect.
        for field in ("number", "head", "base"):
            p, b, d = fixtures()
            def alter(x):
                row = x["pull_requests"][0]
                row[field] = 10 if field == "number" else {"sha": "f"*40}
            mutate(d, "/actions/runs/101", alter)
            mutate(d, path, lambda x: alter(x["workflow_runs"][0]))
            with self.subTest(field=field), self.assertRaises(target.EvidenceError):
                self.run_fixture(p, b, d)

    def test_moving_ref_pr_and_retry_rejected(self):
        p, b, d = fixtures()
        for path, change in (("/git/ref/heads/main", lambda x: x["object"].update(sha="f"*40)),
             ("/git/ref/heads/"+p["coordination_ref"], lambda x: x["object"].update(sha="f"*40)),
             ("/pulls/9", lambda x: x.update(state="closed")),
             ("/actions/runs/101", lambda x: x.update(run_attempt=2))):
            with self.subTest(path=path), self.assertRaises(target.EvidenceError):
                self.run_fixture(p, b, d, drift={path: change})

    def test_wrong_coordinator_epoch_and_blob(self):
        for field, val in (("coordinator_epoch", 8), ("coordinator_blob_sha", "f"*40)):
            p, b, d = fixtures()
            b[field] = val
            with self.subTest(field=field), self.assertRaises(target.EvidenceError):
                self.run_fixture(p, b, d)

    def coordinator_fixture(self, change):
        p,b,d=fixtures()
        path='/git/blobs/'+b['coordinator_blob_sha']
        state=json.loads(d[path].text)
        change(state)
        raw=json.dumps(state,sort_keys=True)
        digest=hashlib.sha1(b'blob '+str(len(raw.encode())).encode()+b'\0'+raw.encode()).hexdigest()
        d['/git/blobs/'+digest]=target.Response(200,raw)
        b['coordinator_blob_sha']=digest
        mutate(d,'/git/trees/'+CTREE+'?recursive=1',lambda x:x['tree'][0].update(sha=digest))
        return p,b,d

    def test_wrong_registered_role_in_immutable_state_is_rejected(self):
        p,b,d=self.coordinator_fixture(lambda x:x['authorized_tasks'].update(META='7'*32))
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p,b,d)

    def test_holder_wrong_task_and_epoch_are_rejected(self):
        holder={'kind':'META','owner_id':RUN,'task_id':'7'*32,'epoch':7,
                'acquired_at':'2026-10-27T10:00:00Z','expires_at':'2026-10-27T10:30:00Z'}
        p,b,d=self.coordinator_fixture(lambda x:x.update(holder=holder))
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p,b,d)
        holder.update(task_id=p['roles']['meta'],epoch=8)
        p,b,d=self.coordinator_fixture(lambda x:x.update(holder=holder))
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p,b,d)

    def test_expiry_never_removes_holder_or_authorizes_takeover(self):
        p,_,_=fixtures()
        holder={'kind':'META','owner_id':RUN,'task_id':p['roles']['meta'],'epoch':7,
                'acquired_at':'2026-10-27T10:00:00Z','expires_at':'2026-10-27T10:30:00Z'}
        p,b,d=self.coordinator_fixture(lambda x:x.update(holder=holder))
        result=self.run_fixture(p,b,d)
        self.assertEqual(result['coordinator']['holder'],holder)
        advice=target.advisory([p],result)
        self.assertIn('JOIN_EXISTING_LEASE',advice['scheduler']['candidates'][0]['issues'])
        self.assertFalse(advice['triage']['takeover_allowed'])
        self.assertFalse(advice['triage']['safe_to_next_schedule'])

    def test_created_commit_without_ref_claim_cannot_verify(self):
        p,b,d=fixtures()
        b['coordinator_sha']='f'*40
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p,b,d)

    def test_blob_tampering_and_duplicate_fields(self):
        for raw in ('{"epoch":7,"epoch":8}', '{"provider":true}', 'not json'):
            p, b, d = fixtures()
            d["/git/blobs/"+b["coordinator_blob_sha"]] = target.Response(200, raw)
            with self.subTest(raw=raw), self.assertRaises(target.EvidenceError):
                self.run_fixture(p, b, d)
        with self.assertRaises(target.EvidenceError):
            target.loads('{"provider":true,"provider":false}')

    def test_rest_base64_blob_also_checks_git_hash(self):
        import base64
        p, b, d = fixtures()
        for path, response in list(d.items()):
            if path.startswith("/git/blobs/"):
                d[path] = target.Response(200, json.dumps({"sha": path.rsplit("/",1)[1],
                    "encoding": "base64", "content": base64.b64encode(response.text.encode()).decode()}))
        self.assertEqual(self.run_fixture(p, b, d)["integrity"], "SCOPED_GETS_AND_BINDINGS_CHECKED")

    def test_symlink_and_truncated_tree_rejected(self):
        path = "/git/trees/"+CTREE+"?recursive=1"
        self.rejected(path, lambda x: x["tree"][0].update(mode="120000"))
        self.rejected(path, lambda x: x.update(truncated=True))
        self.rejected(path, lambda x: x["tree"].append(x["tree"][0]))

    def test_403_404_and_transport_error_fail_closed_without_secret(self):
        p, b, d = fixtures()
        for status in (403, 404, 429, 500):
            d[""] = target.Response(status, 'sensitive_token=DO_NOT_LOG')
            with self.subTest(status=status), self.assertRaisesRegex(target.EvidenceError, '^GET_REJECTED$'):
                self.run_fixture(p, b, d)
        def failing(url):
            raise RuntimeError('token=DO_NOT_LOG')
        with self.assertRaisesRegex(target.EvidenceError, '^GET_UNAVAILABLE$'):
            target.collect([p], b, failing, lambda: NOW)

    def test_unknown_transport_schema_rejected(self):
        p, b, _ = fixtures()
        with self.assertRaises(target.EvidenceError):
            target.collect([p], b, lambda _: {"provider": "github", "status": 200}, lambda: NOW)

    def test_out_of_order_future_run_and_jobs(self):
        self.rejected("/actions/runs?branch=main&event=push&per_page=100",
                      lambda x: x["workflow_runs"][0].update(updated_at="2026-10-28T00:00:00Z"))
        self.rejected("/actions/runs/101/attempts/1/jobs?per_page=100",
                      lambda x: x["jobs"][0].update(completed_at="2026-10-26T00:00:00Z"))

    def test_observation_clock_reversal_or_expiry_rejected(self):
        p, b, d = fixtures()
        for after in ("2026-10-27T11:49:59Z", "2026-10-27T11:52:01Z"):
            ticks = iter([NOW] + [after]*40)
            with self.subTest(after=after), self.assertRaises(target.EvidenceError):
                target.collect([p], b, FakeGET(p,d), lambda: next(ticks))

    def test_status_only_main_descendant_requires_direct_complete_compare(self):
        p, b, d = fixtures()
        old = "f"*40
        path = "/actions/runs?branch=main&event=push&per_page=100"
        mutate(d, path, lambda x: x["workflow_runs"][0].update(head_sha=old))
        mutate(d, "/actions/runs/100/attempts/1/jobs?per_page=100",
               lambda x: [j.update(head_sha=old) for j in x["jobs"]])
        cmp = {"status":"ahead", "behind_by":0,"base_commit":{"sha":old},
               "merge_base_commit":{"sha":old},"files":[{"filename":"status/LATEST_STATE.json","status":"modified"}]}
        cpath = "/compare/"+old+"..."+MAIN
        d[cpath] = target.Response(200,json.dumps(cmp))
        self.assertEqual(self.run_fixture(p,b,d)["status_only"],["status/LATEST_STATE.json"])
        for field, value in (("status","diverged"),("behind_by",1)):
            bad=deepcopy(d)
            mutate(bad,cpath,lambda x:x.update({field:value}))
            with self.subTest(field=field),self.assertRaises(target.EvidenceError):
                self.run_fixture(p,b,bad)
        mutate(d,cpath,lambda x:x["files"][0].update(filename="tools/unsafe.py"))
        with self.assertRaises(target.EvidenceError):
            self.run_fixture(p,b,d)

    def test_provider_permissions_never_grant_authority(self):
        p,b,d=fixtures()
        mutate(d,"",lambda x:x.update(permissions={"admin":True,"push":True},provider=True))
        result=self.run_fixture(p,b,d)
        self.assertFalse(any(result["authority"].values()))
        self.assertEqual(result["verification"],"NOT_VERIFIED")
        self.assertNotIn("permissions",json.dumps(result))

    def test_no_network_token_or_writer_dependency(self):
        # Architectural boundary, in addition to behavior tests on actual GETs.
        import ast
        tree=ast.parse((ROOT/"tools/system_github_evidence.py").read_text())
        imports={n.module for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)}
        imports|={a.name for n in ast.walk(tree) if isinstance(n,ast.Import) for a in n.names}
        self.assertTrue(imports.isdisjoint({"urllib","requests","httpx","os","subprocess"}))


if __name__ == "__main__":
    unittest.main()
