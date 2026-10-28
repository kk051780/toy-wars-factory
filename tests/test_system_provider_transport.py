"""Synthetic contract tests for real transport + accepted collectors, not auth."""
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
from tools import system_provider_transport as target
from test_system_incident_observer import fixtures, Provider, set_holder, NOW
from test_system_github_evidence import mutate
from test_system_service_observer import IDS


def service_pins(binding):
    b = {k: binding["github"][k] for k in target.service.FIELDS if k != "max_record_age_seconds"}
    b["max_record_age_seconds"] = binding["max_record_age_seconds"]
    return b


def replace_document(data, pins, tree_sha, name, change):
    tree_path = "/git/trees/" + tree_sha + "?recursive=1"
    tree = json.loads(data[tree_path].text)
    entry = next(e for e in tree["tree"] if e["path"] == name)
    obj = json.loads(data["/git/blobs/" + entry["sha"]].text)
    change(obj)
    raw = json.dumps(obj, sort_keys=True)
    sha = hashlib.sha1(b"blob " + str(len(raw.encode())).encode() + b"\0" + raw.encode()).hexdigest()
    entry["sha"] = sha
    data[tree_path] = target.github.Response(200, json.dumps(tree))
    data["/git/blobs/" + sha] = target.github.Response(200, raw)
    if name == "ops/REPAIR_COORDINATOR.json":pins["github"]["coordinator_blob_sha"] = sha


