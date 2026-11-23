"""Synthetic unit fixtures only; these are never Studio or approval evidence."""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile

import resolve_artifact as gate

NOW = datetime.now(timezone.utc).replace(microsecond=0)
HEAD, BASE, MERGE = "a" * 40, "b" * 40, "c" * 40
RUN, PR = 1001, 1013


def timestamp(minutes=0):
    return (NOW + timedelta(minutes=minutes)).isoformat()


def archive(files):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as stream:
        for name, value in files.items():
            stream.writestr(name, value if isinstance(value, bytes) else json.dumps(value).encode())
    return output.getvalue()


class SelectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        repo = {"id": gate.REPO_ID, "full_name": gate.REPO, "fork": False}
        self.pr = {"number": PR, "state": "open", "merge_commit_sha": MERGE,
                   "head": {"sha": HEAD, "ref": "quality/example", "repo": copy.deepcopy(repo)},
                   "base": {"sha": BASE, "ref": gate.RC, "repo": copy.deepcopy(repo)}}
        self.payload = {"number": PR, "pull_request": copy.deepcopy(self.pr)}
        self.ctx = gate.context("pull_request", self.payload, MERGE)
        self.ref = {"object": {"sha": BASE}}
        self.run = {"id": RUN, "run_attempt": 1, "workflow_id": gate.WORKFLOW_ID,
                    "path": gate.WORKFLOW, "event": "pull_request", "head_sha": HEAD,
                    "head_branch": "quality/example", "repository": copy.deepcopy(repo),
                    "head_repository": copy.deepcopy(repo), "created_at": timestamp(-10),
                    "run_started_at": timestamp(-9), "updated_at": timestamp(-7),
                    "status": "completed", "conclusion": "success",
                    "pull_requests": [{"number": PR, "head": copy.deepcopy(self.pr["head"]),
                                       "base": copy.deepcopy(self.pr["base"])}]}
        self.runs = {"total_count": 1, "workflow_runs": [copy.deepcopy(self.run)]}
        # Deliberately not a real Place: the new helper checks provenance only.
        # The unchanged check_art_quality validator still runs on actual XML in CI.
        self.place = b"synthetic provenance fixture; not a Studio Place or approval"
        digest = hashlib.sha256(self.place).hexdigest()
        self.place_files = {"example.rbxlx": self.place, "RECEIPT.json": {
            "status": "PRIVATE_SOURCE_QA_NOT_OFFICIAL", "lua_sources": 80,
            "rojo_sources_exact": 80, "one_game": True, "other79_byte_exact": True,
            "official_rc_adopted": False, "owner_art": "ART_NO_GO",
            "place_bytes": len(self.place), "place_sha256": digest}}
        self.report_files = {"ART_RC_INTAKE_RECEIPT.json": {
            "schema": "P0D_ART_QUALITY_SAMEHEAD_RC80_RECEIPT_V1", "github_head": MERGE,
            "github_run_id": str(RUN), "github_ref": f"refs/pull/{PR}/merge",
            "forest_candidate_source_gate": "PASS", "official_script_count": 80,
            "owner_accepted": False, "official_art_adoption_by_this_gate": False,
            "art_decision": "ART_NO_GO"}, "ART_CHECK_FOREST_PRIVATE80.json": {
                "source": {"source_gate": "PASS", "script_count": 80,
                           "place_bytes": len(self.place), "place_sha256": digest},
                "art_decision": "ART_NO_GO", "owner_accepted": False}}
        self.repack()
        self.calls = []

    def repack(self):
        self.place_zip = self.directory / "place.zip"
        self.report_zip = self.directory / "report.zip"
        self.place_zip.write_bytes(archive(self.place_files))
        self.report_zip.write_bytes(archive(self.report_files))
        records = []
        for ident, name, path in [(2001, gate.PLACE_ARTIFACT, self.place_zip),
                                  (2002, gate.REPORT_ARTIFACT, self.report_zip)]:
            raw = path.read_bytes()
            records.append({"id": ident, "name": name, "size_in_bytes": len(raw),
                            "digest": "sha256:" + hashlib.sha256(raw).hexdigest(),
                            "created_at": timestamp(-8), "expires_at": timestamp(60 * 24 * 7),
                            "expired": False, "workflow_run": {
                                "id": RUN, "head_sha": HEAD, "head_branch": "quality/example",
                                "repository_id": gate.REPO_ID, "head_repository_id": gate.REPO_ID}})
        self.artifacts = {"total_count": len(records), "artifacts": records}

    def api(self, path):
        self.calls.append(path)
        if path == f"{gate.PREFIX}/pulls/{PR}":
            return copy.deepcopy(self.pr)
        if path == f"{gate.PREFIX}/git/ref/heads/{gate.RC}":
            return copy.deepcopy(self.ref)
        if path == f"{gate.PREFIX}/actions/runs?head_sha={HEAD}&event=pull_request&per_page=100":
            return copy.deepcopy(self.runs)
        if path == f"{gate.PREFIX}/actions/runs/{RUN}":
            return copy.deepcopy(self.run)
        if path == f"{gate.PREFIX}/actions/runs/{RUN}/artifacts?per_page=100":
            return copy.deepcopy(self.artifacts)
        raise AssertionError("Unexpected API call: " + path)

    def select(self):
        return gate.select(self.api, self.ctx, NOW)

    def verify(self):
        return gate.verify_downloads(self.select(), self.place_zip, self.report_zip)

    def test_exact_pr_selection_and_archive_provenance(self):
        selection = self.select()
        self.assertEqual(selection["run_id"], RUN)
        self.assertEqual(selection["artifacts"]["place"]["id"], 2001)
        place, receipt = gate.verify_downloads(selection, self.place_zip, self.report_zip)
        self.assertEqual(place, self.place)
        self.assertEqual(receipt["place_sha256"], hashlib.sha256(self.place).hexdigest())
        self.assertFalse(selection["owner_accepted"])
        self.assertEqual(selection["art_decision"], "ART_NO_GO")

    def test_explicit_manual_input_does_not_claim_same_head(self):
        ctx = gate.context("workflow_dispatch", {}, "d" * 40, str(RUN), gate.PLACE_ARTIFACT)
        selected = gate.select(self.api, ctx, NOW)
        self.assertEqual(selected["producer_head"], HEAD)
        self.assertEqual(selected["context"]["kind"], "MANUAL_EXPLICIT")
        self.assertNotEqual(selected["producer_head"], ctx["check_head"])
        self.assertEqual(gate.verify_downloads(selected, self.place_zip)[0], self.place)

    def test_implicit_manual_and_invalid_events_are_rejected(self):
        for event, run, name in [("workflow_dispatch", "", gate.PLACE_ARTIFACT),
                                 ("workflow_dispatch", str(RUN), ""),
                                 ("workflow_dispatch", str(RUN), "name\ninjected=value"),
                                 ("push", str(RUN), gate.PLACE_ARTIFACT)]:
            with self.subTest(event=event, run=run, name=name), self.assertRaises(gate.RedGate):
                gate.context(event, {}, MERGE, run, name)

    def test_wrong_producer_identity_is_rejected(self):
        original = copy.deepcopy(self.run)
        variants = [("head_sha", "d" * 40), ("head_branch", "other"),
                    ("path", ".github/workflows/other.yml"), ("workflow_id", 999),
                    ("event", "push"), ("id", RUN + 1), ("conclusion", "failure")]
        for key, value in variants:
            with self.subTest(key=key), self.assertRaises(gate.RedGate):
                self.run = copy.deepcopy(original)
                self.run[key] = value
                self.select()
        for key, value in [("full_name", "foreign/repo"), ("fork", True), ("id", 5)]:
            with self.subTest(repo_key=key), self.assertRaises(gate.RedGate):
                self.run = copy.deepcopy(original)
                self.run["head_repository"][key] = value
                self.select()

    def test_other_pr_base_and_missing_binding_are_rejected(self):
        original = copy.deepcopy(self.run)
        for part, key, value in [(None, "number", PR + 1), ("base", "sha", "d" * 40),
                                 ("base", "ref", "main"), ("head", "sha", "d" * 40)]:
            self.run = copy.deepcopy(original)
            binding = self.run["pull_requests"][0]
            (binding if part is None else binding[part])[key] = value
            with self.subTest(part=part, key=key), self.assertRaises(gate.RedGate):
                self.select()
        for bindings in ([], [original["pull_requests"][0]] * 2):
            self.run = copy.deepcopy(original)
            self.run["pull_requests"] = bindings
            with self.assertRaises(gate.RedGate):
                self.select()

    def test_live_head_base_merge_and_rc_movement_fail(self):
        original = copy.deepcopy(self.pr)
        for side in ("head", "base"):
            self.pr = copy.deepcopy(original)
            self.pr[side]["sha"] = "d" * 40
            with self.subTest(side=side), self.assertRaises(gate.RedGate):
                self.select()
        self.pr = copy.deepcopy(original)
        self.pr["merge_commit_sha"] = "e" * 40
        with self.assertRaisesRegex(gate.RedGate, "MERGE_SHA"):
            self.select()
        self.pr = original
        self.ref["object"]["sha"] = "e" * 40
        with self.assertRaisesRegex(gate.RedGate, "RC_BASE_MOVED"):
            self.select()

    def add_older_green(self):
        old = copy.deepcopy(self.run)
        old.update(id=RUN - 1, created_at=timestamp(-20))
        self.runs = {"total_count": 2, "workflow_runs": [old, copy.deepcopy(self.run)]}

    def test_latest_pending_never_uses_older_green(self):
        self.add_older_green()
        self.run.update(status="queued", conclusion=None, run_started_at=None)
        with self.assertRaises(gate.Pending):
            self.select()
        self.assertNotIn(f"{gate.PREFIX}/actions/runs/{RUN - 1}", self.calls)

    def test_latest_failed_never_uses_older_green(self):
        self.add_older_green()
        for outcome in ("failure", "cancelled", "timed_out", "skipped"):
            self.run["conclusion"] = outcome
            with self.subTest(outcome=outcome), self.assertRaisesRegex(gate.RedGate, "PRODUCER_FAILED"):
                self.select()
        self.assertNotIn(f"{gate.PREFIX}/actions/runs/{RUN - 1}", self.calls)

    def test_latest_attempt_rejects_previous_attempt_artifacts(self):
        self.run.update(run_attempt=2, run_started_at=timestamp(-5), updated_at=timestamp(-2))
        with self.assertRaisesRegex(gate.RedGate, "OLD_ATTEMPT"):
            self.select()
        for row in self.artifacts["artifacts"]:
            row["created_at"] = timestamp(-3)
        self.assertEqual(self.select()["run_attempt"], 2)

    def test_incomplete_and_duplicate_api_lists_fail(self):
        self.runs["total_count"] = 2
        with self.assertRaisesRegex(gate.RedGate, "API_LIST"):
            self.select()
        self.runs["workflow_runs"].append(copy.deepcopy(self.run))
        with self.assertRaisesRegex(gate.RedGate, "DUPLICATE_RUN"):
            self.select()

    def test_expired_duplicate_missing_and_empty_artifacts(self):
        original = copy.deepcopy(self.artifacts)
        for field, value in [("expired", True), ("expires_at", timestamp(-1)),
                             ("size_in_bytes", 0), ("digest", ""), ("id", False)]:
            self.artifacts = copy.deepcopy(original)
            self.artifacts["artifacts"][0][field] = value
            with self.subTest(field=field), self.assertRaises(gate.RedGate):
                self.select()
        self.artifacts = copy.deepcopy(original)
        self.artifacts["artifacts"].append(copy.deepcopy(self.artifacts["artifacts"][0]))
        self.artifacts["total_count"] = 3
        with self.assertRaisesRegex(gate.RedGate, "DUPLICATE_EXACT_ARTIFACT"):
            self.select()
        self.artifacts = {"total_count": 0, "artifacts": []}
        with self.assertRaises(gate.Pending):
            self.select()

    def test_artifact_wrong_run_head_or_repository_fails(self):
        original = copy.deepcopy(self.artifacts)
        for key, value in [("id", RUN + 1), ("head_sha", "e" * 40),
                           ("repository_id", 99), ("head_repository_id", 99),
                           ("head_branch", "other")]:
            self.artifacts = copy.deepcopy(original)
            self.artifacts["artifacts"][0]["workflow_run"][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(gate.RedGate, "RUN_BINDING"):
                self.select()

    def test_wait_is_bounded_and_can_observe_ready_artifacts(self):
        elapsed, polls = [0], [0]
        def initially_missing(path):
            if path.endswith("/artifacts?per_page=100"):
                polls[0] += 1
                if polls[0] == 1:
                    return {"total_count": 0, "artifacts": []}
            return self.api(path)
        result = gate.wait_for_selection(initially_missing, self.ctx, 20,
                                         clock=lambda: elapsed[0],
                                         sleep=lambda seconds: elapsed.__setitem__(0, elapsed[0] + seconds),
                                         utcnow=lambda: NOW)
        self.assertEqual(result["run_id"], RUN)
        self.assertEqual(elapsed[0], 10)
        self.runs = {"total_count": 0, "workflow_runs": []}
        elapsed[0] = 0
        with self.assertRaisesRegex(gate.RedGate, "WAIT_TIMEOUT"):
            gate.wait_for_selection(self.api, self.ctx, 20, clock=lambda: elapsed[0],
                                    sleep=lambda seconds: elapsed.__setitem__(0, elapsed[0] + seconds),
                                    utcnow=lambda: NOW)
        self.assertEqual(elapsed[0], 20)

    def test_failed_producer_is_not_retried(self):
        self.run["conclusion"] = "failure"
        with self.assertRaisesRegex(gate.RedGate, "PRODUCER_FAILED"):
            gate.wait_for_selection(self.api, self.ctx, 20, sleep=mock.Mock(), utcnow=lambda: NOW)

    def test_completion_during_metadata_get_uses_post_fetch_utc(self):
        observed_clock = [NOW]
        def completes_during_get(path):
            if path == f"{gate.PREFIX}/actions/runs/{RUN}":
                self.run["updated_at"] = (NOW + timedelta(seconds=1)).isoformat()
                observed_clock[0] = NOW + timedelta(seconds=2)
            return self.api(path)
        # A historical fixed snapshot must still reject metadata from its future.
        with self.assertRaisesRegex(gate.RedGate, "RUN_CHRONOLOGY"):
            gate.select(completes_during_get, self.ctx, NOW)
        observed_clock[0] = NOW
        selected = gate.wait_for_selection(completes_during_get, self.ctx, 0,
                                           utcnow=lambda: observed_clock[0])
        self.assertEqual(selected["run_id"], RUN)
        self.assertEqual(selected["selected_at"], (NOW + timedelta(seconds=2)).isoformat())

    def test_selection_drift_after_download_fails(self):
        first = self.select()
        for field, value in [("run_attempt", 2), ("run_id", RUN + 1), ("producer_head", "e" * 40)]:
            second = copy.deepcopy(first)
            second[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(gate.RedGate, "SELECTION_CHANGED"):
                gate.same_selection(first, second)
        second = copy.deepcopy(first)
        second["artifacts"]["place"]["id"] += 1
        with self.assertRaises(gate.RedGate):
            gate.same_selection(first, second)

    def test_zip_bytes_and_size_are_bound_to_github_digest(self):
        selected = self.select()
        raw = self.place_zip.read_bytes()
        self.place_zip.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
        with self.assertRaisesRegex(gate.RedGate, "ZIP_DIGEST"):
            gate.verify_downloads(selected, self.place_zip, self.report_zip)
        self.place_zip.write_bytes(raw[:-1])
        with self.assertRaisesRegex(gate.RedGate, "ZIP_SIZE"):
            gate.verify_downloads(selected, self.place_zip, self.report_zip)

    def test_publisher_receipt_wrong_merge_run_ref_or_approval_fails(self):
        original = copy.deepcopy(self.report_files)
        fields = [("github_head", "e" * 40), ("github_run_id", str(RUN + 1)),
                  ("github_ref", "refs/heads/" + gate.RC), ("owner_accepted", True),
                  ("official_art_adoption_by_this_gate", True),
                  ("forest_candidate_source_gate", "FAIL"), ("official_script_count", 69)]
        for key, value in fields:
            self.report_files = copy.deepcopy(original)
            self.report_files["ART_RC_INTAKE_RECEIPT.json"][key] = value
            self.repack()  # Valid ZIP digest cannot excuse a wrong producer receipt.
            with self.subTest(key=key), self.assertRaises(gate.RedGate):
                self.verify()

    def test_place_hash_and_size_must_match_both_receipts(self):
        original_place, original_report = copy.deepcopy(self.place_files), copy.deepcopy(self.report_files)
        for destination, key, value in [("place", "place_sha256", "0" * 64),
                                         ("report", "place_sha256", "0" * 64),
                                         ("place", "place_bytes", 1), ("report", "place_bytes", 1)]:
            self.place_files, self.report_files = copy.deepcopy(original_place), copy.deepcopy(original_report)
            target = self.place_files["RECEIPT.json"] if destination == "place" else self.report_files[
                "ART_CHECK_FOREST_PRIVATE80.json"]["source"]
            target[key] = value
            self.repack()
            with self.subTest(destination=destination, key=key), self.assertRaisesRegex(gate.RedGate, "HASH_OR_SIZE"):
                self.verify()

    def test_source_report_cannot_replace_no_go_with_approval(self):
        original = copy.deepcopy(self.report_files)
        for key, value in [("source_gate", "FAIL"), ("script_count", 69)]:
            self.report_files = copy.deepcopy(original)
            self.report_files["ART_CHECK_FOREST_PRIVATE80.json"]["source"][key] = value
            self.repack()
            with self.assertRaises(gate.RedGate):
                self.verify()
        self.report_files = original
        self.report_files["ART_CHECK_FOREST_PRIVATE80.json"]["owner_accepted"] = True
        self.repack()
        with self.assertRaises(gate.RedGate):
            self.verify()

    def test_missing_receipt_and_nonunique_place_fail(self):
        original = copy.deepcopy(self.place_files)
        self.place_files.pop("RECEIPT.json")
        self.repack()
        with self.assertRaisesRegex(gate.RedGate, "RECEIPT_MISSING"):
            self.verify()
        self.place_files = original
        self.place_files["second.rbxlx"] = self.place
        self.repack()
        with self.assertRaisesRegex(gate.RedGate, "PLACE_NOT_UNIQUE"):
            self.verify()
        self.place_files.pop("example.rbxlx")
        self.place_files.pop("second.rbxlx")
        self.repack()
        with self.assertRaisesRegex(gate.RedGate, "PLACE_NOT_UNIQUE"):
            self.verify()

    def test_unsafe_or_duplicate_zip_members_fail(self):
        self.place_files["../outside.txt"] = b"no extraction"
        self.repack()
        with self.assertRaisesRegex(gate.RedGate, "UNSAFE_ARTIFACT_MEMBER"):
            self.verify()
        self.place_files.pop("../outside.txt")
        self.repack()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(self.place_zip, "a") as stream:
                stream.writestr("example.rbxlx", b"second member")
        raw = self.place_zip.read_bytes()
        self.artifacts["artifacts"][0].update(size_in_bytes=len(raw),
            digest="sha256:" + hashlib.sha256(raw).hexdigest())
        with self.assertRaisesRegex(gate.RedGate, "DUPLICATE_ARTIFACT_MEMBER"):
            self.verify()

    def test_duplicate_json_keys_fail(self):
        with self.assertRaisesRegex(gate.RedGate, "DUPLICATE_JSON_KEY"):
            gate.load_json('{"github_head":"wrong","github_head":"right"}')

    def test_cli_rechecks_and_writes_only_verified_input(self):
        event = self.directory / "event.json"
        event.write_text(json.dumps(self.payload))
        report, output = self.directory / "result.json", self.directory / "github-output"
        source, receipt = self.place_zip.read_bytes(), self.report_zip.read_bytes()
        api = mock.Mock(side_effect=self.api)
        api.download.side_effect = lambda ident, path: path.write_bytes(source if ident == 2001 else receipt)
        with mock.patch.object(gate, "GitHubReadOnly", return_value=api), mock.patch.dict(
                gate.os.environ, {"GITHUB_REPOSITORY": gate.REPO}):
            result = gate.main(["--event", "pull_request", "--event-file", str(event),
                                "--head", MERGE, "--wait-seconds", "0",
                                "--directory", str(self.directory / "download"),
                                "--report", str(report), "--github-output", str(output)])
        self.assertEqual(result, 0)
        self.assertEqual(json.loads(report.read_text())["status"], "VERIFIED_INPUT_NOT_ART_APPROVAL")
        self.assertEqual((self.directory / "download/SELECTED_AUTHENTIC_ART_INPUT.rbxlx").read_bytes(), self.place)
        self.assertGreaterEqual(self.calls.count(f"{gate.PREFIX}/pulls/{PR}"), 2)
        self.assertIn("mode=PR", output.read_text())


if __name__ == "__main__":
    unittest.main()
