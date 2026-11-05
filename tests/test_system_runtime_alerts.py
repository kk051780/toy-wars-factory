"""A12 synthetic adversaries through the accepted transport and observers."""
from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tests")]
from tools import system_runtime_alerts as target
from test_system_incident_observer import fixtures, Provider, set_holder, NOW
from test_system_github_evidence import mutate
from test_system_service_observer import IDS


def rules():
    return {"service_timeout_seconds": {"author": 1800, "meta": 1800, "reviewer": 1800},
            "ci_timeout_seconds": 900, "max_observation_age_seconds": 120, "replay_window_seconds": 172800}


def later(seconds):
    return (datetime.fromisoformat(NOW.replace("Z", "+00:00")) + timedelta(seconds=seconds)).isoformat()


def pending(data, run=101, *, attempt=1, created="2026-10-27T12:25:00Z"):
    path = "/actions/runs/" + str(run)
    row = json.loads(data[path].text)
    row.update(status="in_progress", conclusion=None, run_attempt=attempt,
               created_at=created, updated_at="2026-10-27T12:29:00Z")
    data[path] = target.github.Response(200, json.dumps(row))
    query = ("/actions/runs?head_sha=" + row["head_sha"] + "&event=pull_request&per_page=100"
             if run == 101 else "/actions/runs?branch=main&event=push&per_page=100")
    data[query] = target.github.Response(200, json.dumps({"total_count": 1, "workflow_runs": [row]}))
    jobs = json.loads(data[f"/actions/runs/{run}/attempts/1/jobs?per_page=100"].text)
    for job in jobs["jobs"]:
        job.update(status="in_progress", conclusion=None, run_attempt=attempt, completed_at=None)
    data[f"/actions/runs/{run}/attempts/{attempt}/jobs?per_page=100"] = target.github.Response(200, json.dumps(jobs))


