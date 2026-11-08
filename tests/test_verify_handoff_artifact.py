"""Adversarial offline ZIP verification; never calls GitHub or writes remote refs."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/verify_handoff_artifact.py"
spec = importlib.util.spec_from_file_location("verify_handoff_artifact", SCRIPT)
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)

VALID = {
    "schema": 2, "canonical_repo": "kk051780/toy-wars-factory",
    "release_decision": "HOLD_ENGINE_UNVERIFIED",
    "source_revision": "7e3b22efbfd79220360e1e9c5e1b02f7cc417c02",
}


def member(name, mode=stat.S_IFREG | 0o644):
    info = zipfile.ZipInfo(name)
    info.create_system = 3
    info.external_attr = mode << 16
    info.compress_type = zipfile.ZIP_DEFLATED
    return info


def archive_bytes(state=None, manifest=True, entries=None):
    content = {
        "CHAT_HANDOFF.md": b"# Handoff (not authoritative)\n",
        "LATEST_STATE.json": json.dumps(VALID if state is None else state).encode(),
    }
    if manifest:
        content["HANDOFF_SHA256SUMS.txt"] = "".join(
            hashlib.sha256(content[k]).hexdigest() + "  " + k + "\n"
            for k in verifier.TWO).encode()
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w") as archive:
        if entries is None:
            entries = [(member(key), value) for key, value in content.items()]
        for info, value in entries:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                archive.writestr(info, value)
    return result.getvalue()


class HandoffArtifactTrustBoundary(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="twf-artifact-verifier-")
        self.addCleanup(temporary.cleanup)
        self.zip_path = Path(temporary.name) / "artifact.zip"

    def inspect(self, data):
        self.zip_path.write_bytes(data)
        return verifier.verify_archive(self.zip_path)

    def assert_rejected(self, data):
        with self.assertRaises(ValueError):
            self.inspect(data)

    def test_valid_current_manifest_is_data_only_not_provenance(self):
        result = self.inspect(archive_bytes())
        self.assertEqual(result["status"], "ARCHIVE_STRUCTURE_VALID_ONLY")
        self.assertFalse(result["provider_authenticated"])
        self.assertFalse(result["main_ancestry_verified"])
        self.assertFalse(result["authorizes_write"])
        self.assertIn("sha256", result["integrity"])

    def test_real_legacy_format_without_manifest_is_explicitly_weaker(self):
        result = self.inspect(archive_bytes(manifest=False))
        self.assertEqual(result["integrity"], "legacy_zip_crc_only_no_sha256_manifest")

    def test_wrong_repo_and_fake_release_fail_closed(self):
        for change in ({"canonical_repo": "attacker/other"},
                       {"release_decision": "PUBLISHED"},
                       {"schema": True},
                       {"source_revision": "f" * 39}):
            with self.subTest(change=change):
                self.assert_rejected(archive_bytes(state={**VALID, **change}))

    def test_duplicate_json_keys_rejected_even_with_matching_manifest(self):
        bad = b'{"schema":2,"schema":2,"canonical_repo":"kk051780/toy-wars-factory"}'
        self.assert_rejected(archive_bytes(entries=[
            (member("CHAT_HANDOFF.md"), b"hand off\n"),
            (member("LATEST_STATE.json"), bad),
        ]))

    def test_zip_duplicate_entries_rejected(self):
        self.assert_rejected(archive_bytes(entries=[
            (member("CHAT_HANDOFF.md"), b"one\n"),
            (member("LATEST_STATE.json"), json.dumps(VALID).encode()),
            (member("LATEST_STATE.json"), json.dumps(VALID).encode()),
        ]))

    def test_zip_traversal_and_extra_paths_rejected(self):
        for name in ("../LATEST_STATE.json", "status/LATEST_STATE.json",
                     "/LATEST_STATE.json", "tools/execute.py"):
            with self.subTest(name=name):
                self.assert_rejected(archive_bytes(entries=[
                    (member("CHAT_HANDOFF.md"), b"ok\n"),
                    (member(name), json.dumps(VALID).encode()),
                ]))

    def test_symlink_member_fails_closed(self):
        self.assert_rejected(archive_bytes(entries=[
            (member("CHAT_HANDOFF.md", stat.S_IFLNK | 0o777), b"LATEST_STATE.json"),
            (member("LATEST_STATE.json"), json.dumps(VALID).encode()),
        ]))

    def test_executable_extra_or_directory_rejected(self):
        self.assert_rejected(archive_bytes(entries=[
            (member("CHAT_HANDOFF.md"), b"ok\n"),
            (member("LATEST_STATE.json", stat.S_IFDIR | 0o755), json.dumps(VALID).encode()),
        ]))

    def test_correctly_checksumed_archive_required(self):
        current = archive_bytes()
        current = current.replace(b"HANDOFF_SHA256SUMS.txt", b"HANDOFF_SHA256SUMS.txt")
        self.assertIn("sha256", self.inspect(current)["integrity"])
        bad = archive_bytes(entries=[
            (member("CHAT_HANDOFF.md"), b"some handoff\n"),
            (member("LATEST_STATE.json"), json.dumps(VALID).encode()),
            (member("HANDOFF_SHA256SUMS.txt"), b"0" * 64 + b"  CHAT_HANDOFF.md\n"),
        ])
        self.assert_rejected(bad)

    def test_bad_zip_and_member_expansion_budget_fail_closed(self):
        self.assert_rejected(b"not a ZIP")
        giant = archive_bytes(entries=[
            (member("CHAT_HANDOFF.md"), b"a" * verifier.MAX_MEMBER),
            (member("LATEST_STATE.json"), json.dumps(VALID).encode()),
        ])
        self.assert_rejected(giant)

    def test_cli_never_claims_authority_and_failure_nonzero(self):
        self.zip_path.write_bytes(archive_bytes(manifest=False))
        good = subprocess.run([sys.executable, str(SCRIPT), str(self.zip_path)],
                              capture_output=True, text=True, check=False)
        self.assertEqual(good.returncode, 0, good.stderr)
        self.assertFalse(json.loads(good.stdout)["authorizes_write"])
        self.zip_path.write_bytes(b"bad ZIP")
        bad = subprocess.run([sys.executable, str(SCRIPT), str(self.zip_path)],
                             capture_output=True, text=True, check=False)
        self.assertEqual(bad.returncode, 2)
        self.assertEqual(json.loads(bad.stdout)["status"], "UNTRUSTED_STALE")


if __name__ == "__main__":
    unittest.main()
