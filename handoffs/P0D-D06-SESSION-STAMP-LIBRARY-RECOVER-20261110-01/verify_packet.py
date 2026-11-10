#!/usr/bin/env python3
"""Read-only verifier for an extracted v39 handoff or a ZIP pack."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile


def sha(b): return hashlib.sha256(b).hexdigest()


def verify_zip(path):
    errors = []
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            errors.append("DUPLICATE_ZIP_PATH")
        if any(n.startswith(("/", "\\")) or ".." in n.replace("\\", "/").split("/") or ":" in n or "\\" in n for n in names):
            errors.append("UNSAFE_ZIP_PATH")
        if errors: return {"ok": False, "errors": errors}
        manifest = json.loads(z.read("BUILD_MANIFEST.json"))
        expected = {e["path"] for e in manifest["files"]} | {"BUILD_MANIFEST.json"}
        if set(names) != expected:
            errors.append("FILE_SET_MISMATCH")
        for item in manifest["files"]:
            path = item["path"]
            if path not in names:
                errors.append(f"MISSING:{path}")
            else:
                data = z.read(path)
                if sha(data) != item["sha256"] or len(data) != item["bytes"]:
                    errors.append(f"HASH_OR_SIZE_MISMATCH:{path}")
        if z.testzip() is not None: errors.append("ZIP_CRC_FAIL")
    return {"ok": not errors, "errors": errors, "files": len(manifest["files"]),
            "game_integrated": False, "studio_verified": False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("zip_path", type=Path)
    args = p.parse_args()
    try: result = verify_zip(args.zip_path)
    except Exception as exc: result = {"ok": False, "errors": [type(exc).__name__ + ":" + str(exc)]}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    sys.exit(0 if result["ok"] else 1)

if __name__ == "__main__": main()
