#!/usr/bin/env python3
"""Verify hashes of the bundled public QA tool; does not authenticate GitHub provenance."""
import hashlib
import json
from pathlib import Path
import re
import sys

PATH_RE=re.compile(r'^[A-Za-z0-9_./-]{1,150}$')
PACKET='P0D-D07-GOROGAN-STUDIO-TRACE-GATE-20261110-01'


def verify(root):
    root=Path(root)
    m=json.loads((root/'BUILD_MANIFEST.json').read_text(encoding='utf-8'))
    if m.get('schema')!='P0D_PUBLIC_SAFE_MANIFEST_V1' or m.get('packet_id')!=PACKET:
        raise ValueError('manifest identity mismatch')
    items=m.get('files')
    if not isinstance(items,list) or not items or len(items)>64:
        raise ValueError('invalid manifest entries')
    seen=set()
    for item in items:
        if not isinstance(item,dict): raise ValueError('bad entry')
        name=item.get('path')
        if not isinstance(name,str) or not PATH_RE.fullmatch(name) or name.startswith('/') or '..' in name.split('/') or name.startswith('./'):
            raise ValueError('unsafe path')
        folded=name.casefold()
        if folded in seen: raise ValueError('duplicate manifest path')
        seen.add(folded)
        path=root/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size>2_000_000:
            raise ValueError('missing or unsafe file: '+name)
        data=path.read_bytes()
        if hashlib.sha256(data).hexdigest()!=item.get('sha256') or len(data)!=item.get('size'):
            raise ValueError('SHA or size mismatch: '+name)
    return len(items)


if __name__=='__main__':
    try:
        count=verify(sys.argv[1] if len(sys.argv)>1 else Path(__file__).resolve().parent.parent)
        print(f'PUBLIC_MANIFEST_VERIFIED {count}')
    except (ValueError,OSError,KeyError,json.JSONDecodeError) as exc:
        print('PUBLIC_MANIFEST_INVALID '+str(exc),file=sys.stderr)
        sys.exit(1)
