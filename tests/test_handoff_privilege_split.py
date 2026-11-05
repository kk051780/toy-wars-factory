"""Regressions for handoff privileged writer split; not live GitHub authority."""
import pathlib
import re
import subprocess
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / ".github/workflows/handoff-sync.yml").read_text(encoding="utf-8")

VALID_STATE = '{"schema":2,"canonical_repo":"kk051780/toy-wars-factory","source_revision":"e5deff4d5681bca4823a3da0f848e01bc089ae6e","release_decision":"HOLD_ENGINE_UNVERIFIED"}\n'


def sections():
    a, b = SRC.split("\n  status_writer:", 1)
    return a, "\n  status_writer:" + b


def shell_step(name):
    start = "      - name: " + name + "\n"
    segment = SRC.split(start, 1)[1].split("\n      - name:", 1)[0]
    lines = segment.split("        run: |\n", 1)[1].splitlines()
    return "\n".join(line[10:] if line.startswith("          ") else line for line in lines)


def manifest(folder):
    with (folder / "HANDOFF_SHA256SUMS.txt").open("w") as output:
        subprocess.run(["sha256sum", "CHAT_HANDOFF.md", "LATEST_STATE.json"],
                       cwd=folder, stdout=output, check=True)


class HandoffPrivilegeSplit(unittest.TestCase):
    def test_default_repo_permissions_read_only(self):
        self.assertIn("\npermissions:\n  contents: read\n", SRC)
        self.assertEqual(SRC.count("contents: write"), 1)

    def test_separate_verifier_and_writer(self):
        verify, writer = sections()
        self.assertIn("\n  verify:\n    permissions:\n      contents: read\n", verify)
        self.assertIn("  status_writer:\n    needs: verify\n", writer)
        self.assertIn("    permissions:\n      contents: write\n", writer)

    def test_source_tests_and_builder_never_run_with_write_job(self):
        verify, writer = sections()
        for command in ("python3 -m unittest discover", "python3 tools/repository_gate.py",
                        "python3 tools/build_handoff.py"):
            self.assertIn(command, verify)
            self.assertNotIn(command, writer)
        self.assertNotIn("python3 ", writer)

    def test_no_persisted_checkout_credentials(self):
        self.assertEqual(SRC.count("persist-credentials: false"), 2)
        self.assertNotIn("persist-credentials: true", SRC)

    def test_every_external_action_is_immutable_sha(self):
        refs = re.findall(r"^\s*uses: ([^\s]+)", SRC, re.MULTILINE)
        self.assertEqual(len(refs), 4)
        self.assertTrue(all(re.search(r"@[0-9a-f]{40}$", ref) for ref in refs))

    def test_existing_main_push_and_twenty_minute_schedule_kept(self):
        self.assertIn("branches: [main]", SRC)
        self.assertIn("cron: '13,33,53 * * * *'", SRC)
        self.assertIn("  workflow_dispatch:", SRC)
        self.assertNotIn("pull_request:", SRC)

    def test_source_sha_pin_and_main_only_writer(self):
        self.assertEqual(SRC.count("ref: $" + "{{ github.sha }}"), 2)
        self.assertIn("if: github.ref == 'refs/heads/main'", SRC)
        self.assertIn('test "$(git rev-parse HEAD)" = "$TWF_SOURCE_COMMIT"', SRC)
        self.assertIn('git ls-remote origin refs/heads/main | cut -f1', SRC)

    def test_token_only_present_in_final_step(self):
        verify, writer = sections()
        self.assertNotIn("github.token", verify)
        self.assertEqual(writer.count("GH_TOKEN: $" + "{{ github.token }}"), 1)
        self.assertEqual(writer.count("gh auth setup-git"), 1)
        self.assertNotIn("secrets.", SRC)

    def test_exact_two_status_files_only(self):
        writer = sections()[1]
        self.assertIn("git hash-object -w -- status/CHAT_HANDOFF.md", writer)
        self.assertIn("git hash-object -w -- status/LATEST_STATE.json", writer)
        self.assertIn("git mktree", writer)
        self.assertIn("commit-tree \"$snapshot_tree\"", writer)
        self.assertIn("snapshot_ref=\'refs/heads/twf-handoff-snapshots\'", writer)
        self.assertIn("git push origin \"$snapshot_commit:$snapshot_ref\"", writer)
        self.assertNotIn("git push ", sections()[0])
        self.assertNotIn("git push origin HEAD:refs/heads/main", writer)
        self.assertNotIn("git push --force", writer)

    def test_exact_prior_git_object_mode_format(self):
        writer = sections()[1]
        self.assertIn("git ls-tree -r --format='%(objectmode) %(objecttype) %(path)'", writer)
        expected = "100644 blob status/CHAT_HANDOFF.md" + chr(92) + "n100644 blob status/LATEST_STATE.json"
        self.assertIn(expected, writer)
        self.assertNotIn("status/CHAT_HANDOFF.md" + chr(92) * 2 + "n100644", writer)

    def test_writer_only_downloads_passive_artifact(self):
        writer = sections()[1]
        self.assertIn("uses: actions/download-artifact@", writer)
        self.assertIn("name: toy-wars-handoff", writer)
        self.assertNotIn("run-id:", writer)
        self.assertNotIn("bash .verified-handoff", writer)
        self.assertNotIn("source .verified-handoff", writer)

    def test_exact_checksum_manifest_and_bounded_sizes(self):
        self.assertIn("sha256sum --check --status HANDOFF_SHA256SUMS.txt", SRC)
        self.assertIn("sha256sum CHAT_HANDOFF.md LATEST_STATE.json > HANDOFF_SHA256SUMS.txt", SRC)
        self.assertIn('-lt 500000', SRC)

    def artifact(self, extra=False, altered=False, symlink=False):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = pathlib.Path(temporary.name)
        folder = root / ".verified-handoff"
        folder.mkdir()
        (root / "status").mkdir()
        (folder / "CHAT_HANDOFF.md").write_text("Snapshot\n")
        if symlink:
            (root / "outside.json").write_text("{}\n")
            (folder / "LATEST_STATE.json").symlink_to("../outside.json")
        else:
            (folder / "LATEST_STATE.json").write_text(VALID_STATE)
        manifest(folder)
        if extra:
            (folder / "intruder.txt").write_text("extra\n")
        if altered:
            (folder / "LATEST_STATE.json").write_text('{"changed":true}\n')
        script = shell_step("Inspect passive artifact, never execute files from it")
        result = subprocess.run(["bash", "-euo", "pipefail", "-c", script],
                                cwd=root, capture_output=True, text=True)
        return root, result

    def test_valid_artifact_installs_exact_snapshot(self):
        root, result = self.artifact()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((root / "status/CHAT_HANDOFF.md").read_text(), "Snapshot\n")

    def test_extra_artifact_is_rejected(self):
        _, result = self.artifact(extra=True)
        self.assertNotEqual(result.returncode, 0)

    def test_tampered_checksum_is_rejected(self):
        _, result = self.artifact(altered=True)
        self.assertNotEqual(result.returncode, 0)

    def test_symlink_is_rejected(self):
        _, result = self.artifact(symlink=True)
        self.assertNotEqual(result.returncode, 0)


    def bad_payload_with_valid_checksums(self, payload):
        root, first = self.artifact()
        self.assertEqual(first.returncode, 0, first.stderr)
        folder = root / ".verified-handoff"
        (folder / "LATEST_STATE.json").write_text(payload, encoding="utf-8")
        # This is the critical adversary: generate a fresh *matching* checksum
        # rather than corrupting the data after the checksum was calculated.
        manifest(folder)
        script = shell_step("Inspect passive artifact, never execute files from it")
        return subprocess.run(["bash", "-euo", "pipefail", "-c", script],
                              cwd=root, capture_output=True, text=True)

    def test_invalid_json_with_matching_sha_is_rejected(self):
        result = self.bad_payload_with_valid_checksums('{"schema":2,invalid}\n')
        self.assertNotEqual(result.returncode, 0)

    def test_multiple_json_documents_with_matching_sha_are_rejected(self):
        result = self.bad_payload_with_valid_checksums(VALID_STATE + VALID_STATE)
        self.assertNotEqual(result.returncode, 0)

    def test_wrong_repo_with_matching_sha_is_rejected(self):
        result = self.bad_payload_with_valid_checksums(
            VALID_STATE.replace("kk051780/toy-wars-factory", "untrusted/other-repo"))
        self.assertNotEqual(result.returncode, 0)

    def test_schema_downgrade_with_matching_sha_is_rejected(self):
        result = self.bad_payload_with_valid_checksums(VALID_STATE.replace('"schema":2', '"schema":1'))
        self.assertNotEqual(result.returncode, 0)

    def test_release_hold_removed_with_matching_sha_is_rejected(self):
        result = self.bad_payload_with_valid_checksums(
            VALID_STATE.replace("HOLD_ENGINE_UNVERIFIED", "PUBLISHED"))
        self.assertNotEqual(result.returncode, 0)

    def test_bad_source_revision_with_matching_sha_is_rejected(self):
        result = self.bad_payload_with_valid_checksums(
            VALID_STATE.replace("e5deff4d5681bca4823a3da0f848e01bc089ae6e", "NOT_A_GIT_SHA"))
        self.assertNotEqual(result.returncode, 0)

    def test_array_document_with_matching_sha_is_rejected(self):
        result = self.bad_payload_with_valid_checksums('["not", "status"]\n')
        self.assertNotEqual(result.returncode, 0)



if __name__ == "__main__":
    unittest.main()
