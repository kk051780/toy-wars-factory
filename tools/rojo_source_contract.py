#!/usr/bin/env python3
"""Read-only accepted-source pin and manual-main checkout guard for Rojo builds.

These checks are NOT a GitHub-hosted actor attestation or Studio runtime test.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ACCEPTED_MAIN = "e5deff4d5681bca4823a3da0f848e01bc089ae6e"
REPO = "kk051780/toy-wars-factory"
PINS = {
    "src/ToyWarsBalance.lua": "e78a07c7551f19183316803706c5602cd4049459",
    "src/ToyWarsServer.server.lua": "d86a0b89a1d811ec6da83da93b24e29235218b04",
    "src/ToyWarsSmokeTest.server.lua": "ccba431909c664909e2680785648d0402fedf3c3",
    "src/ToyWarsHUD.client.lua": "f1b7a2e2e4e6cd0a5703a7f034f50d4e62801467",
}
EXPECTED_PROJECT = {
    "name": "ToyWarsFactory",
    "tree": {
        "$className": "DataModel",
        "Workspace": {"$className": "Workspace"},
        "ReplicatedStorage": {"$className": "ReplicatedStorage",
            "ToyWarsBalance": {"$path": "src/ToyWarsBalance.lua"},
            "ToyWarsSelectUnit": {"$className": "RemoteEvent"}},
        "ServerScriptService": {"$className": "ServerScriptService",
            "ToyWarsServer": {"$path": "src/ToyWarsServer.server.lua"},
            "ToyWarsSmokeTest": {"$path": "src/ToyWarsSmokeTest.server.lua"}},
        "StarterPlayer": {"$className": "StarterPlayer",
            "StarterPlayerScripts": {"$className": "StarterPlayerScripts",
                "ToyWarsHUD": {"$path": "src/ToyWarsHUD.client.lua"}}},
    },
}
_SHA = re.compile(r"[0-9a-f]{40}\Z")


def git_blob_sha(content: bytes) -> str:
    if type(content) is not bytes:
        raise ValueError("invalid byte content")
    return hashlib.sha1(b"blob " + str(len(content)).encode("ascii") + b"\0" + content).hexdigest()


def _strict_pairs(pairs):
    result = {}
    for name, value in pairs:
        if name in result:
            raise ValueError("duplicate project JSON key")
        result[name] = value
    return result


def validate_project(root: Path):
    path = Path(root) / "default.project.json"
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 32_768:
        raise ValueError("missing or unsafe project")
    try:
        actual = json.loads(path.read_text(encoding="utf8"), object_pairs_hook=_strict_pairs)
    except (UnicodeError, ValueError, OSError) as ex:
        raise ValueError("invalid project JSON") from ex
    if actual != EXPECTED_PROJECT:
        raise ValueError("unreviewed Roblox project mapping")
    return actual


def check_sources(root: Path, pins: dict[str, str] = PINS):
    root = Path(root)
    if type(pins) is not dict or set(pins) != set(PINS) or any(
        type(s) is not str or not _SHA.fullmatch(s) for s in pins.values()
    ):
        raise ValueError("invalid pinned source set")
    for relative, expected in pins.items():
        path = root / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError("missing or symlinked source")
        raw = path.read_bytes()
        if not 0 < len(raw) <= 100_000 or git_blob_sha(raw) != expected:
            raise ValueError("source mismatch against expected Git blob")
        try:
            raw.decode("utf8")
        except UnicodeError as ex:
            raise ValueError("source encoding mismatch") from ex
    return pins


def check_event(env: dict[str, str]):
    if (env.get("GITHUB_REPOSITORY") != REPO or
        env.get("GITHUB_EVENT_NAME") != "workflow_dispatch" or
        env.get("GITHUB_REF") != "refs/heads/main"):
        raise ValueError("not manual default-branch event")
    sha = env.get("GITHUB_SHA")
    if type(sha) is not str or not _SHA.fullmatch(sha):
        raise ValueError("bad checkout provenance")
    return sha


def check_checkout(root: Path, env: dict[str, str], baseline: str = ACCEPTED_MAIN,
                   pins: dict[str, str] = PINS):
    root = Path(root).resolve()
    head = check_event(env)
    if type(baseline) is not str or not _SHA.fullmatch(baseline):
        raise ValueError("invalid baseline")
    def git(*args):
        try:
            return subprocess.run(["git", "-C", str(root), *args],
                                  check=True, capture_output=True, text=True, timeout=10)
        except (subprocess.CalledProcessError, OSError, subprocess.TimeoutExpired) as ex:
            raise ValueError("Git source ancestry unavailable") from ex
    if git("rev-parse", "HEAD").stdout.strip() != head:
        raise ValueError("checkout HEAD differs from event SHA")
    git("merge-base", "--is-ancestor", baseline, head)
    validate_project(root)
    check_sources(root, pins)
    return head


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", default=".")
    args = parser.parse_args()
    head = check_checkout(Path(args.checkout), dict(os.environ))
    print(json.dumps({"accepted_source_main": ACCEPTED_MAIN, "build_head": head,
                      "sources": PINS, "actor_attested": False,
                      "engine_verified": False, "published": False}, sort_keys=True))

if __name__ == "__main__":
    main()
