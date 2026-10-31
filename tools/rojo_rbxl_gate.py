#!/usr/bin/env python3
"""Bounded binary-framing check for a build-only Roblox .rbxl place candidate.

This does NOT decode, load, or execute Roblox content. No engine proof.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import struct

MAGIC = b"<roblox!\x89\xff\r\n\x1a\n"
MAX_BYTES = 10 * 1024 * 1024
END_PAYLOAD = b"</roblox>"
CHUNKS = {"META", "SSTR", "INST", "PROP", "PRNT", "END"}
HEADER_SIZE = len(MAGIC) + struct.calcsize("<HIIQ")
CHUNK_SIZE = struct.calcsize("<4sIII")


def inspect(data: bytes):
    if type(data) is not bytes or not HEADER_SIZE + CHUNK_SIZE <= len(data) <= MAX_BYTES:
        raise ValueError("invalid RBXL candidate size")
    if not data.startswith(MAGIC):
        raise ValueError("invalid Roblox binary magic")
    version, classes, instances, reserved = struct.unpack_from("<HIIQ", data, len(MAGIC))
    if version != 0 or not 1 <= classes <= 4096 or not 1 <= instances <= 100_000 or reserved:
        raise ValueError("invalid Roblox binary header")
    offset = HEADER_SIZE
    seen = []
    while offset < len(data):
        if len(data) - offset < CHUNK_SIZE:
            raise ValueError("truncated chunk header")
        kind_raw, compressed, uncompressed, reserved = struct.unpack_from("<4sIII", data, offset)
        offset += CHUNK_SIZE
        try:
            kind = kind_raw.rstrip(b"\0").decode("ascii")
        except UnicodeDecodeError as ex:
            raise ValueError("non ASCII chunk") from ex
        if kind not in CHUNKS or reserved or len(seen) > 100_000:
            raise ValueError("invalid chunk type or flags")
        length = compressed if compressed else uncompressed
        if length > MAX_BYTES or offset + length > len(data):
            raise ValueError("invalid chunk bounds")
        if kind == "END":
            if (compressed != 0 or uncompressed != len(END_PAYLOAD) or
                    data[offset:offset + length] != END_PAYLOAD):
                raise ValueError("invalid Roblox binary END sentinel")
        offset += length
        if "END" in seen:
            raise ValueError("duplicate/trailing END chunk")
        seen.append(kind)
        if kind == "END":
            break
    if (offset != len(data) or not seen or seen[-1] != "END" or
            not {"INST", "PROP", "PRNT"} <= set(seen) or
            seen.count("PRNT") != 1 or seen.count("META") > 1 or
            seen.count("SSTR") > 1):
        raise ValueError("not a complete Roblox binary place frame")
    return {"format": "RBXL_BINARY_V0_FRAMING_ONLY", "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(), "chunk_types": seen,
            "engine_verified": False, "studio_open_verified": False,
            "published": False, "source_attested": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
    args = parser.parse_args()
    if args.path.is_symlink() or not args.path.is_file() or args.path.stat().st_size > MAX_BYTES:
        raise SystemExit("RBXL_FILE_DENIED")
    print(json.dumps(inspect(args.path.read_bytes()), indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