class RuntimeAlertsTests(unittest.TestCase):
    def collect(self, *, second=False, change=None, projects=None, threshold=None, previous=None, now=NOW):
        p, b, d, s = fixtures(second)
        if change:
            change(p, b, d, s)
        provider = Provider(p, d, s)
        out = target.observe(projects or [p], b, threshold or rules(), provider.get, provider.peek,
                             lambda: now, previous=previous)
        return out, provider, (p, b, d, s)

    def report(self):
        p, b, d, s = fixtures()
        provider = Provider(p, d, s)
        report = target.incident.observe([p], b, provider.get, provider.peek, lambda: NOW)
        return p, b, report

    def states(self, frame):
        return {a["identity"]["kind"] for a in frame["alerts"]}

    def test_two_games_actual_transport_and_accepted_observers_no_grants(self):
        one, two = fixtures(), fixtures(True)
        for second in (False, True):
            out, provider, _ = self.collect(second=second, projects=[one[0], two[0]])
            self.assertEqual(out["verification"], "NOT_VERIFIED")
            self.assertEqual(out["delivery"], "NOT_ATTEMPTED")
            self.assertFalse(out["a12_verified"])
            self.assertFalse(any(out["authority"].values()))
            self.assertEqual(len(provider.peeks), 9)
            self.assertEqual(out["services"][1]["state"], "IN_PROGRESS_NOT_YET_STALE")
            self.assertEqual(out["services"][0]["state"], "OBSERVED_COMPLETED")
            self.assertEqual(self.states(out), set())

    def test_no_update_is_bound_to_exact_current_run_not_green_report(self):
        def change(p,b,d,s):
            row = s[p["roles"]["author"]]
            row["run_details"]["last_run"]["recorded_status"] = "no_update"
            row["run_details"]["latest_result"]["content_text"] = "SUCCESS HOST_WRITE_DENIED token=NEVER_ECHO"
        out, _, _ = self.collect(change=change)
        alert = next(a for a in out["alerts"] if a["identity"]["kind"] == "OBSERVED_NO_UPDATE")
        self.assertEqual(alert["identity"]["subject"]["run_id"], IDS["author"])
        self.assertEqual(out["operation_cause"], "INDETERMINATE")
        self.assertNotIn("NEVER_ECHO", json.dumps(out))

    def test_failed_is_not_current_completed(self):
        out, _, _ = self.collect(change=lambda p,b,d,s:s[p["roles"]["author"]]["run_details"]["last_run"].update(recorded_status="failed"))
        self.assertIn("OBSERVED_FAILED", self.states(out))

    def test_stale_running_ignores_previous_completed_report(self):
        r = rules(); r["service_timeout_seconds"]["meta"] = 600
        out, _, _ = self.collect(threshold=r)
        self.assertIn("STALE_OR_NO_RESULT", self.states(out))
        alert = next(a for a in out["alerts"] if a["identity"]["kind"] == "STALE_OR_NO_RESULT")
        self.assertEqual(alert["identity"]["subject"]["run_id"], IDS["meta"])
        self.assertEqual(out["services"][1]["latest_result_binding"], "PREVIOUS_RUN")

    def test_threshold_boundary_not_early(self):
        r = rules(); r["service_timeout_seconds"]["meta"] = 1200
        out, _, _ = self.collect(threshold=r)
        self.assertNotIn("STALE_OR_NO_RESULT", self.states(out))

    def test_missing_current_result_not_healthy(self):
        out, _, _ = self.collect(change=lambda p,b,d,s:s[p["roles"]["author"]]["run_details"].update(latest_result=None))
        self.assertIn("STALE_OR_NO_RESULT", self.states(out))

    def test_disabled_and_attention_metadata_are_distinct(self):
        for flag in ("disabled", "attention"):
            def change(p,b,d,s):
                row = s[p["roles"]["author"]]
                if flag == "disabled": row["is_enabled"] = False
                else: row["run_details"]["latest_result"]["requires_user_action"] = True
            out, _, _ = self.collect(change=change)
            self.assertIn("SERVICE_DISABLED" if flag == "disabled" else "CURRENT_RESULT_REQUIRES_ATTENTION", self.states(out))

    def test_contradictory_reported_service_label_rejected(self):
        for observed in ("SERVICE_DISABLED", "CURRENT_RESULT_REQUIRES_ATTENTION", "IN_PROGRESS"):
            p,b,report = self.report(); report["services"]["author"]["observation_state"] = observed
            with self.assertRaises(target.EvidenceError): target.classify([p],b,report,rules(),NOW)

    def test_active_lease_retained_and_never_takeover(self):
        def change(p,b,d,s):
            set_holder(p,b,d,{"kind":"META", "owner_id":IDS["meta"], "task_id":p["roles"]["meta"], "epoch":7,
                             "acquired_at":"2026-10-27T12:10:00Z", "expires_at":"2026-10-27T12:40:00Z"})
        out, _, _ = self.collect(change=change)
        self.assertEqual(out["lease"]["state"], "ACTIVE_LEASE")
        self.assertFalse(out["authority"]["takeover_allowed"])

    def test_expired_lease_only_warns_never_steals(self):
        def change(p,b,d,s):
            set_holder(p,b,d,{"kind":"META", "owner_id":IDS["meta"], "task_id":p["roles"]["meta"], "epoch":7,
                             "acquired_at":"2026-10-27T11:50:00Z", "expires_at":"2026-10-27T12:20:00Z"})
        out, _, _ = self.collect(change=change)
        self.assertIn("EXPIRED_LEASE_UNRELEASED", self.states(out))
        self.assertFalse(any(out["authority"].values()))

    def test_ci_pending_in_window_and_timeout_exact_head(self):
        for created, expected in (("2026-10-27T12:25:00Z","CI_RUNNING_IN_WINDOW"), ("2026-10-27T12:00:00Z","CI_TIMEOUT")):
            out, _, (p,b,d,s) = self.collect(change=lambda p,b,d,s:pending(d,created=created))
            ci = next(c for c in out["ci"] if c["target"] == "pr")
            self.assertEqual(ci["state"], expected)
            self.assertEqual(ci["head"], b["github"]["pr_head_sha"])
            self.assertEqual(ci["producing_run_id"], b["github"]["author_run_id"])

    def test_rerun_creation_time_does_not_fake_attempt_timeout(self):
        def change(p,b,d,s):
            pending(d,attempt=2,created="2026-10-27T11:00:00Z");b["github"]["ci_attempt"] = 2
        out, _, _ = self.collect(change=change)
        ci = next(c for c in out["ci"] if c["target"] == "pr")
        self.assertEqual(ci["state"], "INDETERMINATE")
        self.assertNotIn("CI_TIMEOUT", self.states(out))

    def test_main_qa_failure_is_observed_not_silenced_by_pr_pass(self):
        def change(p,b,d,s):
            for path in ("/actions/runs?branch=main&event=push&per_page=100",):
                mutate(d,path,lambda x:[r.update(conclusion="failure") for r in x.get("workflow_runs",[x])])
            mutate(d,"/actions/runs/100/attempts/1/jobs?per_page=100",lambda x:x["jobs"][0].update(conclusion="failure"))
        out, _, _ = self.collect(change=change)
        self.assertIn("MAIN_QA_FAILED", self.states(out))

    def test_wrong_role_reused_run_and_duplicate_service_rejected(self):
        for change in (
            lambda p,b,d,s:s[p["roles"]["reviewer"]]["run_details"]["last_run"].update(id=IDS["author"]),
            lambda p,b,d,s:s[p["roles"]["author"]].update(id=p["roles"]["meta"])):
            out, _, _ = self.collect(change=change)
            self.assertEqual(self.states(out), {"CONNECTOR_UNAVAILABLE"})
            self.assertFalse(any(out["authority"].values()))

    def test_foreign_game_task_reuse_and_unbound_project_rejected(self):
        p,b,d,s=fixtures();q,_,_,_=fixtures(True);q["roles"]["meta"]=p["roles"]["meta"]
        with self.assertRaises(Exception): target.observe([p,q],b,rules(),None,None,lambda:NOW)

    def test_missing_duplicate_wrong_attempt_jobs_fail_closed(self):
        changes = [lambda x:x["jobs"].pop(), lambda x:x["jobs"].append(deepcopy(x["jobs"][0])),
                   lambda x:x["jobs"][0].update(run_attempt=2),lambda x:x["jobs"][0].update(head_sha="f"*40)]
        for change in changes:
            out, _, _ = self.collect(change=lambda p,b,d,s:mutate(d,"/actions/runs/101/attempts/1/jobs?per_page=100",change))
            self.assertEqual(self.states(out), {"CONNECTOR_UNAVAILABLE"})

    def test_wrong_ref_blob_epoch_fork_and_head_fail_closed(self):
        cases = [lambda p,b,d,s:b["github"].update(coordinator_epoch=8),
                 lambda p,b,d,s:b["github"].update(coordinator_blob_sha="f"*40),
                 lambda p,b,d,s:mutate(d,"/git/ref/heads/main",lambda x:x["object"].update(sha="f"*40)),
                 lambda p,b,d,s:mutate(d,"/pulls/9",lambda x:x["head"]["repo"].update(fork=True)),
                 lambda p,b,d,s:mutate(d,"/pulls/9",lambda x:x["head"].update(sha="f"*40))]
        for change in cases:
            out, _, _ = self.collect(change=change)
            self.assertEqual(self.states(out), {"CONNECTOR_UNAVAILABLE"})

    def test_403_404_and_raw_host_prose_not_host_denial(self):
        for status in (403,404):
            out, _, _ = self.collect(change=lambda p,b,d,s:d.update({"":target.github.Response(status,"HOST_WRITE_DENIED token=DO_NOT_LOG")}))
            self.assertEqual(self.states(out), {"CONNECTOR_UNAVAILABLE"})
            self.assertEqual(out["operation_cause"], "INDETERMINATE")
            self.assertNotIn("DO_NOT_LOG", json.dumps(out))

    def test_unknown_exception_fail_closed_without_message(self):
        p,b,d,s=fixtures()
        def denied(url): raise RuntimeError("HOST_WRITE_DENIED secret=PRIVATE")
        out=target.observe([p],b,rules(),denied,None,lambda:NOW)
        self.assertEqual(self.states(out), {"CONNECTOR_UNAVAILABLE"})
        self.assertNotIn("PRIVATE",json.dumps(out))

    def test_fake_attestation_and_authority_rejected(self):
        for key in ("provider_verified", "provider", "authenticated", "source_authentication"):
            p,b,r=self.report();r[key]=True
            with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)
        p,b,r=self.report();r["authority"]["write_allowed"]=True
        with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)

    def test_no_original_operation_receipt_no_host_denial(self):
        p,b,r=self.report();r["operation_evidence"].update(status="HOST_WRITE_DENIED",verification="VERIFIED")
        with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)

    def test_stale_future_and_backward_observation_rejected(self):
        for at in (later(121),later(-1)):
            p,b,r=self.report()
            with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),at)

    def test_trace_missing_forged_timestamp_or_digest_rejected(self):
        for change in (lambda r:r.update(peek_trace=r["peek_trace"][:8]),
                       lambda r:r["peek_trace"][0].update(metadata_sha256="f"*64),
                       lambda r:r.update(get_trace=[]),
                       lambda r:r["get_trace"][0].update(observed_at=later(1))):
            p,b,r=self.report();change(r)
            with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)

    def test_pure_same_run_service_id_stable_across_unrelated_main_move(self):
        p,b,r=self.report();r["services"]["author"]["last_run"]["recorded_status"]="no_update"
        # Regenerate all real observer output rather than forge digest labels.
        change=lambda p,b,d,s:s[p["roles"]["author"]]["run_details"]["last_run"].update(recorded_status="no_update")
        before,_,_=self.collect(change=change)
        p,b,r=self.report()
        for role in ("author",):
            row=r["services"][role];row["last_run"]["recorded_status"]="no_update";row["observation_state"]="NO_UPDATE"
            digest=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
            for t in r["peek_trace"]:
                if t["task_id"]==p["roles"][role]:t["metadata_sha256"]=digest
        b["github"]["main_sha"]="f"*40;r["main_sha"]="f"*40;r["status_only"]=["status/CHAT_HANDOFF.md"]
        r["get_trace"].append({"method":"GET","url":"https://api.github.com/repos/"+p["repository"]+"/compare/"+"a"*40+"..."+"f"*40,"body_sha256":"a"*64,"observed_at":NOW})
        after=target.classify([p],b,r,rules(),later(1))
        a=next(a for a in before["alerts"] if a["identity"]["kind"]=="OBSERVED_NO_UPDATE")
        c=next(a for a in after["alerts"] if a["identity"]["kind"]=="OBSERVED_NO_UPDATE")
        self.assertEqual(a["id"],c["id"])
        self.assertEqual(target.reconcile(before,after)["alerts"][0]["repeats"],2)

    def alert(self):
        return self.collect(change=lambda p,b,d,s:s[p["roles"]["author"]]["run_details"]["last_run"].update(recorded_status="no_update"))[0]

    def test_disappearance_only_unverified_recovery_candidate(self):
        old=self.alert();current,_,_=self.collect(now=later(1))
        out=target.reconcile(old,current)
        self.assertEqual(len(out["recovery_candidates"]),1)
        self.assertEqual(out["recovery_candidates"][0]["status"],"UNVERIFIED_RECOVERY_CANDIDATE")
        self.assertFalse(out["recovery_candidates"][0]["recovered"])
        self.assertFalse(out["a12_verified"])

    def test_unavailable_connector_never_implies_recovery(self):
        old=self.alert();current,_,_=self.collect(now=later(1),change=lambda p,b,d,s:d.update({"":target.github.Response(404,"x")}))
        out=target.reconcile(old,current)
        self.assertEqual(out["recovery_candidates"][0]["status"],"RECOVERY_UNASSESSABLE")

    def test_duplicate_alert_and_replayed_observation_rejected(self):
        old=self.alert();current,_,_=self.collect(now=later(1))
        bad=deepcopy(old);bad["alerts"].append(deepcopy(bad["alerts"][0]))
        with self.assertRaises(target.EvidenceError):target.reconcile(bad,current)
        with self.assertRaises(target.EvidenceError):target.reconcile(old,old)

    def test_foreign_prior_state_roles_and_forged_grants_rejected(self):
        old=self.alert();current,_,_=self.collect(now=later(1))
        for change in (lambda x:x.update(repository="other/repo"),lambda x:x["roles"].update(meta="f"*32),
                       lambda x:x.update(verification="LIVE_PROVIDER_VERIFIED"),lambda x:x.update(delivery="ALERT_DELIVERED"),
                       lambda x:x["authority"].update(start_now_allowed=True),lambda x:x["alerts"][0].update(id="f"*64),
                       lambda x:x["alerts"][0].update(recovered=True)):
            bad=deepcopy(old);change(bad)
            with self.assertRaises(target.EvidenceError):target.reconcile(bad,current)

    def test_replay_window_48_hours_max(self):
        old=self.alert();current=deepcopy(old);current["observed_at"]=later(172801)
        with self.assertRaises(target.EvidenceError):target.reconcile(old,current)

    def test_invalid_bool_and_missing_thresholds_rejected(self):
        for change in (lambda x:x.update(ci_timeout_seconds=True),lambda x:x.pop("replay_window_seconds"),
                       lambda x:x["service_timeout_seconds"].update(meta=0),lambda x:x.update(max_observation_age_seconds=121)):
            r=rules();change(r)
            with self.assertRaises(target.EvidenceError):self.collect(threshold=r)

    def test_never_mutates_inputs_or_launches_a_service(self):
        p,b,d,s=fixtures();original=deepcopy((p,b,d,s));provider=Provider(p,d,s)
        out=target.observe([p],b,rules(),provider.get,provider.peek,lambda:NOW)
        self.assertEqual((p,b,d,s),original)
        self.assertTrue(all(url.startswith("https://api.github.com/repos/"+p["repository"]) for url in provider.raw.calls))
        self.assertFalse(any(out["authority"].values()))

    def test_ref_and_job_drift_during_observation_not_healthy(self):
        for path, change in (("/git/ref/heads/main", lambda x:x["object"].update(sha="f"*40)),
                             ("/actions/runs/101/attempts/1/jobs?per_page=100", lambda x:x["jobs"][0].update(run_attempt=2))):
            p,b,d,s=fixtures()
            def during(task,row,provider):
                if len(provider.peeks)>6:mutate(d,path,change)
            provider=Provider(p,d,s,on_peek=during)
            out=target.observe([p],b,rules(),provider.get,provider.peek,lambda:NOW)
            self.assertEqual(self.states(out),{"CONNECTOR_UNAVAILABLE"})
            self.assertFalse(any(out["authority"].values()))

    def test_pure_ci_head_and_qa_lies_rejected(self):
        for change in (lambda r:r["pr"]["ci"].update(head="f"*40),
                       lambda r:r["main_ci"].update(qa="FAIL"),
                       lambda r:r.update(status_only=["src/other.lua"]),
                       lambda r:r["pr"]["ci"]["jobs"][0].update(run_id=True)):
            p,b,r=self.report();change(r)
            with self.assertRaises(target.EvidenceError):target.classify([p],b,r,rules(),NOW)

    def test_prior_secret_fields_and_unsupported_subject_cannot_leak(self):
        old=self.alert();current,_,_=self.collect(now=later(1))
        for change in (lambda x:x["alerts"][0]["identity"]["subject"].update(token="NEVER_PRINT"),
                       lambda x:x["alerts"][0]["evidence"].append("token=NEVER_PRINT"),
                       lambda x:x["services"][0].update(secret="NEVER_PRINT"),
                       lambda x:x["alerts"][0].update(action="RUN_NOW"),
                       lambda x:x["alerts"][0].update(repeats=True)):
            bad=deepcopy(old);change(bad)
            if "token" in bad["alerts"][0]["identity"]["subject"]:
                bad["alerts"][0]["id"]=target._digest(bad["alerts"][0]["identity"])
            with self.assertRaises(target.EvidenceError):target.reconcile(bad,current)

    def test_recovery_candidate_persists_without_claiming_verified_recovery(self):
        old=self.alert();current,_,_=self.collect(now=later(1));first=target.reconcile(old,current)
        fresh,_,_=self.collect(now=later(2));second=target.reconcile(first,fresh)
        self.assertEqual(second["recovery_candidates"],first["recovery_candidates"])
        self.assertFalse(second["recovery_candidates"][0]["recovered"])

    def test_different_current_run_is_not_duplicate_old_run(self):
        first=self.alert()
        def change(p,b,d,s):
            row=s[p["roles"]["author"]]["run_details"]
            row["last_run"].update(id="eeeeeeee-ffff-4aaa-8bbb-cccccccccccc",recorded_status="no_update")
            row["latest_result"]["run_id"]=row["last_run"]["id"]
        current,_,_=self.collect(now=later(1),change=change)
        second=target.reconcile(first,current)
        alert=next(a for a in second["alerts"] if a["identity"]["kind"]=="OBSERVED_NO_UPDATE")
        self.assertNotEqual(alert["id"],first["alerts"][0]["id"])
        self.assertEqual(alert["repeats"],1)

    def test_ci_rerun_or_head_change_never_deduplicated_to_old_ci(self):
        def change(p,b,d,s):pending(d,created="2026-10-27T12:00:00Z")
        first,_,_=self.collect(change=change)
        ci=next(a for a in first["alerts"] if a["identity"]["kind"]=="CI_TIMEOUT")
        for field,value in (("head","f"*40),("attempt",2)):
            identity=deepcopy(ci["identity"]);identity["subject"][field]=value
            self.assertNotEqual(ci["id"],target._digest(identity))

    def test_old_observer_negative_control_has_no_stall_threshold_alert(self):
        p,b,r=self.report()
        self.assertEqual(r["services"]["meta"]["observation_state"],"IN_PROGRESS")
        self.assertNotIn("alerts",r)
        limit=rules();limit["service_timeout_seconds"]["meta"]=600
        out=target.classify([p],b,r,limit,NOW)
        self.assertIn("STALE_OR_NO_RESULT",self.states(out))

    def test_cli_rejects_fake_json_without_echoing_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"request.json";path.write_text('{"provider_verified":true,"token":"DO_NOT_ECHO"}')
            proc=subprocess.run([sys.executable,str(ROOT/"tools/system_runtime_alerts.py"),"--request",str(path)],capture_output=True,text=True,timeout=10)
            self.assertEqual(proc.returncode,2)
            self.assertNotIn("DO_NOT_ECHO",proc.stdout+proc.stderr)
            self.assertEqual(json.loads(proc.stdout)["state"],"INDETERMINATE")


if __name__ == "__main__":
    unittest.main()
