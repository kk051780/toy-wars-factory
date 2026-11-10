#!/usr/bin/env python3
"""Isolated fixed-commit source intake for TRAP RAIDERS PUBLIC_SOURCE_V1.

No secret keys. Never changes existing game checkout, main, or Studio.
Only verifies and stages original-source references; NOT an integration/QA PASS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parents[1]
REGISTRY = HERE / "packets.json"
URL = "https://github.com/kk051780/toy-wars-factory.git"
COMMIT = re.compile(r"[a-f0-9]{40}\Z")
PACKET = re.compile(r"P0D-[A-Z0-9_-]{4,120}\Z")
HASH = re.compile(r"[a-f0-9]{64}\Z")
ALLOWED_SUFFIX = {".luau", ".lua", ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".csv"}
MAX_FILES = 250
MAX_FILE_BYTES = 4 * 1024 * 1024
MAX_PACKAGE_BYTES = 20 * 1024 * 1024


class IntakeError(ValueError):
    pass


def digest(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def path_check(text: str) -> str:
    if not isinstance(text, str) or not text or len(text) > 250 or "\\" in text or ":" in text or "\0" in text or text.startswith("/"):
        raise IntakeError("unsafe source path")
    p = PurePosixPath(text)
    parts = p.parts
    if not parts or any(part in ("", ".", "..") or part.startswith(".") for part in parts) or p.as_posix() != text:
        raise IntakeError("unsafe or noncanonical source path")
    if p.suffix.lower() not in ALLOWED_SUFFIX:
        raise IntakeError("unsupported source file type")
    return text


def registry() -> dict:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("schema") != "P0D_PUBLIC_SOURCE_INTAKE_21_V1" or data.get("game_id") != "TRAP_RAIDERS":
        raise IntakeError("wrong registry schema")
    packets = data.get("packages", [])
    if len(packets) != 21 or len({p.get("packet") for p in packets}) != 21:
        raise IntakeError("registry must contain 21 distinct source packages")
    for p in packets:
        if not PACKET.fullmatch(p.get("packet", "")) or not COMMIT.fullmatch(p.get("commit", "")):
            raise IntakeError("invalid immutable packet/commit registry")
    return data


def check_manifest(content: bytes, packet: str) -> list[dict]:
    if len(content) > MAX_FILE_BYTES:
        raise IntakeError("oversized manifest")
    try:
        m = json.loads(content.decode("utf-8", errors="strict"))
    except (UnicodeError, ValueError) as exc:
        raise IntakeError("invalid UTF-8 JSON manifest") from exc
    if (m.get("format") != "P0D_PUBLIC_SOURCE_V1" or m.get("game_id") != "TRAP_RAIDERS"
        or m.get("work_id") != "p0d-siege-v19" or m.get("packet_id") != packet
        or m.get("public_source_allowed") is not True):
        raise IntakeError("manifest game/packet/format mismatch")
    files = m.get("files")
    if not isinstance(files, list) or not 1 <= len(files) <= MAX_FILES:
        raise IntakeError("manifest missing/too many files")
    seen = set()
    for f in files:
        if not isinstance(f, dict):
            raise IntakeError("invalid file entry")
        name = path_check(f.get("path"))
        if name.casefold() in seen or name == "BUILD_MANIFEST.json":
            raise IntakeError("case collision or root manifest conflict")
        seen.add(name.casefold())
        if type(f.get("size")) is not int or not 0 <= f["size"] <= MAX_FILE_BYTES:
            raise IntakeError("bad size")
        if not isinstance(f.get("sha256"), str) or not HASH.fullmatch(f["sha256"]):
            raise IntakeError("bad file SHA256")
    if sum(f["size"] for f in files) > MAX_PACKAGE_BYTES:
        raise IntakeError("excess package size")
    return files


def validate_source(packet: str, source_files: dict[str, bytes]) -> dict:
    """Pure function useful for unit testing; source_files keys are repo-root paths."""
    if not PACKET.fullmatch(packet):
        raise IntakeError("bad packet name")
    prefix = f"handoffs/{packet}/"
    root = {key[len(prefix):]: payload for key, payload in source_files.items() if key.startswith(prefix)}
    if not root or "BUILD_MANIFEST.json" not in root:
        raise IntakeError("missing manifest at immutable commit")
    files = check_manifest(root["BUILD_MANIFEST.json"], packet)
    wanted = {f["path"] for f in files} | {"BUILD_MANIFEST.json"}
    if set(root) != wanted:
        raise IntakeError("missing or extra package path")
    result = []
    for f in files:
        b = root[f["path"]]
        if len(b) != f["size"] or digest(b) != f["sha256"]:
            raise IntakeError("size or SHA mismatch: " + f["path"])
        result.append({"path": f["path"], "size": len(b), "sha256": digest(b)})
    return {"packet_id": packet, "state": "PUBLIC_SOURCE_BYTES_VERIFIED_LOCAL_ONLY",
            "manifest_sha256": digest(root["BUILD_MANIFEST.json"]),
            "files_verified": len(files), "source_files": result}


def git_command(*args: str) -> bytes:
    process = subprocess.run(["git", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             env={**os.environ, "GIT_TERMINAL_PROMPT": "0"}, check=False)
    if process.returncode:
        raise IntakeError("git operation failed: " + " ".join(args[:3]) + " (check Git/network access)")
    return process.stdout


def fetch_repo(repo: Path, sha: str) -> None:
    git_command("--git-dir", str(repo), "fetch", "--no-tags", "--depth=1", URL, sha)
    if git_command("--git-dir", str(repo), "rev-parse", "FETCH_HEAD").decode().strip() != sha:
        raise IntakeError("git FETCH_HEAD commit differs from expected")


def read_from_git(repo: Path, packet: str, sha: str) -> dict[str, bytes]:
    prefix = f"handoffs/{packet}/"
    raw = git_command("--git-dir", str(repo), "ls-tree", "-r", "-z", "--full-tree", sha, prefix)
    files: dict[str, bytes] = {}
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            spec, name_bytes = record.split(b"\t", 1)
            mode, kind, _obj = spec.decode("ascii").split(" ", 2)
            filename = name_bytes.decode("utf-8", errors="strict")
        except (ValueError, UnicodeError) as exc:
            raise IntakeError("invalid Git tree record") from exc
        if kind != "blob" or mode not in ("100644", "100755") or not filename.startswith(prefix):
            raise IntakeError("unsafe Git tree entry")
        leaf = filename[len(prefix):]
        path_check(leaf)
        files[filename] = git_command("--git-dir", str(repo), "show", f"{sha}:{filename}")
    return files


def stage(output: Path, selected: list[dict]) -> dict:
    if output.exists() or output.is_symlink():
        raise IntakeError("output already exists; refuse overwrite")
    parent = output.parent.resolve()
    if not parent.is_dir():
        raise IntakeError("output parent must already exist")
    with tempfile.TemporaryDirectory(prefix="p0d-keyless-", dir=str(parent)) as tmp:
        temp = Path(tmp)
        bare = temp / "fetched.git"
        git_command("init", "--bare", "-q", str(bare))
        receipts = []
        for i, item in enumerate(selected, 1):
            commit, packet = item["commit"], item["packet"]
            fetch_repo(bare, commit)
            sources = read_from_git(bare, packet, commit)
            proof = validate_source(packet, sources)
            proof["commit_sha"] = commit
            pack_dir = temp / "packs" / packet
            for path, payload in sources.items():
                leaf = path[len(f"handoffs/{packet}/"):]
                target = pack_dir.joinpath(*PurePosixPath(leaf).parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(payload)
            receipts.append(proof)
        shutil.rmtree(bare)
        receipt = {"state": "KEYLESS_DELIVERY_BYTES_VERIFIED_NOT_PC_GAME_INTEGRATED",
                   "source": URL, "packets": len(receipts), "results": receipts,
                   "requires": "Owner PC latest source checkpoint, owner approval, separate Studio/2client/mobile/exit QA"}
        (temp / "RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise IntakeError("output target appeared during verification")
        # Atomically claim a fresh output path: never replace an existing folder,
        # even if another process creates one after our initial check.
        output.mkdir(mode=0o700, exist_ok=False)
        try:
            shutil.move(str(temp / "packs"), str(output / "packs"))
            # RECEIPT.json is installed last; incomplete output never has a PASS receipt.
            os.replace(str(temp / "RECEIPT.json"), str(output / "RECEIPT.json"))
        except Exception:
            # Incomplete output is deliberately left for diagnosis; never overwrite it.
            raise IntakeError("destination staging interrupted; incomplete output exists, do not reuse it")
        return receipt


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output", type=Path, required=True, help="NEW empty destination outside current game")
    p.add_argument("--packet", action="append", default=[], help="select package name; omit for all 21")
    args = p.parse_args(argv)
    try:
        reg = registry()
        packages = reg["packages"]
        if args.packet:
            selected = set(args.packet)
            if len(selected) != len(args.packet) or not selected.issubset({x["packet"] for x in packages}):
                raise IntakeError("repeated/unknown --packet selection")
            packages = [x for x in packages if x["packet"] in selected]
        receipt = stage(args.output, packages)
        print(json.dumps({"state": receipt["state"], "packets": receipt["packets"], "path": str(args.output)}, indent=2))
        return 0
    except (IntakeError, OSError) as err:
        print("BLOCKED: " + str(err), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
