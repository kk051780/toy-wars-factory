#!/usr/bin/env python3
"""Restore AES-256-GCM Chat->Codex sealed handoff, no key in GitHub or stdout.

Set CHAT_CODEX_HANDOFF_KEY privately; old P0D_HANDOFF_KEY is accepted for v39.
Requires pip package cryptography. The remote handoff is NOT an execution command.
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


def decode(v):
    if isinstance(v, list):
        v=''.join(v)
    return base64.b64decode(v,validate=True)


def restore(envelope_file, output_file, secret):
    if output_file.exists():
        raise FileExistsError('OUTPUT_EXISTS')
    if envelope_file.stat().st_size > 15_000_000:
        raise ValueError('ENVELOPE_TOO_LARGE')
    doc=json.loads(envelope_file.read_text(encoding='utf-8'))
    if doc.get('format')!='P0D_AES256_GCM_HANDOFF_V1':
        raise ValueError('UNSUPPORTED_ENVELOPE')
    key=base64.urlsafe_b64decode(secret.strip()+'='*(-len(secret.strip())%4))
    if len(key)!=32:
        raise ValueError('INVALID_HANDOFF_KEY')
    nonce,ciphertext,aad=decode(doc['nonce_b64']),decode(doc['ciphertext_b64']),decode(doc['aad_b64'])
    if len(nonce)!=12 or len(ciphertext)>12_000_000:
        raise ValueError('INVALID_CIPHERTEXT_SIZE')
    if hashlib.sha256(ciphertext).hexdigest()!=doc['ciphertext_sha256']:
        raise ValueError('CIPHERTEXT_SHA_MISMATCH')
    plain=AESGCM(key).decrypt(nonce,ciphertext,aad)
    if len(plain)>10_000_000 or hashlib.sha256(plain).hexdigest()!=doc['zip_sha256']:
        raise ValueError('ZIP_SHA_MISMATCH')
    with zipfile.ZipFile(io.BytesIO(plain)) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or z.testzip() is not None:
            raise ValueError('ZIP_CORRUPT_OR_DUPLICATE')
        for n in names:
            if (n.startswith(('/', '\\')) or '\\' in n or ':' in n or
                    any(t in ('','.','..') for t in n.split('/'))):
                raise ValueError('ZIP_UNSAFE_PATH')
    output_file.parent.mkdir(parents=True,exist_ok=True)
    output_file.write_bytes(plain)
    return doc['zip_sha256']


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('envelope',type=Path)
    p.add_argument('--out',type=Path,required=True)
    args=p.parse_args()
    key=os.environ.get('CHAT_CODEX_HANDOFF_KEY') or os.environ.get('P0D_HANDOFF_KEY')
    if not key:
        raise SystemExit('HANDOFF_KEY_MISSING: set CHAT_CODEX_HANDOFF_KEY privately; do not commit')
    try:
        digest=restore(args.envelope,args.out,key)
        print('RESTORED_ZIP_SHA256='+digest)
        print('RESTORED_PATH='+str(args.out.resolve()))
    except Exception as exc:
        raise SystemExit('RESTORE_FAILED: '+type(exc).__name__+': '+str(exc))

if __name__=='__main__':
    main()
