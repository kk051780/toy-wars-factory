#!/usr/bin/env python3
"""Verify a PRIVATE local migration bundle without extracting it."""
import argparse, hashlib, io, json, pathlib, zipfile


def check(path):
    with zipfile.ZipFile(path) as b:
        entries=b.namelist()
        if len(entries)!=len(set(entries)) or any(n.startswith('/') or '..' in n.split('/') or '\\' in n for n in entries):
            raise ValueError('Invalid member name')
        catalog=json.loads(b.read('MIGRATION_CATALOG.json'))
        assets=catalog['available_local_source_zips']
        assert len(assets)>0
        seen=set()
        for item in assets:
            file='source_zips/'+item['filename']
            if file in seen:raise ValueError('duplicate catalog entry')
            seen.add(file)
            data=b.read(file)
            if hashlib.sha256(data).hexdigest()!=item['sha256'] or len(data)!=item['bytes']:
                raise ValueError('Source file hash mismatch')
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                inner={i.filename for i in z.infolist() if not i.is_dir()}
                if item['inner_manifest_status']=='VERIFIED':
                    manifest=json.loads(z.read('BUILD_MANIFEST.json'))
                    items=manifest['files']
                    if isinstance(items,dict): items=[{'path':k,**v} for k,v in items.items()]
                    if set(x['path'] for x in items)!=inner-{'BUILD_MANIFEST.json'}:
                        raise ValueError('Inner manifest entry mismatch')
                    for x in items:
                        if hashlib.sha256(z.read(x['path'])).hexdigest()!=x['sha256']:
                            raise ValueError('Inner SHA mismatch')
                elif item['inner_manifest_status']!='LEGACY_NO_MANIFEST':
                    raise ValueError('Unknown manifest status')
        if len(seen)!=len(assets):raise ValueError('Catalog mismatch')
        if set(entries) != seen | {'MIGRATION_CATALOG.json','PRIVATE_README.txt'}:
            raise ValueError('Unexpected/hidden bundle members')
        return {'source_zips':len(assets),'verified_manifest':sum(x['inner_manifest_status']=='VERIFIED' for x in assets),
                'legacy_missing_manifest':sum(x['inner_manifest_status']=='LEGACY_NO_MANIFEST' for x in assets)}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('bundle');a=ap.parse_args()
    print(json.dumps(check(a.bundle),ensure_ascii=False,sort_keys=True))
