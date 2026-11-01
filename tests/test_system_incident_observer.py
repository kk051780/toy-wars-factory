"""Cross-provider incident observations; all fixtures are SYNTHETIC_TEST_ONLY."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tests")]
from tools import system_incident_observer as target
from test_system_github_evidence import fixtures as github_fixtures, FakeGET, mutate
from test_system_service_observer import record, IDS, PREVIOUS

NOW = "2026-10-27T12:30:00Z"


def fixtures(second=False):
    p, pins, d = github_fixtures(second)
    pins["author_role"] = "author"
    branch = "auto/game-" + pins["author_run_id"]
    mutate(d, "/pulls/9", lambda x: x["head"].update(ref=branch))
    for path in ("/actions/runs/101", "/actions/runs?head_sha=" + pins["pr_head_sha"] + "&event=pull_request&per_page=100"):
        def update(x):
            for run in x.get("workflow_runs", [x]):
                run["head_branch"] = branch
        mutate(d, path, update)
    services = {p["roles"][r]: record(p["roles"][r], r) for r in target.service.ROLES}
    return p, {"github": pins, "max_record_age_seconds": 172800, "max_window_seconds": 120}, d, services


def set_holder(p, b, d, holder):
    pins = b["github"]
    path = "/git/blobs/" + pins["coordinator_blob_sha"]
    state = json.loads(d[path].text)
    state["holder"] = holder
    raw = json.dumps(state, sort_keys=True)
    sha = hashlib.sha1(b"blob " + str(len(raw.encode())).encode() + b"\0" + raw.encode()).hexdigest()
    d["/git/blobs/" + sha] = target.github.Response(200, raw)
    pins["coordinator_blob_sha"] = sha
    mutate(d, "/git/trees/" + "e"*40 + "?recursive=1", lambda x: x["tree"][0].update(sha=sha))


class Provider:
    def __init__(self, p, d, s, on_get=None, on_peek=None):
        self.p, self.s = p, s
        self.raw = FakeGET(p, d)
        self.on_get, self.on_peek = on_get, on_peek
        self.peeks = []

    def get(self, url):
        if self.on_get:
            self.on_get(url, self)
        row = self.raw(url)
        return target.github.Response(row.status, row.text)

    def peek(self, task):
        self.peeks.append(task)
        row = deepcopy(self.s[task])
        if self.on_peek:
            self.on_peek(task, row, self)
        return target.service.PeekResponse(True, json.dumps({"automations": [row]}))


class IncidentObserverTests(unittest.TestCase):
    def execute(self, p, b, d, s, *, projects=None, on_get=None, on_peek=None, clock=None):
        provider = Provider(p, d, s, on_get, on_peek)
        return target.observe(projects or [p], b, provider.get, provider.peek, clock or (lambda: NOW)), provider

    def test_two_games_real_code_planners_and_no_authority(self):
        one, two = fixtures(), fixtures(True)
        original = deepcopy((one, two))
        for p, b, d, s in (one, two):
            r, provider = self.execute(p,b,d,s,projects=[one[0],two[0]])
            self.assertEqual(r["verification"], "NOT_VERIFIED")
            self.assertEqual(r["repository"],p["repository"])
            self.assertEqual(r["main_ci"]["qa"],"PASS")
            self.assertEqual(r["pr"]["ci"]["qa"],"PASS")
            self.assertEqual(provider.peeks,[p["roles"][r] for r in target.service.ROLES]*3)
            self.assertFalse(any(r["authority"].values()))
            self.assertFalse(any(r["advisory"]["authority"].values()))
            self.assertFalse(r["advisory"]["scheduler"]["execution"]["dispatch_allowed"])
            self.assertFalse(r["advisory"]["core"]["dispatch_allowed"])
            self.assertEqual(r["advisory"]["triage"]["state"],"INDETERMINATE")
            self.assertEqual(r["advisory"]["triage"]["reason"],"ORIGINAL_OPERATION_EVIDENCE_UNAVAILABLE")
            self.assertEqual(r["missing_triage_inputs"],["original_operation_receipt"])
        self.assertEqual((one,two),original)

    def test_real_supported_v2_called_with_collected_same_run_metadata(self):
        from unittest.mock import patch
        p,b,d,s=fixtures()
        original=target.triage.classify
        calls=[]
        def capture(e,c,n):
            calls.append((deepcopy(e),deepcopy(c)))
            return original(e,c,n)
        with patch.object(target.triage,"classify",side_effect=capture):
            self.execute(p,b,d,s)
        actual=[e for e,c in calls if e.get("schema")==1]
        self.assertEqual(len(actual),1)
        self.assertEqual(actual[0]["run_id"],IDS["author"])
        self.assertEqual(actual[0]["pr"]["data"]["producing_run_id"],IDS["author"])
        self.assertEqual(actual[0]["ci"]["data"]["attempt"],1)
        self.assertNotIn("operation",actual[0])

    def test_failed_and_no_update_remain_unsafe_and_actual_core_gets_status(self):
        for status in ("failed","no_update"):
            p,b,d,s=fixtures()
            s[p["roles"]["author"]]["run_details"]["last_run"]["recorded_status"]=status
            r,_=self.execute(p,b,d,s)
            self.assertEqual(r["advisory"]["triage"]["state"],"INDETERMINATE")
            self.assertFalse(r["advisory"]["triage"]["safe_to_next_schedule"])
            if status=="no_update":
                self.assertIn("WORKER_NO_UPDATE",r["advisory"]["core"]["alerts"])

    def test_previous_meta_report_does_not_complete_active_meta(self):
        p,b,d,s=fixtures();r,_=self.execute(p,b,d,s)
        row=r["services"]["meta"]
        self.assertEqual(row["last_run"]["recorded_status"],"in_progress")
        self.assertIsNone(row["last_run"]["completed_at"])
        self.assertEqual(row["latest_result_metadata"]["run_id"],PREVIOUS)
        self.assertFalse(any(r["authority"].values()))

    def test_historical_pr_qa_does_not_bind_to_later_worker_service(self):
        p,b,d,s=fixtures();row=s[p["roles"]["author"]]["run_details"]
        later="eeeeeeee-ffff-4aaa-8bbb-cccccccccccc"
        row["last_run"]["id"]=later;row["latest_result"]["run_id"]=later
        r,_=self.execute(p,b,d,s)
        self.assertEqual(r["pr_author_service_binding"],"HISTORICAL_PR_AUTHOR_NOT_CURRENT_SERVICE")
        self.assertEqual(r["advisory"]["triage"]["state"],"INDETERMINATE")

    def test_pr_author_cannot_reuse_other_roles_current_run(self):
        p,b,d,s=fixtures();s[p["roles"]["reviewer"]]["run_details"]["last_run"]["id"]=IDS["author"]
        s[p["roles"]["reviewer"]]["run_details"]["latest_result"]["run_id"]=IDS["author"]
        with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)

    def test_service_changes_only_during_github_phase_rejected(self):
        p,b,d,s=fixtures()
        def during(url, provider):
            if url.endswith("/pulls/9"):
                s[p["roles"]["author"]]["run_details"]["last_run"]["recorded_status"]="failed"
        with self.assertRaisesRegex(target.EvidenceError,"CROSS_CHANNEL_SERVICE_DRIFT"):
            self.execute(p,b,d,s,on_get=during)

    def test_job_only_changes_after_github_phase_rejected(self):
        p,b,d,s=fixtures()
        def during(task,row,provider):
            if len(provider.peeks)>6:
                mutate(d,"/actions/runs/101/attempts/1/jobs?per_page=100",lambda x:x["jobs"][0].update(conclusion="failure"))
        with self.assertRaisesRegex(target.EvidenceError,"CROSS_CHANNEL_GITHUB_DRIFT"):
            self.execute(p,b,d,s,on_peek=during)

    def test_main_job_only_changes_rejected(self):
        p,b,d,s=fixtures()
        def during(task,row,provider):
            if len(provider.peeks)>6:
                mutate(d,"/actions/runs/100/attempts/1/jobs?per_page=100",lambda x:x["jobs"][0].update(id=99999))
        with self.assertRaisesRegex(target.EvidenceError,"CROSS_CHANNEL_GITHUB_DRIFT"):
            self.execute(p,b,d,s,on_peek=during)

    def test_pr_closure_or_head_change_between_channels_rejected(self):
        for field,value in (("state","closed"),("merged",True)):
            p,b,d,s=fixtures()
            def during(task,row,provider):
                if len(provider.peeks)>6:mutate(d,"/pulls/9",lambda x:x.update({field:value}))
            with self.subTest(field=field),self.assertRaises(target.EvidenceError):self.execute(p,b,d,s,on_peek=during)

    def test_end_coordinator_ref_movement_rejected(self):
        p,b,d,s=fixtures()
        def during(task,row,provider):
            if len(provider.peeks)>6:
                mutate(d,"/git/ref/heads/"+p["coordination_ref"],lambda x:x["object"].update(sha="f"*40))
        with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s,on_peek=during)

    def test_wrong_epoch_and_blob_rejected(self):
        for field,value in (("coordinator_epoch",8),("coordinator_blob_sha","f"*40)):
            p,b,d,s=fixtures();b["github"][field]=value
            with self.subTest(field=field),self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)

    def test_fork_foreign_repo_stale_head_and_ci_attempt_rejected(self):
        changes=[("/pulls/9",lambda x:x["head"]["repo"].update(fork=True)),
                 ("/pulls/9",lambda x:x["base"]["repo"].update(full_name="other/game")),
                 ("/pulls/9",lambda x:x["head"].update(sha="f"*40)),
                 ("/actions/runs/101/attempts/1/jobs?per_page=100",lambda x:x["jobs"][0].update(run_attempt=2)),
                 ("/actions/runs/101/attempts/1/jobs?per_page=100",lambda x:x["jobs"][0].update(head_sha="f"*40))]
        for path,change in changes:
            p,b,d,s=fixtures();mutate(d,path,change)
            with self.subTest(path=path),self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)

    def test_missing_and_duplicate_jobs_rejected(self):
        for change in (lambda x:x.update(jobs=x["jobs"][:1]),lambda x:x["jobs"].__setitem__(1,deepcopy(x["jobs"][0]))):
            p,b,d,s=fixtures();mutate(d,"/actions/runs/101/attempts/1/jobs?per_page=100",change)
            with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)

    def test_closed_pr_rejected_without_other_pr_edit(self):
        p,b,d,s=fixtures();mutate(d,"/pulls/9",lambda x:x.update(state="closed"))
        with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)

    def test_cross_game_task_reuse_and_foreign_snapshot_rejected(self):
        p,b,d,s=fixtures();q,_,e,_=fixtures(True)
        q["roles"]["meta"]=p["roles"]["meta"]
        with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s,projects=[p,q])
        with self.assertRaises(target.EvidenceError):self.execute(p,b,e,s)

    def test_api_403_404_and_unknown_exception_fail_closed(self):
        for status in (403,404):
            p,b,d,s=fixtures();d[""]=target.github.Response(status,"token=SECRET")
            with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)
        p,b,d,s=fixtures()
        def failed(*args):raise RuntimeError("token=NEVER_EMIT")
        with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s,on_get=failed)

    def test_duplicate_json_fields_provider_labels_and_fake_grants_rejected(self):
        p,b,d,s=fixtures();d[""]=target.github.Response(200,'{"full_name":"'+p["repository"]+'","fork":false,"fork":false}')
        with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)
        for extra in ({"provider":True},{"write_allowed":True},{"operation":{"outcome":"success"}}):
            p,b,d,s=fixtures();b.update(extra)
            with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)

    def test_unknown_service_status_and_missing_result_never_healthy(self):
        p,b,d,s=fixtures();s[p["roles"]["author"]]["run_details"]["last_run"]["recorded_status"]="healthy"
        with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)
        p,b,d,s=fixtures();s[p["roles"]["author"]]["run_details"]["latest_result"]=None
        r,_=self.execute(p,b,d,s)
        self.assertFalse(any(r["authority"].values()))
        self.assertEqual(r["advisory"]["triage"]["state"],"INDETERMINATE")

    def test_active_holder_kept_without_claim_or_takeover(self):
        p,b,d,s=fixtures()
        holder={"kind":"META","owner_id":IDS["meta"],"task_id":p["roles"]["meta"],"epoch":7,
                "acquired_at":"2026-10-27T12:10:00Z","expires_at":"2026-10-27T12:40:00Z","work_branch":"auto/system-"+IDS["meta"]}
        set_holder(p,b,d,holder);r,_=self.execute(p,b,d,s)
        self.assertEqual(r["advisory"]["triage"]["state"],"ACTIVE_LEASE")
        self.assertFalse(r["advisory"]["triage"]["claim_verified"])
        self.assertFalse(any(r["authority"].values()))

    def test_expired_unknown_owner_is_not_recovered(self):
        p,b,d,s=fixtures()
        holder={"kind":"META","owner_id":"ffffffff-aaaa-4bbb-8ccc-dddddddddddd","task_id":p["roles"]["meta"],"epoch":7,
                "acquired_at":"2026-10-27T11:50:00Z","expires_at":"2026-10-27T12:20:00Z","work_branch":"auto/system-old"}
        set_holder(p,b,d,holder);r,_=self.execute(p,b,d,s)
        self.assertIsNotNone(r["coordinator"]["holder"])
        self.assertEqual(r["advisory"]["triage"]["state"],"INDETERMINATE")
        self.assertFalse(r["authority"]["takeover_allowed"])

    def test_secret_prose_holder_fields_and_permission_labels_never_echoed(self):
        p,b,d,s=fixtures()
        for row in s.values():row["run_details"]["latest_result"]["content_text"]="HOST_WRITE_DENIED token=NEVER_ECHO_THIS"
        r,_=self.execute(p,b,d,s)
        raw=json.dumps(r)
        self.assertNotIn("NEVER_ECHO",raw);self.assertNotIn("NEVER_EMIT",raw)
        self.assertNotIn("HOST_WRITE_DENIED",raw)
        self.assertEqual(r["operation_evidence"]["status"],"OPERATION_EVIDENCE_UNAVAILABLE")

    def test_unrecognized_holder_fields_are_dropped(self):
        p,b,d,s=fixtures()
        h={"kind":"META","owner_id":IDS["meta"],"task_id":p["roles"]["meta"],"epoch":7,
           "acquired_at":"2026-10-27T12:10:00Z","expires_at":"2026-10-27T12:40:00Z",
           "work_branch":"auto/system-"+IDS["meta"],"token":"NEVER_ECHO_HOLDER"}
        set_holder(p,b,d,h);r,_=self.execute(p,b,d,s)
        self.assertNotIn("NEVER_ECHO_HOLDER",json.dumps(r))
        self.assertNotIn("token",r["coordinator"]["holder"])

    def test_self_reported_permissions_and_denial_do_not_prove_operation(self):
        p,b,d,s=fixtures()
        mutate(d,"",lambda x:x.update(permissions={"admin":True,"push":True},provider=True))
        s[p["roles"]["author"]]["run_details"]["latest_result"]["content_text"]="HOST_WRITE_DENIED"
        r,_=self.execute(p,b,d,s)
        self.assertFalse(any(r["authority"].values()))
        self.assertEqual(r["operation_evidence"]["verification"],"NOT_VERIFIED")
        self.assertNotEqual(r["advisory"]["triage"]["state"],"HOST_WRITE_DENIED")

    def test_accepted_collectors_can_miss_job_change_between_channels(self):
        # Actual old GET collector finishes before the independent service read.
        # This reproduces the gap; no copied callback or simulated verdict.
        p,b,d,s=fixtures();provider=Provider(p,d,s)
        old=target.github.collect([p],b["github"],provider.get,lambda:NOW)
        mutate(d,"/actions/runs/101/attempts/1/jobs?per_page=100",lambda x:x["jobs"][0].update(conclusion="failure"))
        sb={k:b["github"][k] for k in target.service.FIELDS if k!="max_record_age_seconds"}
        sb["max_record_age_seconds"]=172800
        services=target.service.observe([p],sb,provider.get,provider.peek,lambda:NOW)
        self.assertEqual(old["pr"]["ci"]["qa"],"PASS")
        self.assertEqual(services["services"]["author"]["last_run"]["recorded_status"],"completed")
        self.assertEqual(json.loads(d["/actions/runs/101/attempts/1/jobs?per_page=100"].text)["jobs"][0]["conclusion"],"failure")

    def test_cli_provider_error_payload_cannot_leak(self):
        p,b,d,s=fixtures()
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"request.json";path.write_text(json.dumps({"projects":[p],"binding":b}))
            result=subprocess.run([sys.executable,"tools/system_incident_observer.py","--request",str(path)],cwd=ROOT,
                 input=json.dumps({"status":403,"body":"token=NEVER_ECHO_PROVIDER"})+"\n",text=True,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,2)
            self.assertNotIn("NEVER_ECHO",result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout.splitlines()[-1])["reason"],"INCIDENT_OBSERVATION_REJECTED")

    def test_package_import_without_loader_helpers(self):
        result=subprocess.run([sys.executable,"-c","from tools import system_incident_observer; assert not any(system_incident_observer.DENIED.values())"],
                              cwd=ROOT,text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_single_total_window_and_backward_clock_rejected(self):
        for step in (1,-1):
            p,b,d,s=fixtures();at=datetime(2026,10,27,12,30,tzinfo=timezone.utc);count=0
            def clock():
                nonlocal count
                count+=1
                return (at+timedelta(seconds=count*step)).isoformat()
            with self.subTest(step=step),self.assertRaises(target.EvidenceError):self.execute(p,b,d,s,clock=clock)

    def test_unbounded_or_malformed_window_rejected(self):
        for value in (0,121,True,"120",None):
            p,b,d,s=fixtures();b["max_window_seconds"]=value
            with self.subTest(value=value),self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)

    def test_only_immutable_git_objects_cached_within_one_observation(self):
        p,b,d,s=fixtures();r,provider=self.execute(p,b,d,s)
        paths=[u[len(provider.raw.prefix):] for u in provider.raw.calls]
        objects=[u for u in paths if u.startswith(("/git/blobs/","/git/trees/","/git/commits/"))]
        self.assertEqual(len(objects),len(set(objects)))
        self.assertGreater(len(r["immutable_cache_hits"]),0)
        for key in ("/pulls/9","/actions/runs/101/attempts/1/jobs?per_page=100",
                    "/actions/runs/100/attempts/1/jobs?per_page=100","/git/ref/heads/main"):
            self.assertGreaterEqual(paths.count(key),2)
        # A new call obtains the objects again; this is no persistent receipt.
        r2,again=self.execute(p,b,d,s)
        self.assertEqual(len(again.raw.calls),len(provider.raw.calls))

    def test_corrupted_immutable_blob_never_becomes_cached_evidence(self):
        p,b,d,s=fixtures();path="/git/blobs/"+b["github"]["coordinator_blob_sha"]
        d[path]=target.github.Response(200,d[path].text+" ")
        with self.assertRaises(target.EvidenceError):self.execute(p,b,d,s)

    def test_cli_bad_request_and_secret_response_only_fixed_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"input.json"
            path.write_text('{"token":"NEVER_ECHO_CLI"}')
            result=subprocess.run([sys.executable,"tools/system_incident_observer.py","--request",str(path)],cwd=ROOT,text=True,capture_output=True,timeout=10)
            self.assertEqual(result.returncode,2)
            self.assertNotIn("NEVER_ECHO",result.stdout+result.stderr)
            self.assertEqual(json.loads(result.stdout)["reason"],"INCIDENT_OBSERVATION_REJECTED")


if __name__=="__main__":unittest.main()
