#!/usr/bin/env python3
"""Migrate owner-only manual bundle to public-safe recipient-sealed packets.
A public recipient registration must already exist. This does not generate a
new private identity and requires no handoff of per-ZIP AES keys.
"""
import argparse, hashlib, importlib.util, io, json, pathlib, tempfile, zipfile

MODULE=pathlib.Path(__file__).with_name('keyless_handoff_v2.py')
spec=importlib.util.spec_from_file_location('keyless_handoff_v2',MODULE)
h=importlib.util.module_from_spec(spec)
spec.loader.exec_module(h)


def run(bundle_path, recipient_path, out_dir, include_legacy=False):
    out_dir=pathlib.Path(out_dir)
    if out_dir.exists():
        raise FileExistsError('Output directory must not already exist')
    out_dir.mkdir(parents=True,exist_ok=False)
    results=[]
    try:
        with zipfile.ZipFile(bundle_path) as b:
            catalog=json.loads(b.read('MIGRATION_CATALOG.json'))
            for item in catalog['available_local_source_zips']:
                if item['inner_manifest_status']!='VERIFIED' and not include_legacy:
                    results.append({'filename':item['filename'],'status':'HOLD_LEGACY_NO_MANIFEST'})
                    continue
                plain=b.read('source_zips/'+item['filename'])
                if h.sha(plain)!=item['sha256'] or len(plain)!=item['bytes']:
                    raise ValueError('Migration bundle source mismatch')
                with tempfile.TemporaryDirectory() as tmp:
                    temp_zip=pathlib.Path(tmp)/'source.zip'
                    temp_zip.write_bytes(plain)
                    packet_id='MIGRATED_'+item['filename'].removesuffix('.zip').replace('TRAP_RAIDERS_','')
                    out=out_dir/(packet_id+'.keyless.json')
                    m=h.seal(temp_zip,recipient_path,packet_id,out)
                if m['zip_sha256']!=item['sha256']:
                    raise ValueError('Output identity mismatch')
                results.append({'filename':item['filename'],'packet_id':packet_id,
                                'status':'SEALED_FOR_OWNER_RECIPIENT',
                                'plaintext_sha256':item['sha256'],
                                'sealed_sha256':h.sha(out.read_bytes()),'sealed_filename':out.name,
                                'sealed_bytes':out.stat().st_size})
        manifest={'format':'TWF_KEYLESS_V2_MIGRATED_BATCH','items':results,
                  'recipient_key_id':h.read_json(recipient_path,limit=2048)['recipient_key_id'],
                  'note':'These files are encrypted to this recipient; GitHub remote upload/readback not yet performed.'}
        h.atomic_new(out_dir/'SEALED_INDEX.json',h.canonical(manifest)+b'\n')
        return manifest
    except BaseException:
        # Do not leave misleading half-complete staging directories.
        for f in out_dir.glob('*'):
            if f.is_file():f.unlink()
        out_dir.rmdir()
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bundle',required=True);p.add_argument('--recipient',required=True);p.add_argument('--out-dir',required=True);p.add_argument('--include-legacy',action='store_true')
    a=p.parse_args()
    res=run(a.bundle,a.recipient,a.out_dir,a.include_legacy)
    print(json.dumps({'sealed':sum(x['status']=='SEALED_FOR_OWNER_RECIPIENT' for x in res['items']),
                      'held':sum(x['status'].startswith('HOLD') for x in res['items']),
                      'recipient_key_id':res['recipient_key_id']},sort_keys=True))
