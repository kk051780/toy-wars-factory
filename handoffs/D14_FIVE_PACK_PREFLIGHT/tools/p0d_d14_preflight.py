#!/usr/bin/env python3
"""Owner-run D14 SEALED handoff preflight. Never decrypts or starts Roblox.

Fetches EXACT immutable GitHub plaintext-safe AES envelopes and READMEs,
validates the original Git blob SHA/packet/ZIP identifiers, and can optionally
stage ciphertext-only files in an existing empty private owner directory.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

SCHEMA = 'P0D_D14_SEALED_PREFLIGHT_V1'
SHA1 = re.compile(r'[0-9a-f]{40}\Z')
SHA256 = re.compile(r'[0-9a-f]{64}\Z')
ROLE_ORDER = ('SEATS','CART_RAIL','VISUAL','RAFT','RIDER')
CORE = frozenset(ROLE_ORDER[:3])
OPTIONAL = frozenset(ROLE_ORDER[3:])
MAX_JSON = 80_000
MAX_CONTENT = 2_000_000
EXPECTED_REPO = 'kk051780/toy-wars-factory'

class PreflightError(ValueError):
    pass

def strict_json(raw: bytes):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise PreflightError('DUPLICATE_KEY:' + str(key))
            obj[key] = value
        return obj
    def reject_constant(x):
        raise PreflightError('NONFINITE_JSON:'+x)
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_constant=reject_constant)
    except (ValueError, UnicodeError) as exc:
        if isinstance(exc, PreflightError): raise
        raise PreflightError('INVALID_JSON') from exc

def valid_path(path):
    return (isinstance(path,str) and 2 <= len(path) <= 160
            and all(re.fullmatch(r'[A-Za-z0-9_.-]+',p) and p not in ('.','..') for p in path.split('/')))

def valid_sha(value, kind):
    return isinstance(value,str) and bool((SHA1 if kind == 1 else SHA256).fullmatch(value))

def validate_manifest(m):
    if not isinstance(m,dict) or m.get('schema')!=SCHEMA or m.get('repository')!=EXPECTED_REPO or m.get('game_id')!='TRAP_RAIDERS' or m.get('work_id')!='p0d-siege-v19':
        raise PreflightError('WRONG_MANIFEST_ID')
    if m.get('core_cart') != list(ROLE_ORDER[:3]) or m.get('optional') != list(ROLE_ORDER[3:]):
        raise PreflightError('BAD_ROLE_ORDER')
    reject=m.get('superseded_commits')
    if (not isinstance(reject,list) or len(set(reject))!=len(reject) or
        not all(valid_sha(x,1) for x in reject) or
        'cae5691b622045af57674d922a08a96764354412' not in reject or
        '250658457392e016c668de8d3c368499f39714bc' not in reject):
        raise PreflightError('BAD_SUPERSEDED_SET')
    rows=m.get('packets')
    if not isinstance(rows,list) or len(rows)!=5 or [x.get('role') for x in rows if isinstance(x,dict)]!=list(ROLE_ORDER):
        raise PreflightError('WRONG_PACKET_ORDER')
    seen=set()
    for p in rows:
        if not isinstance(p,dict) or set(p)!={'role','packet_id','commit','encrypted_path','encrypted_git_blob_sha1','readme_path','readme_git_blob_sha1','restored_zip_sha256'}:
            raise PreflightError('BAD_PACKET_SHAPE')
        role=p['role']
        if not isinstance(p['packet_id'],str) or not p['packet_id'].startswith('P0D-D14-') or p['packet_id'] in seen:
            raise PreflightError('BAD_PACKET_ID')
        seen.add(p['packet_id'])
        if not valid_sha(p['commit'],1) or p['commit'] in reject:
            raise PreflightError('SUPERSEDED_OR_UNPINNED_COMMIT')
        if not all(valid_sha(p[k],i) for k,i in [('encrypted_git_blob_sha1',1),('readme_git_blob_sha1',1),('restored_zip_sha256',256)]):
            raise PreflightError('BAD_EXPECTED_HASH')
        if not valid_path(p['encrypted_path']) or not p['encrypted_path'].startswith('handoffs/') or not p['encrypted_path'].endswith('_encrypted.json'):
            raise PreflightError('BAD_ENVELOPE_PATH')
        if not valid_path(p['readme_path']) or not p['readme_path'].startswith('handoffs/README_') or not p['readme_path'].endswith('.md'):
            raise PreflightError('BAD_README_PATH')
    return rows

def git_blob_sha(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def verified_packet(p, encrypted:bytes, readme:bytes):
    if not isinstance(encrypted, bytes) or not isinstance(readme, bytes) or len(encrypted)>MAX_CONTENT or len(readme)>MAX_CONTENT:
        raise PreflightError('FILE_TOO_LARGE')
    if git_blob_sha(encrypted)!=p['encrypted_git_blob_sha1']:
        raise PreflightError('ENCRYPTED_GIT_BLOB_MISMATCH:'+p['role'])
    if git_blob_sha(readme)!=p['readme_git_blob_sha1']:
        raise PreflightError('README_GIT_BLOB_MISMATCH:'+p['role'])
    env=strict_json(encrypted)
    if not isinstance(env,dict) or env.get('packet_id')!=p['packet_id'] or env.get('zip_sha256')!=p['restored_zip_sha256']:
        raise PreflightError('ENVELOPE_IDENTITY_MISMATCH:'+p['role'])
    if p['packet_id'].encode() not in readme:
        raise PreflightError('README_PACKET_ID_MISMATCH:'+p['role'])
    if p['restored_zip_sha256'].encode() not in readme:
        raise PreflightError('README_ZIP_SHA_MISMATCH:'+p['role'])
    return {'role':p['role'],'packet_id':p['packet_id'],'commit':p['commit'],
            'encrypted_git_blob_sha1':git_blob_sha(encrypted),'readme_git_blob_sha1':git_blob_sha(readme),
            'restored_zip_sha256':p['restored_zip_sha256'],'status':'CIPHERTEXT_READBACK_PASS_NO_RESTORE'}

def fetch_raw(repo:str, sha:str, path:str):
    if repo!=EXPECTED_REPO or not valid_sha(sha,1) or not valid_path(path):
        raise PreflightError('UNSAFE_FETCH_ARGUMENT')
    url='https://raw.githubusercontent.com/'+repo+'/'+sha+'/'+quote(path,safe='/')
    req=Request(url,headers={'User-Agent':'P0D-D14-Prefight/1.0','Accept':'application/octet-stream'})
    with urlopen(req,timeout=20) as response:
        final=response.geturl()
        if not final.startswith('https://raw.githubusercontent.com/'+repo+'/'+sha+'/'):
            raise PreflightError('UNEXPECTED_REDIRECT')
        raw=response.read(MAX_CONTENT+1)
    if len(raw)>MAX_CONTENT: raise PreflightError('FILE_TOO_LARGE')
    return raw

def preflight(m, loader=fetch_raw):
    rows=validate_manifest(m)
    receipts=[]
    fetched=[]
    # No files are staged until all five pairs have been authenticated.
    for p in rows:
        enc=loader(m['repository'],p['commit'],p['encrypted_path'])
        readme=loader(m['repository'],p['commit'],p['readme_path'])
        receipts.append(verified_packet(p,enc,readme))
        fetched.append((p,enc,readme))
    return receipts,fetched

def stage_verified(directory:Path, fetched):
    if directory.is_symlink() or not directory.is_dir():
        raise PreflightError('STAGING_DIRECTORY_MUST_EXIST_AND_NOT_BE_SYMLINK')
    if list(directory.iterdir()):
        raise PreflightError('STAGING_DIRECTORY_NOT_EMPTY')
    planned=[]
    for p,enc,readme in fetched:
        planned.append((directory / (p['role']+'_encrypted.json'), enc))
        planned.append((directory / (p['role']+'_README.md'), readme))
    made=[]
    try:
        for path,raw in planned:
            flags=os.O_CREAT|os.O_EXCL|os.O_WRONLY
            if hasattr(os,'O_NOFOLLOW'): flags|=os.O_NOFOLLOW
            fd=os.open(path,flags,0o600)
            made.append(path)
            with os.fdopen(fd,'wb') as fh:
                fh.write(raw)
        return len(made)
    except Exception:
        for path in made:
            path.unlink(missing_ok=True)
        raise

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest',type=Path,default=Path(__file__).resolve().parent.parent/'d14_packets.json')
    ap.add_argument('--stage',type=Path,help='EXISTING EMPTY owner-only directory; ciphertext+README only, no keys')
    ap.add_argument('--receipt',type=Path,help='new JSON report; refuses overwrite')
    args=ap.parse_args(argv)
    try:
        if args.manifest.stat().st_size>MAX_JSON: raise PreflightError('MANIFEST_TOO_LARGE')
        m=strict_json(args.manifest.read_bytes())
        receipts,fetched=preflight(m)
        created=stage_verified(args.stage,fetched) if args.stage else 0
        report={'schema':'P0D_D14_PREFLIGHT_RESULT_V1','game_id':'TRAP_RAIDERS','packets':receipts,
                'authenticated_pairs':len(receipts),'staged_files':created,
                'cart_core_roles':list(ROLE_ORDER[:3]),'optional_roles':list(ROLE_ORDER[3:]),
                'windows_restore':'NOT_TESTED','studio_integration':'NOT_TESTED',
                'next':'OWNER_DIRECT_CODEX_RESTORE_ONE_AT_A_TIME_ONLY_AFTER_PC_CHECKPOINT_AND_KEYS'}
        result=(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
        if args.receipt:
            if args.receipt.is_symlink():raise PreflightError('OUTPUT_SYMLINK')
            with args.receipt.open('xb') as fh: fh.write(result)
        else:sys.stdout.buffer.write(result)
        return 0
    except (PreflightError,OSError,ValueError,TypeError) as exc:
        print('P0D_D14_PREFLIGHT_BLOCKED:'+str(exc).splitlines()[0][:150],file=sys.stderr)
        return 2
if __name__=='__main__':
    raise SystemExit(main())
