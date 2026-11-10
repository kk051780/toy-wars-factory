#!/usr/bin/env python3
"""Fail-closed read-only ZIP/manifest verification for D07 composition reference."""
from __future__ import annotations
import argparse, hashlib, io, json, stat, zipfile
from pathlib import Path
PACKET_ID='P0D-D07-GOROGAN-COMBINED-WIRING-20261110-04'
MAX_BYTES=1_000_000
MAX_FILE=150_000
MAX_UNPACKED=1_000_000

def sha(b):return hashlib.sha256(b).hexdigest()

def verify(contents:bytes):
    if not isinstance(contents,bytes) or not 0<len(contents)<=MAX_BYTES:raise ValueError('ZIP_SIZE')
    with zipfile.ZipFile(io.BytesIO(contents)) as z:
        infos=z.infolist();names=[i.filename for i in infos]
        if len(names)<5 or len(names)>64 or len(names)!=len(set(names)) or len(names)!=len({x.casefold() for x in names}):raise ValueError('ENTRY_SET')
        total=0
        for item in infos:
            p=item.filename;mode=(item.external_attr>>16)&0xffff
            total+=item.file_size
            if not p or p.startswith(('/','\\')) or '\\' in p or ':' in p or item.is_dir() or any(x in ('','.','..') for x in p.split('/')) or stat.S_IFMT(mode) not in (0,stat.S_IFREG):raise ValueError('UNSAFE_ZIP_PATH')
            if item.file_size>MAX_FILE or total>MAX_UNPACKED:raise ValueError('ZIP_BOMB')
        if z.testzip() is not None:raise ValueError('BAD_CRC')
        if 'BUILD_MANIFEST.json' not in names:raise ValueError('MISSING_MANIFEST')
        manifest=json.loads(z.read('BUILD_MANIFEST.json'))
        if manifest.get('schema_version')!=1 or manifest.get('packet_id')!=PACKET_ID or manifest.get('classification')!='REFERENCE_ONLY':raise ValueError('INVALID_MANIFEST')
        files=manifest.get('files')
        if not isinstance(files,dict) or set(files)!=set(names)-{'BUILD_MANIFEST.json'}:raise ValueError('MANIFEST_MISMATCH')
        for name,spec in files.items():
            content=z.read(name)
            if not isinstance(spec,dict) or spec.get('size_bytes')!=len(content) or spec.get('sha256')!=sha(content):raise ValueError('SOURCE_SHA')
        return {'ok':True,'packet_id':PACKET_ID,'files':len(files),'zip_sha256':sha(contents),'studio_qa':'NOT_TESTED'}

def main():
 p=argparse.ArgumentParser();p.add_argument('zip',type=Path);args=p.parse_args()
 print(json.dumps(verify(args.zip.read_bytes()),sort_keys=True))
if __name__=='__main__':main()
