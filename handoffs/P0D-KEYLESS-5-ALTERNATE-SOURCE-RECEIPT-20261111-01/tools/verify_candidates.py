#!/usr/bin/env python3
"""Read-only original-vs-alternate-aware no-key GitHub source receipt verifier.

This tool NEVER installs a game feature. Every source in the frozen registry is
NEW CLEAN-ROOM code, not a decrypted or byte-identical historical game asset.
No Roblox, Studio, main, owner PC game checkout or credentials are modified.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent.parent
REGISTRY_PATH = HERE / "candidates.json"
REPO = "https://github.com/kk051780/toy-wars-factory.git"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
SHA64 = re.compile(r"[0-9a-f]{64}\Z")
PACKET = re.compile(r"P0D-[A-Z0-9_-]{6,120}\Z")
SUFFIXES = frozenset({".luau", ".lua", ".py", ".md", ".json", ".txt", ".csv", ".toml", ".yaml", ".yml"})
MAX_FILE = 2 * 1024 * 1024
MAX_PACKAGE = 10 * 1024 * 1024
MAX_FILES = 250


class Blocked(ValueError):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_path(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 240 or any(c in value for c in ("\\", ":", "\0")) or value.startswith("/"):
        raise Blocked("unsafe file path")
    parts = value.split("/")
    if any(not p or p in (".", "..") or p.startswith(".") for p in parts):
        raise Blocked("unsafe path component")
    if PurePosixPath(value).suffix.lower() not in SUFFIXES:
        raise Blocked("unexpected file extension")
    return value


def load_registry(path: Path = REGISTRY_PATH) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if (data.get("schema") != "P0D_KEYLESS_5_CLEANROOM_RECEIPT_V1"
            or data.get("game_id") != "TRAP_RAIDERS"
            or data.get("work_id") != "p0d-siege-v19"
            or data.get("source_kind") != "NEW_CLEANROOM_ALTERNATIVES_NOT_EXACT_LEGACY"):
        raise Blocked("invalid alternate registry contract")
    arr = data.get("candidates")
    if not isinstance(arr, list) or len(arr) != 5:
        raise Blocked("exactly five frozen alternatives required")
    if len({x.get("packet_id") for x in arr}) != 5 or len({x.get("legacy_old_packet_id") for x in arr}) != 5:
        raise Blocked("duplicate legacy or candidate IDs")
    for x in arr:
        if not PACKET.fullmatch(x.get("packet_id", "")) or not PACKET.fullmatch(x.get("legacy_old_packet_id", "")):
            raise Blocked("invalid packet id")
        if not SHA40.fullmatch(x.get("commit_sha", "")) or not SHA64.fullmatch(x.get("manifest_sha256", "")):
            raise Blocked("invalid pinned hash")
    return arr


def check_manifest(packet: str, raw: bytes) -> list[dict]:
    if len(raw) > MAX_FILE:
        raise Blocked("manifest too large")
    try:
        doc = json.loads(raw.decode("utf-8", errors="strict"))
    except (UnicodeError, ValueError) as exc:
        raise Blocked("manifest invalid UTF-8 JSON") from exc
    if (doc.get("format") != "P0D_PUBLIC_SOURCE_V1"
            or doc.get("game_id") != "TRAP_RAIDERS"
            or doc.get("work_id") != "p0d-siege-v19"
            or doc.get("packet_id") != packet
            or doc.get("public_source_allowed") is not True):
        raise Blocked("manifest authority mismatch")
    files = doc.get("files")
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        raise Blocked("invalid manifest files")
    seen = set()
    total = 0
    for item in files:
        if not isinstance(item, dict):
            raise Blocked("malformed manifest file entry")
        name = safe_path(item.get("path"))
        if name.casefold() in seen or name == "BUILD_MANIFEST.json":
            raise Blocked("duplicate or reserved path")
        seen.add(name.casefold())
        if type(item.get("size")) is not int or item["size"] < 0 or item["size"] > MAX_FILE:
            raise Blocked("bad manifest size")
        if not isinstance(item.get("sha256"), str) or not SHA64.fullmatch(item["sha256"]):
            raise Blocked("bad manifest digest")
        total += item["size"]
    if total > MAX_PACKAGE:
        raise Blocked("package too large")
    return files


def validate_bytes(entry: dict, files: dict[str, bytes]) -> dict:
    packet = entry["packet_id"]
    prefix = "handoffs/" + packet + "/"
    source = {p[len(prefix):]: data for p, data in files.items() if p.startswith(prefix)}
    if len(source) != len(files) or "BUILD_MANIFEST.json" not in source:
        raise Blocked("missing manifest or unrelated files")
    if sha256(source["BUILD_MANIFEST.json"]) != entry["manifest_sha256"]:
        raise Blocked("pinned manifest SHA mismatch")
    manifest = check_manifest(packet, source["BUILD_MANIFEST.json"])
    needed = {"BUILD_MANIFEST.json"} | {x["path"] for x in manifest}
    if set(source) != needed:
        raise Blocked("missing or unexpected source files")
    results = []
    for item in manifest:
        raw = source[item["path"]]
        if len(raw) != item["size"] or sha256(raw) != item["sha256"]:
            raise Blocked("source SHA/size mismatch")
        results.append({"path": item["path"], "size": len(raw), "sha256": sha256(raw)})
    return {
        "legacy_original_id": entry["legacy_old_packet_id"],
        "packet_id": packet,
        "commit_sha": entry["commit_sha"],
        "manifest_sha256": entry["manifest_sha256"],
        "source_kind": "NEW_CLEANROOM_ALTERNATIVE_NOT_ORIGINAL",
        "original_source_migrated": False,
        "studio_qa": "NOT_TESTED",
        "files_verified": len(results),
        "files": results,
    }


def run_git(*args: str) -> bytes:
    p = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       env={**os.environ, "GIT_TERMINAL_PROMPT": "0", "GIT_CONFIG_NOSYSTEM": "1"}, check=False)
    if p.returncode:
        raise Blocked("git failed (network, path or commit unavailable): " + " ".join(args[:3]))
    return p.stdout


def remote_files(gitdir: Path, entry: dict) -> dict[str, bytes]:
    sha = entry["commit_sha"]
    packet = entry["packet_id"]
    prefix = "handoffs/" + packet + "/"
    run_git("--git-dir", str(gitdir), "fetch", "--no-tags", "--depth=1", REPO, sha)
    fetched = run_git("--git-dir", str(gitdir), "rev-parse", "FETCH_HEAD").decode("ascii").strip()
    if fetched != sha:
        raise Blocked("fetched commit differs from pinned SHA")
    raw = run_git("--git-dir", str(gitdir), "ls-tree", "-r", "-z", "--full-tree", sha, prefix)
    files = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            spec, path_bytes = record.split(b"\t", 1)
            mode, kind, _ = spec.decode("ascii").split(" ", 2)
            path = path_bytes.decode("utf-8", errors="strict")
        except (UnicodeError, ValueError) as exc:
            raise Blocked("bad Git tree record") from exc
        if mode not in ("100644", "100755") or kind != "blob" or not path.startswith(prefix):
            raise Blocked("untrusted Git object (including symlink/submodule)")
        safe_path(path[len(prefix):])
        if path in files:
            raise Blocked("duplicate Git source path")
        files[path] = run_git("--git-dir", str(gitdir), "show", sha + ":" + path)
    return files


def _readonly_cleanup(onerror_func, filename, exc_info):
    """Windows Git pack files may be read-only; clear flag ONLY under our temp root."""
    try:
        os.chmod(filename, stat.S_IWRITE | stat.S_IREAD)
        onerror_func(filename)
    except OSError:
        raise


@contextmanager
def private_temp(parent: Path):
    root = Path(tempfile.mkdtemp(prefix="p0d-five-candidates-", dir=parent))
    try:
        yield root
    finally:
        shutil.rmtree(root, onerror=_readonly_cleanup)


def receive(dest: Path, entries: list[dict]) -> dict:
    if not entries or dest.exists() or dest.is_symlink():
        raise Blocked("empty selection or destination exists; refuse overwrite")
    parent = dest.parent.resolve()
    if not parent.is_dir():
        raise Blocked("destination parent must already exist")
    with private_temp(parent) as temp:
        bare = temp / "repo.git"
        run_git("init", "--bare", "-q", str(bare))
        staging = temp / "staging"
        staging.mkdir()
        reports = []
        for entry in entries:
            source = remote_files(bare, entry)
            receipt = validate_bytes(entry, source)
            reports.append(receipt)
            base = staging / "packs" / entry["packet_id"]
            for source_path, payload in source.items():
                suffix = source_path[len("handoffs/" + entry["packet_id"] + "/"):]
                output = base.joinpath(*PurePosixPath(suffix).parts)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(payload)
        receipt = {
            "status": "KEYLESS_FIVE_ALTERNATE_SOURCE_RECEIPT_ONLY",
            "candidate_packets_verified": len(reports),
            "source_kind": "CLEANROOM_NOT_ORIGINAL",
            "original_legacy_packets_migrated_by_this_tool": 0,
            "windows_game_integration": "NOT_TESTED",
            "roblox_studio_qa": "NOT_TESTED",
            "cannot_auto_install": True,
            "results": reports,
        }
        (staging / "RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        # Single atomic rename within same volume; no success receipt in partial path.
        if dest.exists() or dest.is_symlink():
            raise Blocked("destination appeared during verification")
        staging.rename(dest)
        return receipt


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="new nonexistent directory, outside game checkout")
    parser.add_argument("--packet", action="append", default=[], help="select one or more candidate packet IDs")
    args = parser.parse_args(argv)
    try:
        entries = load_registry()
        if args.packet:
            selected = set(args.packet)
            if len(selected) != len(args.packet) or not selected.issubset({e["packet_id"] for e in entries}):
                raise Blocked("duplicate or unknown --packet selection")
            entries = [e for e in entries if e["packet_id"] in selected]
        result = receive(args.output, entries)
        print(json.dumps({"status": result["status"], "packets": result["candidate_packets_verified"],
                          "output": str(args.output), "original_migrations": 0}, indent=2))
        return 0
    except (Blocked, OSError, ValueError, subprocess.SubprocessError) as exc:
        print("BLOCKED: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
