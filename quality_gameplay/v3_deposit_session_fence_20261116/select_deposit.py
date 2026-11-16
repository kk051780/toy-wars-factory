#!/usr/bin/env python3
"""Fail-closed, byte-exact membership fence for ORIGINAL V3 own-castle deposit callback."""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path
FEATURE = 'GQ-V3-OWN-DEPOSIT-CURRENT-SESSION-FENCE-20261116'
ORIGINAL_HEAD = 'fe67d31bc8d1b3e481cd22d2be9ea54a1eb031c9'
ORIGINAL_BLOB = '7162b209bf67b74a71553217f3f744e072a0365d'
BLOCK = (b'prompt(deposit,"\xe5\x8d\xb5\xe3\x82\x92\xe7\xb4\x8d\xe5\x85\xa5","\xe8\x87\xaa\xe5\x88\x86\xe3\x81\xae\xe5\x9f\x8e",function(p)\n'
         b'  if tostring(p.UserId)~=entry.id or not session.rules then return end')
REPLACEMENT = BLOCK.replace(
    b' or not session.rules then return end',
    b' or joined[p.UserId]~=session.mode or sessions[session.mode]~=session or not session.rules then return end'
)
def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
def transform(data: bytes, *, inverse: bool = False) -> bytes:
    start, dest = (REPLACEMENT, BLOCK) if inverse else (BLOCK, REPLACEMENT)
    if data.count(start) != 1 or data.count(dest) != 0:
        raise ValueError('RED: absent/duplicate/already-selected own-egg callback')
    result = data.replace(start, dest, 1)
    if result.replace(dest, start, 1) != data:
        raise AssertionError('RED: byte-exact rollback failed')
    return result
def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--original', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--expected-original-blob', default=ORIGINAL_BLOB)
    parser.add_argument('--inverse', action='store_true')
    args = parser.parse_args()
    source = args.original.read_bytes()
    if not args.inverse and git_blob_sha(source) != args.expected_original_blob:
        raise ValueError('RED: immutable original Git blob mismatch')
    result = transform(source, inverse=args.inverse)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(result)
    print(f'{FEATURE}: {len(source)} to {len(result)} bytes, exact rollback; selected_blob={git_blob_sha(result)}')
if __name__ == '__main__':
    main()
