#!/usr/bin/env python3
"""Restore the seven pinned historical GQ8 inputs without expiring downloads.

This is an offline transport boundary, not source or CI admission. The caller
must retain the original eight run/head/success checks, live RC fencing, and
every existing composer, source/class, rollback, Native and delivery check.
Five ZIPs are the original downloaded bytes. Two are explicitly documented
recipe reconstructions, not purported downloads of the missing original ZIPs.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import zipfile

HERE = Path(__file__).resolve().parent
LOCK_SHA256 = "abc088ed1a9addf17e98c0b874f5f9d4badf8b11287769ad07b868f15b43dc18"
PACKETS = ("base55", "hud59", "trade62", "formal62", "formal63", "viral56", "counter56")
RECONSTRUCTED = {"hud59", "counter56"}


def require(ok, reason):
    if not ok:
        raise ValueError("RED_ORIGINAL_INPUTS_" + reason)


def identity(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def strict_json(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            require(key not in result, "DUPLICATE_JSON_KEY")
            result[key] = value
        return result
    return json.loads(raw.decode("utf-8"), object_pairs_hook=unique)


def no_links(path):
    path = Path(os.path.abspath(path))
    require(all(not p.is_symlink() for p in (path, *path.parents)), "SYMLINK_PATH")
    return path


def read_regular(path):
    path = no_links(path)
    mode = path.lstat().st_mode
    require(stat.S_ISREG(mode) and not mode & 0o7000, "NON_REGULAR_FILE")
    return path.read_bytes()


def relative(name):
    require(isinstance(name, str) and name and "\\" not in name and ":" not in name
            and "\0" not in name, "UNSAFE_MEMBER_NAME")
    path = PurePosixPath(name)
    require(bool(path.parts) and not path.is_absolute() and path.as_posix() == name
            and all(part not in (".", "..", "") for part in path.parts), "UNSAFE_MEMBER_NAME")
    return path


def snapshot(inputs):
    require(inputs.is_dir(), "INPUT_DIRECTORY_MISSING")
    expected = {"LOCK.json"} | {name + ".zip" for name in PACKETS}
    require({p.name for p in inputs.iterdir()} == expected, "INPUT_FILE_SET")
    return {name: identity(read_regular(inputs / name)) for name in sorted(expected)}


def load_lock(inputs):
    raw = read_regular(inputs / "LOCK.json")
    require(identity(raw)["sha256"] == LOCK_SHA256, "LOCK_IDENTITY")
    lock = strict_json(raw)
    require(lock.get("schema") == "GQ8_ORIGINAL_INPUT_TRANSPORT_V1"
            and lock.get("transport_only") is True
            and lock.get("canonical_ci_or_rc_adoption_proven") is False
            and set(lock.get("packets", {})) == set(PACKETS), "LOCK_CONTRACT")
    for name, row in lock["packets"].items():
        require(row["archive"]["path"] == name + ".zip", "ARCHIVE_NAME")
        if name in RECONSTRUCTED:
            require(row["source_kind"] == "RECONSTRUCTED_FROM_ORIGINAL_RECIPE"
                    and row["historical_receipt_raw_byte_hash"] == "UNKNOWN"
                    and row["original_artifact_downloaded"] is False
                    and row["new_native_run_claimed"] is False
                    and row["reconstruction"]["ci_environment_fabricated"] is False,
                    "RECONSTRUCTION_PROVENANCE")
        else:
            require(row["source_kind"] == "DOWNLOADED_ORIGINAL_ARTIFACT"
                    and row["original_zip"] == {k: row["archive"][k] for k in ("bytes", "sha256")},
                    "ORIGINAL_ZIP_PROVENANCE")
    return lock


def decode_packet(raw, row):
    """Decode a locked packet; the public restore path first pins the lock."""
    require(identity(raw) == {k: row["archive"][k] for k in ("bytes", "sha256")}, "ARCHIVE_IDENTITY")
    payload = {}
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        require(len(names) == len(set(names)) == len({n.casefold() for n in names}), "DUPLICATE_MEMBER")
        require(set(names) == set(row["members"]) and len(names) == row["file_count"], "MEMBER_SET")
        require(sum(info.file_size for info in infos) == row["unpacked_bytes"], "UNPACKED_SIZE")
        for info in infos:
            path = relative(info.filename)
            require(not any(parent.as_posix() in names for parent in path.parents), "FILE_DIRECTORY_COLLISION")
            kind = stat.S_IFMT(info.external_attr >> 16)
            require(not info.is_dir() and kind in (0, stat.S_IFREG)
                    and not (info.external_attr >> 16) & 0o7000, "NON_REGULAR_MEMBER")
            require(not info.flag_bits & 1 and info.compress_type in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED),
                    "UNSUPPORTED_ARCHIVE_MEMBER")
            pin = row["members"][info.filename]
            require(type(pin["bytes"]) is int and pin["bytes"] >= 0 and info.file_size == pin["bytes"],
                    "MEMBER_SIZE")
            with archive.open(info) as stream:
                content = stream.read(pin["bytes"] + 1)
            require(identity(content) == pin, "MEMBER_IDENTITY")
            payload[info.filename] = content
    return payload


def inventory(root):
    result = {}
    for path in root.rglob("*"):
        require(not path.is_symlink(), "OUTPUT_SYMLINK")
        if path.is_dir():
            continue
        result[path.relative_to(root).as_posix()] = identity(read_regular(path))
    return result


def remove_owned(created_files, created_dirs):
    """Remove only this invocation's inodes; preserve intervening foreign work."""
    for path, owned, pin in reversed(created_files):
        try:
            no_links(path)
            current = path.lstat()
            if (current.st_dev, current.st_ino) == owned and identity(read_regular(path)) == pin:
                path.unlink()
        except (OSError, ValueError):
            pass
    for path, owned in reversed(created_dirs):
        try:
            no_links(path)
            current = path.lstat()
            if (current.st_dev, current.st_ino) == owned:
                path.rmdir()  # A nonempty directory, including foreign files, is retained.
        except (OSError, ValueError):
            pass


