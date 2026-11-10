import hashlib
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import verified_intake as m

PACKET = "P0D-TEST-21-20261110-01"
PREFIX = f"handoffs/{PACKET}/"
SAMPLE = b"return {}\n"


def fixture(name="src/main.luau", payload=SAMPLE, **changes):
    manifest = dict(format="P0D_PUBLIC_SOURCE_V1", game_id="TRAP_RAIDERS", work_id="p0d-siege-v19",
                    packet_id=PACKET, public_source_allowed=True,
                    files=[{"path": name, "size": len(payload), "sha256": hashlib.sha256(payload).hexdigest()}])
    manifest.update(changes)
    return {PREFIX + "BUILD_MANIFEST.json": json.dumps(manifest).encode(), PREFIX + name: payload}


class TestIntake(unittest.TestCase):
    def test_registry_21(self):
        self.assertEqual(len(m.registry()["packages"]), 21)

    def test_valid_roundtrip(self):
        self.assertEqual(m.validate_source(PACKET, fixture())["files_verified"], 1)

    def test_integrity_bad_file(self):
        files = fixture()
        files[PREFIX + "src/main.luau"] = b"tampered"
        with self.assertRaisesRegex(m.IntakeError, "SHA mismatch"):
            m.validate_source(PACKET, files)

    def test_manifest_game_mismatch(self):
        with self.assertRaisesRegex(m.IntakeError, "manifest"):
            m.validate_source(PACKET, fixture(game_id="OTHER"))

    def test_manifest_packet_mismatch(self):
        with self.assertRaisesRegex(m.IntakeError, "manifest"):
            m.validate_source(PACKET, fixture(packet_id="P0D-OTHER"))

    def test_manifest_format_mismatch(self):
        with self.assertRaisesRegex(m.IntakeError, "manifest"):
            m.validate_source(PACKET, fixture(format="ZIP_ENCRYPTED"))

    def test_manifest_public_approval_required(self):
        with self.assertRaisesRegex(m.IntakeError, "manifest"):
            m.validate_source(PACKET, fixture(public_source_allowed=False))

    def test_missing_file_fails_closed(self):
        z = fixture()
        z.pop(PREFIX + "src/main.luau")
        with self.assertRaisesRegex(m.IntakeError, "missing or extra"):
            m.validate_source(PACKET, z)

    def test_extra_file_fails_closed(self):
        z = fixture()
        z[PREFIX + "other.txt"] = b"extra"
        with self.assertRaisesRegex(m.IntakeError, "missing or extra"):
            m.validate_source(PACKET, z)

    def test_relative_traversal_rejected(self):
        with self.assertRaises(m.IntakeError):
            m.path_check("src/../../x.lua")

    def test_windows_drive_path_rejected(self):
        with self.assertRaises(m.IntakeError):
            m.path_check("C:\\Users\\evil.lua")

    def test_absolute_path_rejected(self):
        with self.assertRaises(m.IntakeError):
            m.path_check("/home/x.py")

    def test_hidden_path_rejected(self):
        with self.assertRaises(m.IntakeError):
            m.path_check(".git/config.json")

    def test_banned_binary_extension(self):
        with self.assertRaises(m.IntakeError):
            m.path_check("malware.exe")

    def test_manifest_repeated_case_files_rejected(self):
        z = fixture()
        manifest = json.loads(z[PREFIX + "BUILD_MANIFEST.json"])
        manifest["files"].append(dict(manifest["files"][0], path="src/MAIN.luau"))
        z[PREFIX + "BUILD_MANIFEST.json"] = json.dumps(manifest).encode()
        with self.assertRaisesRegex(m.IntakeError, "case collision"):
            m.validate_source(PACKET, z)

    def test_manifest_replacement_file_size_fails(self):
        z = fixture()
        manifest = json.loads(z[PREFIX + "BUILD_MANIFEST.json"])
        manifest["files"][0]["size"] = 200
        z[PREFIX + "BUILD_MANIFEST.json"] = json.dumps(manifest).encode()
        with self.assertRaisesRegex(m.IntakeError, "SHA mismatch"):
            m.validate_source(PACKET, z)

    def test_manifest_replacement_file_hash_fails(self):
        z = fixture()
        manifest = json.loads(z[PREFIX + "BUILD_MANIFEST.json"])
        manifest["files"][0]["sha256"] = "0" * 64
        z[PREFIX + "BUILD_MANIFEST.json"] = json.dumps(manifest).encode()
        with self.assertRaisesRegex(m.IntakeError, "SHA mismatch"):
            m.validate_source(PACKET, z)

    def test_no_live_repo_mutation_commands(self):
        code=(ROOT / "tools" / "verified_intake.py").read_text()
        for cmd in ("git push", "git merge", "git reset", "git checkout", "RobloxStudio", "os.system"):
            self.assertNotIn(cmd, code)

    def test_registry_remainder_distinct(self):
        r=m.registry()
        self.assertEqual(len(r["remaining_originals_not_yet_verified"]),5)
        self.assertEqual(len(set(r["remaining_originals_not_yet_verified"])),5)


if __name__ == "__main__":
    unittest.main()


class EndToEndOfflineGitTest(unittest.TestCase):
    def test_local_git_fetch_and_strict_staging(self):
        import subprocess
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            base = pathlib.Path(directory)
            repo = base / "source_repo"
            repo.mkdir()
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test"], check=True)
            pack_dir = repo / PREFIX
            pack_dir.mkdir(parents=True)
            (pack_dir / "src").mkdir()
            (pack_dir / "src" / "main.luau").write_bytes(SAMPLE)
            content = fixture()[PREFIX + "BUILD_MANIFEST.json"]
            (pack_dir / "BUILD_MANIFEST.json").write_bytes(content)
            subprocess.run(["git", "-C", str(repo), "add", "."], check=True)
            subprocess.run(["git", "-C", str(repo), "commit", "-qm", "test"], check=True)
            sha = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"]).decode().strip()
            old = m.URL
            m.URL = str(repo)
            self.addCleanup(lambda: setattr(m, "URL", old))
            dest = base / "receipt"
            x = m.stage(dest, [{"packet": PACKET, "commit": sha}])
            self.assertEqual(x["packets"], 1)
            self.assertEqual((dest / "packs" / PACKET / "src" / "main.luau").read_bytes(), SAMPLE)
            self.assertEqual(json.loads((dest / "RECEIPT.json").read_text())["results"][0]["commit_sha"], sha)
            with self.assertRaisesRegex(m.IntakeError, "already exists"):
                m.stage(dest, [{"packet": PACKET, "commit": sha}])
