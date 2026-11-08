"""Offline, read-only structural verifier for one downloaded Actions handoff ZIP.

The caller MUST independently authenticate GitHub run/head/job/artifact identity,
the current main revision and source_revision ancestry/status-only compare.
This program does NOT access GitHub, grant permission or authenticate an archive.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
import zipfile

REPOSITORY = "kk051780/toy-wars-factory"
TWO = ("CHAT_HANDOFF.md", "LATEST_STATE.json")
MANIFEST = "HANDOFF_SHA256SUMS.txt"
MAX_MEMBER = 500_000
MAX_TOTAL = 1_000_000
MAX_ZIP = 1_000_000
HEX40 = re.compile(r"[0-9a-f]{40}\Z")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def reject_nonfinite_constant(value):
    raise ValueError("non-finite JSON constant: " + value)


def verify_archive(path):
    """Verify archive structure, fields and same-archive checksums only.

    Result means ARCHIVE_STRUCTURE_VALID_ONLY; not permission, provenance,
    freshness or a safe-to-merge / safe-to-publish verdict.
    """
    path = Path(path)
    if not path.is_file() or path.stat().st_size > MAX_ZIP:
        raise ValueError("missing or oversized ZIP")
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            names = [member.filename for member in infos]
            present = set(names)
            allowed = set(TWO)
            if len(names) not in (2, 3) or len(present) != len(names):
                raise ValueError("unexpected/duplicate ZIP members")
            if present not in (allowed, allowed | {MANIFEST}):
                raise ValueError("unexpected ZIP paths")
            if sum(member.file_size for member in infos) > MAX_TOTAL:
                raise ValueError("oversized uncompressed ZIP")
            data = {}
            for member in infos:
                mode = member.external_attr >> 16
                if (member.is_dir() or member.file_size >= MAX_MEMBER or
                        member.compress_size > MAX_ZIP or member.flag_bits & 1 or
                        member.compress_type not in (zipfile.ZIP_STORED,
                                                    zipfile.ZIP_DEFLATED) or
                        (member.create_system == 3 and
                         (stat.S_IFMT(mode) not in (0, stat.S_IFREG) or
                          mode & 0o111)):
                    raise ValueError("unsafe ZIP member")
                # Bound decompression even if ZIP metadata is dishonest.
                with archive.open(member) as stream:
                    payload = stream.read(MAX_MEMBER)
                    if len(payload) != member.file_size or stream.read(1):
                        raise ValueError("ZIP size mismatch")
                data[member.filename] = payload
    except (zipfile.BadZipFile, RuntimeError, OSError, EOFError) as exc:
        raise ValueError("invalid ZIP") from exc

    if not data[TWO[0]]:
        raise ValueError("empty handoff")
    try:
        data[TWO[0]].decode("utf-8")
        state = json.loads(data[TWO[1]].decode("utf-8"),
                           object_pairs_hook=unique_object,
                           parse_constant=reject_nonfinite_constant)
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid text/JSON") from exc
    if (type(state) is not dict or type(state.get("schema")) is not int or
            state["schema"] != 2 or
            state.get("canonical_repo") != REPOSITORY or
            state.get("release_decision") != "HOLD_ENGINE_UNVERIFIED" or
            type(state.get("source_revision")) is not str or
            not HEX40.fullmatch(state["source_revision"])):
        raise ValueError("invalid HOLD/repository/source fields")

    if MANIFEST in data:
        expected = "".join(
            hashlib.sha256(data[name]).hexdigest() + "  " + name + "\n"
            for name in TWO)
        if data[MANIFEST] != expected.encode("ascii"):
            raise ValueError("invalid checksum manifest")
        integrity = "same_zip_sha256_manifest_not_provenance"
    else:
        integrity = "legacy_zip_crc_only_no_sha256_manifest"
    return {
        "status": "ARCHIVE_STRUCTURE_VALID_ONLY",
        "repository": REPOSITORY,
        "source_revision": state["source_revision"],
        "integrity": integrity,
        "files": list(TWO),
        "provider_authenticated": False,
        "main_ancestry_verified": False,
        "authorizes_write": False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("zip_path", help="downloaded GitHub Actions artifact ZIP")
    args = parser.parse_args(argv)
    try:
        outcome = verify_archive(args.zip_path)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "UNTRUSTED_STALE",
                          "reason": str(exc), "authorizes_write": False},
                         sort_keys=True))
        return 2
    print(json.dumps(outcome, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
