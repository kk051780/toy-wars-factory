"""Strict plain public-source SHA256+byte-size verification. Fail closed on extra or tampered files."""
from pathlib import Path
import hashlib, json, os, sys

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "BUILD_MANIFEST.json"
EXPECTED_KEYS = {"files", "format", "game_id", "packet_id",
                 "public_source_allowed", "work_id"}

def verify(root=ROOT, manifest=None):
    m = json.loads((root / "BUILD_MANIFEST.json").read_text(encoding="utf-8")) if manifest is None else manifest
    if set(m) != EXPECTED_KEYS:
        raise ValueError("bad root keys")
    if m["format"] != "P0D_PUBLIC_SOURCE_V1" or m["game_id"] != "TRAP_RAIDERS":
        raise ValueError("wrong format or game")
    if m["work_id"] != "p0d-siege-v19" or m["public_source_allowed"] is not True:
        raise ValueError("wrong authority")
    if m["packet_id"] != "P0D-WF13-LOCAL-GRAVITY-PROTOTYPE-20261112-01":
        raise ValueError("wrong isolated pack")
    if not isinstance(m["files"], list) or not m["files"]:
        raise ValueError("no listed files")
    declared = set()
    for f in m["files"]:
        if set(f) != {"path", "size", "sha256"}:
            raise ValueError("bad file keys")
        path = f["path"]
        if not isinstance(path, str) or path.startswith("/") or "\\" in path:
            raise ValueError("absolute/backslash path forbidden")
        if any(x in ("", ".", "..") for x in path.split("/")):
            raise ValueError("path traversal")
        if path in declared or path == "BUILD_MANIFEST.json":
            raise ValueError("duplicate/manifest self-reference")
        declared.add(path)
        fp = root / path
        if fp.is_symlink() or not fp.is_file() or not fp.resolve().is_relative_to(root.resolve()):
            raise ValueError("missing/symlink/path escape")
        raw = fp.read_bytes()
        if f["size"] != len(raw) or hashlib.sha256(raw).hexdigest() != f["sha256"]:
            raise ValueError("SHA256 or size mismatch: " + path)
    actual = {p.relative_to(root).as_posix() for p in root.rglob("*")
              if p.is_file() and p.name != "BUILD_MANIFEST.json"}
    if declared != actual:
        raise ValueError("hidden/unlisted or missing files")
    return len(declared)

if __name__ == "__main__":
    try:
        print("WF13_PUBLIC_SOURCE_MANIFEST_PASS files=", verify())
    except Exception as e:
        print("WF13_PUBLIC_SOURCE_MANIFEST_FAIL", e, file=sys.stderr)
        raise
