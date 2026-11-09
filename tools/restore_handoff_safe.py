#!/usr/bin/env python3
"""Fail-closed v39/v43A P0-D AES-GCM handoff restore (generic, no game sources).

Usage: CHAT_CODEX_HANDOFF_KEY is supplied privately; never pass it on command line.
No git/Studio/Roblox/network calls, no automatic ZIP extraction, no overwrites.
Do NOT use outputs as trusted executable code without independent source review.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import zipfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

FORMAT = "P0D_AES256_GCM_HANDOFF_V1"
MAX_ENVELOPE = 15_000_000
MAX_CIPHERTEXT = 12_000_000
MAX_ZIP = 10_000_000
MAX_FILES = 512
_ID = re.compile(r"[A-Za-z0-9_.-]{1,96}\Z")
_SHA = re.compile(r"[0-9a-f]{64}\Z")


class HandoffError(ValueError):
    """Safe (nonsecret) verification error."""


def _pair_no_duplicates(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise HandoffError("DUPLICATE_JSON_FIELD")
        data[key] = value
    return data


def _read_envelope(path: Path) -> dict:
    if path.is_symlink():
        raise HandoffError("INPUT_SYMLINK_REJECTED")
    with path.open("rb") as file:
        if not stat.S_ISREG(os.fstat(file.fileno()).st_mode):
            raise HandoffError("INPUT_NOT_REGULAR")
        raw = file.read(MAX_ENVELOPE + 1)
        if len(raw) > MAX_ENVELOPE:
            raise HandoffError("ENVELOPE_TOO_LARGE")
    try:
        doc = json.loads(raw.decode("utf-8"), object_pairs_hook=_pair_no_duplicates)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise HandoffError("INVALID_JSON") from exc
    if not isinstance(doc, dict):
        raise HandoffError("INVALID_ENVELOPE")
    return doc


def _b64(value, max_encoded: int) -> bytes:
    if isinstance(value, list):
        if not value or any(not isinstance(x, str) for x in value):
            raise HandoffError("INVALID_B64_TYPE")
        value = "".join(value)
    if not isinstance(value, str) or len(value) > max_encoded:
        raise HandoffError("INVALID_B64_SIZE")
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HandoffError("INVALID_B64") from exc


def _decode_key(value: str) -> bytes:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{43}=?", value.strip()):
        raise HandoffError("INVALID_KEY")
    key_text = value.strip().rstrip("=")
    try:
        key = base64.b64decode(key_text + "=", altchars=b"-_", validate=True)
    except (binascii.Error, ValueError) as exc:
        raise HandoffError("INVALID_KEY") from exc
    if len(key) != 32:
        raise HandoffError("INVALID_KEY")
    return key


def _verify_zip(blob: bytes) -> None:
    if not blob or len(blob) > MAX_ZIP:
        raise HandoffError("ZIP_SIZE_REJECTED")
    try:
        with zipfile.ZipFile(io.BytesIO(blob)) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_FILES:
                raise HandoffError("ZIP_ENTRY_COUNT_REJECTED")
            names = set()
            total = 0
            for info in infos:
                name = info.filename
                if (not isinstance(name, str) or not name or name.startswith(("/", "\\"))
                        or "\\" in name or ":" in name or info.is_dir()
                        or any(part in ("", ".", "..") for part in name.split("/"))):
                    raise HandoffError("ZIP_UNSAFE_PATH")
                # Casefold guards against collisions on common Windows filesystems.
                folded = name.casefold()
                if folded in names:
                    raise HandoffError("ZIP_COLLISION")
                names.add(folded)
                if info.flag_bits & 1:
                    raise HandoffError("ZIP_ENCRYPTED_ENTRY")
                mode = (info.external_attr >> 16) & 0xFFFF
                if mode and stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                    raise HandoffError("ZIP_SPECIAL_FILE")
                total += info.file_size
                if total > MAX_ZIP:
                    raise HandoffError("ZIP_EXPANSION_LIMIT")
            if archive.testzip() is not None:
                raise HandoffError("ZIP_BAD_CRC")
    except (zipfile.BadZipFile, RuntimeError, OSError, EOFError) as exc:
        raise HandoffError("ZIP_CORRUPT") from exc


def decode_and_verify(envelope: dict, secret: str, *, expected_zip_sha256: str,
                      expected_work_id: str, expected_game_id: str = "TRAP_RAIDERS",
                      expected_packet_id: str | None = None) -> bytes:
    """Verify identities + authenticated envelope and ZIP, but NEVER write/extract."""
    if envelope.get("format") != FORMAT:
        raise HandoffError("WRONG_FORMAT")
    for field, expected in (("game_id", expected_game_id), ("work_id", expected_work_id)):
        if envelope.get(field) != expected:
            raise HandoffError("IDENTITY_MISMATCH")
    if expected_packet_id is not None and envelope.get("packet_id") != expected_packet_id:
        raise HandoffError("PACKET_MISMATCH")
    packet_id = envelope.get("packet_id")
    if not isinstance(packet_id, str) or not _ID.fullmatch(packet_id):
        raise HandoffError("BAD_PACKET_ID")
    digest = envelope.get("zip_sha256")
    if (not isinstance(digest, str) or not _SHA.fullmatch(digest)
            or not _SHA.fullmatch(expected_zip_sha256)
            or digest != expected_zip_sha256):
        raise HandoffError("EXPECTED_ZIP_SHA_MISMATCH")
    nonce = _b64(envelope.get("nonce_b64"), 32)
    aad = _b64(envelope.get("aad_b64"), 1000)
    ciphertext = _b64(envelope.get("ciphertext_b64"), MAX_CIPHERTEXT * 2)
    if len(nonce) != 12 or not 16 <= len(ciphertext) <= MAX_CIPHERTEXT:
        raise HandoffError("BAD_NONCE_OR_CIPHERTEXT_SIZE")
    if (not isinstance(envelope.get("ciphertext_sha256"), str) or
            hashlib.sha256(ciphertext).hexdigest() != envelope["ciphertext_sha256"]):
        raise HandoffError("CIPHERTEXT_SHA_MISMATCH")
    expected_aad = (f"{expected_game_id}|{expected_work_id}|{packet_id}|"
                    f"zip_sha256={expected_zip_sha256}").encode("ascii")
    if aad != expected_aad:
        raise HandoffError("AAD_IDENTITY_MISMATCH")
    key = _decode_key(secret)
    try:
        plain = AESGCM(key).decrypt(nonce, ciphertext, aad)
    except Exception as exc:
        # Deliberately never include the key or payload in error text.
        raise HandoffError("AUTHENTICATION_FAILED") from exc
    if len(plain) > MAX_ZIP or hashlib.sha256(plain).hexdigest() != expected_zip_sha256:
        raise HandoffError("DECRYPTED_ZIP_SHA_MISMATCH")
    _verify_zip(plain)
    return plain


def write_new_file_only(path: Path, content: bytes) -> None:
    """Atomically claim a new filename, never overwrite a pre-existing path.

    Caller must use a trusted, already existing output DIRECTORY. Even O_EXCL
    cannot defend against a malicious concurrent replacement of parent dirs.
    """
    parent = path.parent
    if not parent.exists() or not parent.is_dir() or parent.is_symlink():
        raise HandoffError("OUTPUT_PARENT_NOT_TRUSTED")
    # Check all existing path ancestors for symlinks; user must protect the dir.
    for segment in (parent, *parent.parents):
        if segment.is_symlink():
            raise HandoffError("OUTPUT_PARENT_SYMLINK")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_BINARY"):
        flags |= os.O_BINARY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "wb") as file:
            fd = -1
            file.write(content)
            file.flush()
            os.fsync(file.fileno())
    except Exception:
        if fd >= 0:
            os.close(fd)
        # Do not automatically unlink: in an attacker-writable directory its
        # name might have been substituted after exclusive creation.
        raise


def restore(envelope_file: Path, output_file: Path, secret: str, *,
            expected_zip_sha256: str, expected_work_id: str,
            expected_game_id: str = "TRAP_RAIDERS",
            expected_packet_id: str | None = None) -> str:
    document = _read_envelope(envelope_file)
    contents = decode_and_verify(document, secret,
                                 expected_zip_sha256=expected_zip_sha256,
                                 expected_work_id=expected_work_id,
                                 expected_game_id=expected_game_id,
                                 expected_packet_id=expected_packet_id)
    write_new_file_only(output_file, contents)
    return hashlib.sha256(contents).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("envelope", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expect-zip-sha256", required=True)
    parser.add_argument("--expect-work-id", required=True)
    parser.add_argument("--expect-game-id", default="TRAP_RAIDERS")
    parser.add_argument("--expect-packet-id")
    args = parser.parse_args()
    key = os.environ.get("CHAT_CODEX_HANDOFF_KEY") or os.environ.get("P0D_HANDOFF_KEY")
    if not key:
        print("BLOCKED: HANDOFF_KEY_MISSING (supply through private OWNER channel)")
        return 2
    try:
        digest = restore(args.envelope, args.out, key,
                         expected_zip_sha256=args.expect_zip_sha256,
                         expected_work_id=args.expect_work_id,
                         expected_game_id=args.expect_game_id,
                         expected_packet_id=args.expect_packet_id)
    except (HandoffError, FileExistsError, FileNotFoundError, OSError, ValueError) as exc:
        # No untrusted path, exception value or key is echoed to stdout/logs.
        print("BLOCKED: RESTORE_FAILED (output not authorized or evidence invalid); type="
              + type(exc).__name__)
        return 2
    print("RESTORED_SHA256=" + digest)
    print("STATUS=RESTORE_LOCAL_ZIP_ONLY_NOT_STUDIO_QA")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
