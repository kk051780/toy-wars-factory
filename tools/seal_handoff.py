#!/usr/bin/env python3
"""Encrypt a tested source ZIP for a PUBLIC GitHub handoff without publishing plaintext.

DO NOT upload the output key file. Never print the key in a GitHub Issue or logs.
The caller must supply a unique destination for both ciphertext JSON and key file.
The handoff is distribution only and does not authorize code merge or Roblox release.
"""
import argparse
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import zipfile

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

MAX_ZIP_BYTES = 10_000_000


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def check_zip_bytes(contents):
    if not contents or len(contents) > MAX_ZIP_BYTES:
        raise ValueError('ZIP_SIZE_REJECTED')
    with zipfile.ZipFile(io.BytesIO(contents)) as z:
        names = z.namelist()
        if len(names) != len(set(names)) or z.testzip() is not None:
            raise ValueError('ZIP_DUPLICATE_OR_CORRUPT')
        for info in z.infolist():
            path = info.filename
            if (path.startswith(('/', '\\')) or '\\' in path or ':' in path or
                    any(x in ('', '.', '..') for x in path.split('/')) or info.is_dir()):
                raise ValueError('ZIP_UNSAFE_PATH')
    return True


def encode_b64(data):
    return base64.b64encode(data).decode('ascii')


def seal(contents, game_id, work_id, packet_id, key=None, nonce=None):
    for name in (game_id, work_id, packet_id):
        if not isinstance(name, str) or re.fullmatch(r'[A-Za-z0-9_.-]{1,96}', name) is None:
            raise ValueError('INVALID_ID')
    check_zip_bytes(contents)
    key = os.urandom(32) if key is None else key
    nonce = os.urandom(12) if nonce is None else nonce
    if len(key) != 32 or len(nonce) != 12:
        raise ValueError('INVALID_KEY_OR_NONCE')
    zip_sha = sha256(contents)
    aad = f'{game_id}|{work_id}|{packet_id}|zip_sha256={zip_sha}'.encode()
    ciphertext = AESGCM(key).encrypt(nonce, contents, aad)
    b64 = encode_b64(ciphertext)
    doc = {
        'format': 'P0D_AES256_GCM_HANDOFF_V1',
        'game_id': game_id, 'work_id': work_id, 'packet_id': packet_id,
        'nonce_b64': encode_b64(nonce),
        'aad_b64': encode_b64(aad),
        'zip_sha256': zip_sha,
        'ciphertext_sha256': sha256(ciphertext),
        'ciphertext_b64': [b64[i:i+96] for i in range(0, len(b64), 96)],
        'private_key_not_included': True,
    }
    return doc, base64.urlsafe_b64encode(key).decode('ascii').rstrip('=')


def secure_new_file(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, 'w', encoding='utf-8') as file:
        file.write(text)
    os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source_zip', type=Path)
    p.add_argument('--game-id', required=True)
    p.add_argument('--work-id', required=True)
    p.add_argument('--packet-id', required=True)
    p.add_argument('--encrypted-json', required=True, type=Path)
    p.add_argument('--key-out', required=True, type=Path)
    args = p.parse_args()
    if args.encrypted_json.resolve() == args.key_out.resolve():
        raise SystemExit('JSON_AND_KEY_PATH_MUST_DIFFER')
    for path in (args.encrypted_json, args.key_out):
        if path.exists():
            raise SystemExit('OUTPUT_EXISTS_ABORT: '+str(path))
    doc, secret = seal(args.source_zip.read_bytes(), args.game_id, args.work_id, args.packet_id)
    # Write the key locally first (private), then the encrypted JSON. Never print key.
    secure_new_file(args.key_out, secret+'\n')
    secure_new_file(args.encrypted_json, json.dumps(doc, sort_keys=True, indent=2)+'\n')
    print('ZIP_SHA256='+doc['zip_sha256'])
    print('ENCRYPTED_JSON_SHA256='+sha256(args.encrypted_json.read_bytes()))
    print('ENCRYPTED_JSON_PATH='+str(args.encrypted_json))
    print('PRIVATE_KEY_FILE='+str(args.key_out)+' (NEVER UPLOAD)')

if __name__ == '__main__':
    main()