def restore(output, inputs=None):
    inputs = no_links(HERE / "immutable_inputs" if inputs is None else inputs)
    output = no_links(output)
    require(not output.exists() and output.parent.is_dir(), "OUTPUT_MUST_BE_NEW")
    require(not output.is_relative_to(inputs) and not inputs.is_relative_to(output), "DIRECTORY_OVERLAP")
    source_before = read_regular(Path(__file__))
    before = snapshot(inputs)
    lock = load_lock(inputs)
    payload = {}
    for name in PACKETS:
        row = lock["packets"][name]
        packet = decode_packet(read_regular(inputs / row["archive"]["path"]), row)
        payload.update({name + "/" + path: raw for path, raw in packet.items()})
    expected = {path: identity(raw) for path, raw in payload.items()}
    require(len(expected) == 316, "TOTAL_MEMBER_COUNT")
    require(snapshot(inputs) == before, "INPUTS_CHANGED_DURING_DECODE")
    created_files, created_dirs = [], []
    try:
        output.mkdir(mode=0o755, exist_ok=False)
        st = output.lstat()
        created_dirs.append((output, (st.st_dev, st.st_ino)))
        for name, raw in sorted(payload.items()):
            parts = relative(name).parts
            parent = output
            for component in parts[:-1]:
                parent = no_links(parent / component)
                if not parent.exists():
                    parent.mkdir(mode=0o755)
                    st = parent.lstat()
                    created_dirs.append((parent, (st.st_dev, st.st_ino)))
                require(parent.is_dir(), "OUTPUT_PARENT_NOT_DIRECTORY")
            path = parent / parts[-1]
            with path.open("xb") as stream:
                stream.write(raw)
            st = path.lstat()
            created_files.append((path, (st.st_dev, st.st_ino), expected[name]))
        require(inventory(output) == expected, "RESTORED_PAYLOAD_DRIFT")
        require(snapshot(inputs) == before and read_regular(Path(__file__)) == source_before,
                "INPUTS_OR_RESTORER_CHANGED")
        return {"schema": "GQ8_ORIGINAL_INPUT_RESTORE_V1", "status": "PASS_IMMUTABLE_TRANSPORT_ONLY",
                "lock": before["LOCK.json"], "packet_count": len(PACKETS), "file_count": len(expected),
                "original_zip_packets": 5, "reconstructed_recipe_packets": 2,
                "packet_origins": {name: lock["packets"][name]["source_kind"] for name in PACKETS},
                "source_inputs_unchanged": True, "canonical_ci_or_rc_adoption_proven": False,
                "native_or_studio_pass_claimed": False}
    except Exception:
        remove_owned(created_files, created_dirs)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="New directory; its parent must already exist")
    parser.add_argument("--inputs", type=Path, help="Relocated identical immutable_inputs directory; pins remain mandatory")
    args = parser.parse_args()
    try:
        result = restore(args.out, args.inputs)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(json.dumps({"status": "FAIL_NO_INPUT_ADMISSION", "reason": str(error)}, sort_keys=True))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
