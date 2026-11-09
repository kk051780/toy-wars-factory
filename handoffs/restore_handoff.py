#!/usr/bin/env python3
"""Decrypt an OWNER-delivered AES-256-GCM GitHub handoff envelope.

Requires: python -m pip install cryptography
Set P0D_HANDOFF_KEY from the *private ChatGPT conversation*, never GitHub.
This utility may safely be published; it contains no decryption key.
"""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import zipfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def b64decode(text):
    if isinstance(text, list):
        text = "".join(text)
    if not isinstance(text, str):
        raise ValueError("INVALID_B64")
    return base64.b64decode(text.encode("ascii"), validate=True)


def restore(envelope_file: Path, output_file: Path, secret: str):
    if output_file.exists():
        raise FileExistsError("OUTPUT_EXISTS: refuse overwrite; select a fresh path")
    if envelope_file.stat().st_size > 15_000_000:
        raise ValueError("ENVELOPE_TOO_LARGE")
    doc = json.loads(envelope_file.read_text(encoding="utf-8"))
    if doc.get("format") != "P0D_AES256_GCM_HANDOFF_V1":
        raise ValueError("UNSUPPORTED_FORMAT")
    raw_key = base64.urlsafe_b64decode(secret.strip() + "=" * (-len(secret.strip()) % 4))
    if len(raw_key) != 32:
        raise ValueError("HANDOFF_KEY_MUST_BE_32_BYTES")
    nonce = b64decode(doc["nonce_b64"])
    ciphertext = b64decode(doc["ciphertext_b64"])
    aad = b64decode(doc["aad_b64"])
    if len(nonce) != 12 or len(ciphertext) > 12_000_000:
        raise ValueError("ENVELOPE_INVALID_SIZE")
    if hashlib.sha256(ciphertext).hexdigest() != doc["ciphertext_sha256"]:
        raise ValueError("CIPHERTEXT_DIGEST_MISMATCH")
    plaintext = AESGCM(raw_key).decrypt(nonce, ciphertext, aad)
    if hashlib.sha256(plaintext).hexdigest() != doc["zip_sha256"]:
        raise ValueError("ZIP_DIGEST_MISMATCH")
    if len(plaintext) > 10_000_000:
        raise ValueError("ZIP_TOO_LARGE")
    with zipfile.ZipFile(io.BytesIO(plaintext)) as z:
        names = z.namelist()
        if len(names) != len(set(names)):
            raise ValueError("ZIP_DUPLICATE_ENTRY")
        for name in names:
            parts = name.replace("\\", "/").split("/")
            if name.startswith(("/", "\\")) or ".." in parts or ":" in name or "\\" in name:
                raise ValueError("ZIP_UNSAFE_PATH")
        if z.testzip() is not None:
            raise ValueError("ZIP_CORRUPT")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_bytes(plaintext)
    return doc["zip_sha256"]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("envelope", type=Path)
    p.add_argument("--out", type=Path, default=Path("TRAP_RAIDERS_v39_ChatLead.zip"))
    args = p.parse_args()
    secret = os.environ.get("P0D_HANDOFF_KEY")
    if not secret:
        raise SystemExit("Set P0D_HANDOFF_KEY from the private chat before running (not in GitHub).")
    try:
        print("RESTORED_ZIP_SHA256=" + restore(args.envelope, args.out, secret))
        print("RESTORED_PATH=" + str(args.out.resolve()))
    except Exception as exc:
        raise SystemExit(f"HANDOFF_RESTORE_FAILED: {type(exc).__name__}: {exc}")

if __name__ == "__main__":
    main()