class TransportTests(unittest.TestCase):
    def make(self, second=False, *, collector="service"):
        p,b,d,s = fixtures(second)
        provider = Provider(p,d,s)
        transport = target.ReadOnlyTransport([p],b,provider.get,provider.peek,lambda:NOW)
        return p,b,d,s,provider,transport

    def bind(self, p,b,transport):
        return target.service.project_binding([p],service_pins(b),transport.get,transport.clock)

    def test_two_games_actual_incident_core_scheduler_v2_and_no_grants(self):
        one,two = fixtures(),fixtures(True)
        original = deepcopy((one,two))
        for p,b,d,s in (one,two):
            provider=Provider(p,d,s)
            out=target.observe([one[0],two[0]],b,provider.get,provider.peek,lambda:NOW)
            self.assertEqual(out["verification"],"NOT_VERIFIED")
            self.assertEqual(out["observation"]["repository"],p["repository"])
            self.assertEqual(out["observation"]["pr"]["ci"]["qa"],"PASS")
            self.assertEqual(out["observation"]["advisory"]["triage"]["state"],"INDETERMINATE")
            self.assertFalse(out["observation"]["advisory"]["core"]["dispatch_allowed"])
            self.assertFalse(out["observation"]["advisory"]["scheduler"]["execution"]["dispatch_allowed"])
            self.assertFalse(any(out["authority"].values()))
            self.assertFalse(any(out["transport"]["authority"].values()))
            self.assertTrue(out["transport"]["roles_bound_to_pinned_blobs"])
            self.assertEqual(out["transport"]["calls"],len(provider.raw.calls)+len(provider.peeks))
        self.assertEqual((one,two),original)

    def test_existing_bridge_exposes_service_prose_before_new_projection(self):
        # Execute accepted snapshot boundary. It drops prose in its OUTPUT,
        # but its input callback still receives the full raw provider text.
        p,b,d,s,provider,t=self.make()
        raw=provider.peek(p["roles"]["author"]).text
        self.assertIn("NEVER_EMIT_PROMPT_SECRET",raw)
        self.assertIn("NEVER_EMIT_REPORT_SECRET",raw)
        accepted=target.service.snapshot(raw,p["roles"]["author"],target.github.moment(NOW),172800)
        self.assertNotIn("NEVER_EMIT",json.dumps(accepted))
        self.bind(p,b,t)
        forwarded=t.peek(p["roles"]["author"]).text
        self.assertNotIn("NEVER_EMIT",forwarded)
        self.assertEqual(target.service.snapshot(forwarded,p["roles"]["author"],target.github.moment(NOW),172800),accepted)

    def test_projection_happens_before_accepted_collector_and_preserves_result(self):
        p,b,d,s,provider,t=self.make()
        baseline=target.service.observe([p],service_pins(b),provider.get,provider.peek,lambda:NOW)
        forwarded=[]
        def checked(task):
            response=t.peek(task);forwarded.append(response.text)
            self.assertNotIn("NEVER_EMIT",response.text)
            row=json.loads(response.text)["automations"][0]
            self.assertEqual(set(row),{"id","is_enabled","run_details"})
            self.assertEqual(set(row["run_details"]),{"last_run","latest_result"})
            return response
        actual=target.service.observe([p],service_pins(b),t.get,checked,t.clock)
        self.assertEqual(actual,baseline)
        self.assertEqual(len(forwarded),6)

    def test_arbitrary_service_fields_and_chat_refs_not_forwarded(self):
        p,b,d,s,provider,t=self.make()
        for row in s.values():
            row.update(api_key="NEVER_PASS_KEY",title="NEVER_PASS_TITLE",schedule="NEVER_PASS_SCHEDULE")
            row["run_details"]["last_run"]["chat_ref"]={"id":"NEVER_PASS_CHAT"}
            row["run_details"]["latest_result"]["headers"]={"Authorization":"NEVER_PASS_AUTH"}
        self.bind(p,b,t)
        for task in p["roles"].values():
            raw=t.peek(task).text
            self.assertNotIn("NEVER_PASS",raw)
            self.assertNotIn("content_text",raw)
            self.assertNotIn("prompt",raw)
        self.assertNotIn("NEVER_PASS",json.dumps(t.audit()))

    def test_previous_result_lifecycle_and_failure_flags_preserved(self):
        p,b,d,s,provider,t=self.make();self.bind(p,b,t)
        raw=t.peek(p["roles"]["meta"]).text
        row=target.service.snapshot(raw,p["roles"]["meta"],target.github.moment(NOW),172800)
        self.assertEqual(row["latest_result_binding"],"PREVIOUS_RUN")
        self.assertEqual(row["observation_state"],"IN_PROGRESS")
        for flag in ("is_failure_message","requires_user_action"):
            s[p["roles"]["author"]]["run_details"]["latest_result"][flag]=True
            row=target.service.snapshot(t.peek(p["roles"]["author"]).text,p["roles"]["author"],target.github.moment(NOW),172800)
            self.assertEqual(row["observation_state"],"CURRENT_RESULT_REQUIRES_ATTENTION")

    def test_failed_no_update_disabled_not_promoted_by_filter(self):
        for status in ("failed","no_update"):
            p,b,d,s=fixtures();s[p["roles"]["author"]]["run_details"]["last_run"]["recorded_status"]=status
            provider=Provider(p,d,s);out=target.observe([p],b,provider.get,provider.peek,lambda:NOW)
            self.assertEqual(out["observation"]["services"]["author"]["observation_state"],status.upper())
            self.assertEqual(out["observation"]["advisory"]["triage"]["state"],"INDETERMINATE")
            self.assertFalse(any(out["authority"].values()))
        p,b,d,s=fixtures();s[p["roles"]["author"]]["is_enabled"]=False;provider=Provider(p,d,s)
        out=target.observe([p],b,provider.get,provider.peek,lambda:NOW,collector="service")
        self.assertEqual(out["observation"]["services"]["author"]["observation_state"],"SERVICE_DISABLED")

    def test_peek_before_pinned_main_and_coordinator_binding_never_called(self):
        p,b,d,s,provider,t=self.make()
        with self.assertRaises(target.EvidenceError):t.peek(p["roles"]["author"])
        self.assertEqual(provider.peeks,[])
        self.assertTrue(t.closed)

    def test_missing_ref_relationship_does_not_enable_peek(self):
        p,b,d,s,provider,t=self.make()
        for commit,tree in (("a"*40,"d"*40),("b"*40,"e"*40)):
            t.get(provider.raw.prefix+"/git/commits/"+commit)
            t.get(provider.raw.prefix+"/git/trees/"+tree+"?recursive=1")
        for path in list(t._rules):
            if path.startswith("/git/blobs/"):t.get(provider.raw.prefix+path)
        self.assertFalse(t.roles_bound)
        with self.assertRaises(target.EvidenceError):t.peek(p["roles"]["author"])
        self.assertEqual(provider.peeks,[])

    def test_foreign_or_unregistered_task_refused_before_provider(self):
        for task in ("f"*32,"6add445e4138819197d9cf2b1a02534d",None,True):
            p,b,d,s,provider,t=self.make();self.bind(p,b,t)
            with self.subTest(task=task),self.assertRaises(target.EvidenceError):t.peek(task)
            self.assertEqual(provider.peeks,[])

    def test_cross_game_task_reuse_rejected_before_any_call(self):
        p,b,d,s=fixtures();q,_,_,_=fixtures(True);q["roles"]["reviewer"]=p["roles"]["meta"]
        provider=Provider(p,d,s)
        with self.assertRaises(Exception):target.ReadOnlyTransport([p,q],b,provider.get,provider.peek,lambda:NOW)
        self.assertEqual(provider.raw.calls,[]);self.assertEqual(provider.peeks,[])

    def test_malformed_pins_and_extra_permissions_rejected_before_call(self):
        for change in (lambda b:b.update(provider=True),lambda b:b["github"].update(ci_attempt=True),
                       lambda b:b["github"].update(manifest_path="../credentials"),lambda b:b.update(max_window_seconds=121)):
            p,b,d,s=fixtures();change(b);provider=Provider(p,d,s)
            with self.assertRaises(target.EvidenceError):target.ReadOnlyTransport([p],b,provider.get,provider.peek,lambda:NOW)
            self.assertEqual(provider.raw.calls,[])

    def test_foreign_repo_userinfo_redirect_encoding_and_write_urls_refused(self):
        suffixes=["-other","/../secrets","/%2e%2e/secrets","/contents/.env","/actions/workflows/qa.yml/dispatches",
                  "/git/ref/heads/main?force=true","/pulls/10","/pulls/9?method=DELETE","/actions/runs/999"]
        for suffix in suffixes:
            p,b,d,s,provider,t=self.make()
            with self.subTest(suffix=suffix),self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix+suffix)
            self.assertEqual(provider.raw.calls,[])
        for url in ("https://api.github.com.evil/repos/example/clockwork","https://evil@api.github.com/repos/example/clockwork",None):
            p,b,d,s,provider,t=self.make()
            with self.assertRaises(target.EvidenceError):t.get(url)
            self.assertEqual(provider.raw.calls,[])

    def test_unknown_object_and_unlearned_tree_refused(self):
        for path in ("/git/blobs/"+"f"*40,"/git/commits/"+"f"*40,"/git/trees/"+"d"*40+"?recursive=1"):
            p,b,d,s,provider,t=self.make()
            with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix+path)
            self.assertEqual(provider.raw.calls,[])

    def test_unrelated_blob_in_legitimate_tree_does_not_expand_scope(self):
        p,b,d,s,provider,t=self.make()
        mutate(d,"/git/trees/"+"d"*40+"?recursive=1",lambda x:x["tree"].append({"path":"private/credentials.json","mode":"100644","type":"blob","sha":"f"*40}))
        self.bind(p,b,t);count=len(provider.raw.calls)
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix+"/git/blobs/"+"f"*40)
        self.assertEqual(len(provider.raw.calls),count)

    def test_wrong_or_moving_ref_closes_transport(self):
        p,b,d,s,provider,t=self.make()
        mutate(d,"/git/ref/heads/main",lambda x:x["object"].update(sha="f"*40))
        with self.assertRaises(target.EvidenceError):self.bind(p,b,t)
        self.assertTrue(t.closed);self.assertFalse(t.roles_bound)

    def test_symlink_duplicate_path_and_wrong_blob_fail_closed(self):
        cases=[("/git/trees/"+"d"*40+"?recursive=1",lambda x:x["tree"][0].update(mode="120000")),
               ("/git/trees/"+"e"*40+"?recursive=1",lambda x:x["tree"].append(deepcopy(x["tree"][0])))]
        for path,change in cases:
            p,b,d,s,provider,t=self.make();mutate(d,path,change)
            with self.assertRaises(target.EvidenceError):self.bind(p,b,t)
            self.assertEqual(provider.peeks,[])
        p,b,d,s,provider,t=self.make();key="/git/blobs/"+b["github"]["coordinator_blob_sha"]
        d[key]=target.github.Response(200,d[key].text+" ")
        with self.assertRaises(target.EvidenceError):self.bind(p,b,t)

    def test_policy_or_state_wrong_task_cannot_bind_even_with_matching_hash(self):
        for name,tree,change in (("config/autonomous_repair.json","d"*40,lambda x:x["system_review"].update(task_id="f"*32)),
                                 ("ops/REPAIR_COORDINATOR.json","e"*40,lambda x:x.update(epoch=8))):
            p,b,d,s,provider,t=self.make();replace_document(d,b,tree,name,change)
            t=target.ReadOnlyTransport([p],b,provider.get,provider.peek,lambda:NOW)
            with self.assertRaises(target.EvidenceError):self.bind(p,b,t)
            self.assertEqual(provider.peeks,[])

    def test_http_errors_and_unknown_exception_never_become_host_denial(self):
        for status in (403,404,500):
            p,b,d,s,provider,t=self.make();d[""]=target.github.Response(status,"Authorization: NEVER_LOG")
            with self.assertRaisesRegex(target.EvidenceError,"^READONLY_TRANSPORT_REJECTED$"):t.get(provider.raw.prefix)
            self.assertNotIn("NEVER_LOG",json.dumps(t.audit()))
            self.assertFalse(any(t.audit()["authority"].values()))
        p,b,d,s,provider,t=self.make()
        def secret_error(url):raise target.EvidenceError("token=NEVER_LOG_EXCEPTION")
        t._get=secret_error
        with self.assertRaisesRegex(target.EvidenceError,"^READONLY_TRANSPORT_REJECTED$"):t.get(provider.raw.prefix)

    def test_duplicate_json_fields_rejected_and_no_retry(self):
        p,b,d,s,provider,t=self.make();d[""]=target.github.Response(200,'{"fork":false,"fork":false}')
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix)
        self.assertEqual(len(provider.raw.calls),1)
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix)
        self.assertEqual(len(provider.raw.calls),1)

    def test_main_qa_resource_graph_accepts_only_observed_exact_run_attempt(self):
        p,b,d,s,provider,t=self.make()
        t.get(provider.raw.prefix+"/actions/runs?branch=main&event=push&per_page=100")
        t.get(provider.raw.prefix+"/actions/runs/100/attempts/1/jobs?per_page=100")
        count=len(provider.raw.calls)
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix+"/actions/runs/100/attempts/2/jobs?per_page=100")
        self.assertEqual(len(provider.raw.calls),count)

    def test_foreign_main_run_cannot_expand_job_scope(self):
        p,b,d,s,provider,t=self.make()
        mutate(d,"/actions/runs?branch=main&event=push&per_page=100",lambda x:x["workflow_runs"][0]["head_repository"].update(fork=True))
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix+"/actions/runs?branch=main&event=push&per_page=100")
        self.assertNotIn("/actions/runs/100/attempts/1/jobs?per_page=100",t._rules)

    def test_existing_adversarial_job_validation_not_weakened(self):
        for change in (lambda x:x["jobs"][0].update(run_attempt=2),lambda x:x.update(jobs=x["jobs"][:1])):
            p,b,d,s=fixtures();mutate(d,"/actions/runs/101/attempts/1/jobs?per_page=100",change);provider=Provider(p,d,s)
            with self.assertRaises(target.EvidenceError):target.observe([p],b,provider.get,provider.peek,lambda:NOW)

    def test_job_drift_during_service_phase_still_rejected(self):
        p,b,d,s=fixtures()
        def during(task,row,provider):
            if len(provider.peeks)>6:mutate(d,"/actions/runs/101/attempts/1/jobs?per_page=100",lambda x:x["jobs"][0].update(conclusion="failure"))
        provider=Provider(p,d,s,on_peek=during)
        with self.assertRaises(target.EvidenceError):target.observe([p],b,provider.get,provider.peek,lambda:NOW)

    def test_callback_urls_and_permission_claims_add_no_capability(self):
        p,b,d,s,provider,t=self.make();mutate(d,"",lambda x:x.update(url="https://evil.invalid",permissions={"admin":True},provider=True))
        t.get(provider.raw.prefix)
        self.assertFalse(any(t.audit()["authority"].values()))
        with self.assertRaises(target.EvidenceError):t.get("https://evil.invalid")
        self.assertEqual(provider.raw.calls,[provider.raw.prefix])

    def test_call_byte_and_time_limits_fail_closed(self):
        p,b,d,s,provider,t=self.make()
        for _ in range(64):t.get(provider.raw.prefix)
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix)
        self.assertEqual(len(provider.raw.calls),64)
        p,b,d,s,provider,t=self.make();d[""]=target.github.Response(200,"x"*2_000_001)
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix)
        self.assertTrue(t.closed)
        p,b,d,s,provider,t=self.make();t._clock=lambda:"2026-10-27T12:32:01Z"
        with self.assertRaises(target.EvidenceError):t.clock()
        t._clock=lambda:NOW
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix)
        self.assertEqual(provider.raw.calls,[])

    def test_total_response_budget_and_backward_clock_close_session(self):
        p,b,d,s,provider,t=self.make()
        mutate(d,"",lambda x:x.update(unused="x"*1_900_000))
        with self.assertRaises(target.EvidenceError):
            for _ in range(10):t.get(provider.raw.prefix)
        self.assertTrue(t.closed)
        self.assertLessEqual(t.raw_bytes,16_000_000)
        p,b,d,s,provider,t=self.make();t._clock=lambda:"2026-10-27T12:29:59Z"
        with self.assertRaises(target.EvidenceError):t.get(provider.raw.prefix)
        self.assertEqual(provider.raw.calls,[])

    def test_error_or_ambiguous_peek_envelope_never_forwarded(self):
        for mutate_envelope in (lambda e:e.update(isError=True),lambda e:e.update(status="ERROR"),
                                lambda e:e.update(error_code="UNKNOWN_ERROR"),
                                lambda e:e.update(structuredContent={"automations":e["automations"]})):
            p,b,d,s,provider,t=self.make();self.bind(p,b,t)
            original=provider.peek
            def error(task):
                row=json.loads(original(task).text);mutate_envelope(row)
                return target.service.PeekResponse(True,json.dumps(row))
            t._peek=error
            with self.assertRaises(target.EvidenceError):t.peek(p["roles"]["author"])
            self.assertTrue(t.closed)

    def test_invalid_forged_stale_service_metadata_rejected_before_forward(self):
        for change in (lambda row:row.update(id="f"*32),
                       lambda row:row["run_details"]["last_run"].update(started_at="2026-10-20T00:00:00Z"),
                       lambda row:row["run_details"]["latest_result"].update(is_failure_message="false")):
            p,b,d,s,provider,t=self.make();self.bind(p,b,t);change(s[p["roles"]["author"]])
            with self.assertRaises(target.EvidenceError):t.peek(p["roles"]["author"])

    def test_unknown_fields_and_self_authentication_never_upgrade_origin(self):
        p,b,d,s=fixtures();provider=Provider(p,d,s)
        for row in s.values():row.update(provider=True,verification="LIVE_PROVIDER_VERIFIED",write_allowed=True)
        out=target.observe([p],b,provider.get,provider.peek,lambda:NOW,collector="service")
        self.assertEqual(out["verification"],"NOT_VERIFIED")
        self.assertEqual(out["transport"]["verification"],"NOT_VERIFIED")
        self.assertNotIn("LIVE_PROVIDER_VERIFIED",json.dumps(out))
        self.assertFalse(any(out["authority"].values()))

    def test_unknown_collector_and_cli_prose_never_forwarded(self):
        p,b,d,s,provider,t=self.make()
        with self.assertRaises(target.EvidenceError):target.observe([p],b,provider.get,provider.peek,lambda:NOW,collector="write")
        self.assertEqual(provider.raw.calls,[])
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/"request.json";path.write_text(json.dumps({"projects":[p],"binding":b,"collector":"service"}))
            r=subprocess.run([sys.executable,"tools/system_provider_transport.py","--request",str(path)],cwd=ROOT,
                input=json.dumps({"status":403,"body":"token=NEVER_LOG_CLI"})+"\n",text=True,capture_output=True,timeout=10)
            self.assertEqual(r.returncode,2);self.assertNotIn("NEVER_LOG",r.stdout+r.stderr)
            self.assertEqual(json.loads(r.stdout.splitlines()[-1])["reason"],"READONLY_TRANSPORT_REJECTED")

    def test_package_import_is_stdlib_only_and_adds_no_execution(self):
        r=subprocess.run([sys.executable,"-c","from tools import system_provider_transport as t; assert not any(t.DENIED.values())"],cwd=ROOT,text=True,capture_output=True,timeout=10)
        self.assertEqual(r.returncode,0,r.stderr)


if __name__=="__main__":unittest.main()
