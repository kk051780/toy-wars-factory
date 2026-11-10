#!/usr/bin/env python3
"""Safely stage a privately received source-bundle, WITHOUT any decryption key.
No game source is printed, committed, merged, or installed in Roblox Studio.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import zipfile

from verify_local_bundle import check


def receive(bundle_path, out_dir):
    summary=check(bundle_path)  # Verify all source/member SHA before any mutation.
    out_dir=Path(out_dir)
    if out_dir.exists():
        raise FileExistsError("Destination exists: never merge or overwrite prior work")
    out_dir.mkdir(parents=True,mode=0o700,exist_ok=False)
    try:
        with zipfile.ZipFile(bundle_path) as z:
            catalog=z.read('MIGRATION_CATALOG.json')
            parsed=json.loads(catalog)
            for item in parsed['available_local_source_zips']:
                name=item['filename']
                if Path(name).name!=name or not name.endswith('.zip'):
                    raise ValueError('Invalid source ZIP name')
                b=z.read('source_zips/'+name)
                if len(b)!=item['bytes'] or hashlib.sha256(b).hexdigest()!=item['sha256']:
                    raise ValueError('Source ZIP hash changed')
                p=out_dir/name
                fd=os.open(str(p),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
                with os.fdopen(fd,'wb') as f:
                    f.write(b);f.flush();os.fsync(f.fileno())
                if os.name!='nt':os.chmod(p,0o600)
            fd=os.open(str(out_dir/'MIGRATION_CATALOG.json'),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'wb') as f:f.write(catalog)
        return summary
    except BaseException:
        # A partial staging directory is NEVER valid. Do not delete a user-owned
        # directory here because it was newly and exclusively created by us.
        for f in out_dir.iterdir():
            if f.is_file():f.unlink()
        out_dir.rmdir()
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--out-dir',required=True)
    a=p.parse_args()
    try:
        print(json.dumps({'status':'PRIVATE_BUNDLE_STAGED_NO_GAME_INTEGRATION',**receive(a.bundle,a.out_dir)},sort_keys=True))
    except Exception as e:
        print('BUNDLE_STAGE_BLOCKED='+type(e).__name__,file=sys.stderr)
        raise SystemExit(2)
