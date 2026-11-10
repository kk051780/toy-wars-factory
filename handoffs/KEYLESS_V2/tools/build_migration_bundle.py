#!/usr/bin/env python3
"""Pack user-owned local ZIPs into a PRIVATE manual fallback archive, no passwords.
Never upload the resulting bundle to a PUBLIC GitHub repo. This creates a
source ZIP inventory, not a Roblox Studio integration or QA claim.
"""
import argparse, datetime, hashlib, io, json, pathlib, zipfile

SOURCES={
    'TRAP_RAIDERS_v39_ChatLead.zip':('D06', 'baa29df8bc3f10f94792fcb135b3ee2a136ad8b8'),
    'TRAP_RAIDERS_v40_v42_ChatLead.zip':('D07_D08_D10', 'c0b0bf692410cb651893c38f1a453c93d9f8b3b5'),
    'TRAP_RAIDERS_v42_3.zip':('LEGACY_V42_3', None),
    'TRAP_RAIDERS_v43A_ChatLead.zip':('D11', 'db734240f0157cc125b563656dbd09668226f3ab'),
    'TRAP_RAIDERS_D07_GoroganVisual.zip':('D07', '5128e288c7bd119a470c253a9792f4d829c569ec'),
    'TRAP_RAIDERS_D07_GoroganServerAI.zip':('D07', '80483ad6543fd73dfaf8a21ecf7b58dc2eca75e1'),
    'TRAP_RAIDERS_D07_GoroganRigNavDamage.zip':('D07', 'e7801615c5b70346dfaec189f195a65f5b597ec9'),
    'TRAP_RAIDERS_D07_GoroganCombinedWiring.zip':('D07', '05fb3b1b986a2d8dfb925bce7592b13da6f61316'),
    'TRAP_RAIDERS_D08_CanonicalEventBridge.zip':('D08', '2ecf899d1202c6bf6868355dc02d2a3ad4f03d47'),
    'TRAP_RAIDERS_D11_V43A_AcceptanceGate.zip':('D11_QA', 'a9038099c2e1ce333bb005f5a1af0259f22cf554'),
    'TRAP_RAIDERS_D15_ChatLead.zip':('D15', 'f789276cee28d40d8cdfb59a9c57c303f6d5fd09'),
    'TRAP_RAIDERS_D17_CosmeticCatalog.zip':('D17', 'e2117e9d7dd42ef895b7bae48e6fc9e8520b917d'),
}

def sha(data):return hashlib.sha256(data).hexdigest()

def inspect(archive):
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        names=[f.filename for f in z.infolist() if not f.is_dir()]
        if len(names)!=len(set(names)) or any(n.startswith('/') or '..' in n.split('/') or '\\' in n for n in names):
            raise ValueError('Unsafe ZIP')
        if 'BUILD_MANIFEST.json' not in names:
            return 'LEGACY_NO_MANIFEST',len(names)
        m=json.loads(z.read('BUILD_MANIFEST.json'))
        f=m.get('files')
        if isinstance(f,dict):rows=[{'path':k,**v} for k,v in f.items()]
        elif isinstance(f,list):rows=f
        else:raise ValueError('Unrecognized manifest')
        if {x['path'] for x in rows}!={n for n in names if n!='BUILD_MANIFEST.json'}:
            raise ValueError('Manifest entry list differs')
        for e in rows:
            if sha(z.read(e['path']))!=e['sha256']:
                raise ValueError('Inner SHA mismatch')
        return 'VERIFIED',len(rows)


def build(source_dir,bundle_path,catalog_public_path):
    source_dir=pathlib.Path(source_dir)
    entries=[]
    for filename,(lane,remote) in sorted(SOURCES.items()):
        p=source_dir/filename
        if not p.is_file():
            entries.append({'filename':filename,'feature':lane,'source_commit':remote,'status':'MISSING_LOCAL_SOURCE'})
            continue
        b=p.read_bytes()
        status,count=inspect(b)
        entries.append({'filename':filename,'feature':lane,'source_commit':remote,'status':'AVAILABLE_LOCAL_SOURCE',
                        'bytes':len(b),'sha256':sha(b),'inner_manifest_status':status,'inner_files':count})
    available=[x for x in entries if x['status']=='AVAILABLE_LOCAL_SOURCE']
    if not available:raise ValueError('No source ZIPs available')
    catalog={'format':'P0D_KEYLESS_V2_LOCAL_MIGRATION_CATALOG','game_id':'TRAP_RAIDERS',
             'work_id':'p0d-siege-v19','available_local_source_zips':available,
             'missing_local_source_zips':[x for x in entries if x['status']=='MISSING_LOCAL_SOURCE'],
             'pc_restore_claims_from_last_issues':['D06/v39 scoped','D11/v43-A scoped','D07 rig isolated scoped'],
             'not_in_scope':'No claim that other chats D13/D14/D16/D18 private source files are mounted; no Studio QA',
             'next_step':'Private repo upload OR seal each source ZIP with owner PC PUBLIC recipient, no pasted password'}
    compact=json.dumps(catalog,ensure_ascii=False,sort_keys=True,indent=2).encode()+b'\n'
    catalog_public_path=pathlib.Path(catalog_public_path)
    catalog_public_path.parent.mkdir(parents=True,exist_ok=True)
    if catalog_public_path.exists():raise FileExistsError('Do not overwrite existing catalog')
    catalog_public_path.write_bytes(compact)
    bundle_path=pathlib.Path(bundle_path)
    if bundle_path.exists():raise FileExistsError('Do not overwrite existing bundle')
    with zipfile.ZipFile(bundle_path,'x',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
        z.writestr('MIGRATION_CATALOG.json',compact)
        z.writestr('PRIVATE_README.txt',(
            'TRAP RAIDERS / P0D OWNER PRIVATE LOCAL KEYLESS BUNDLE\n'
            'No passwords, no pasted decryption keys.\n'
            'CONFIDENTIAL: Contains game source ZIPs. NEVER PUSH THIS BUNDLE TO PUBLIC GITHUB.\n'
            'For OWNER PC transfer, download privately and give the file path to Codex.\n'
            'Compare sha256 and inspect MIGRATION_CATALOG.json before extracting.\n'
            'Individual ZIPs are source REFERENCE packets, not verified Studio integration.\n'
            'Some previously PC-integrated packets are still here for inventory; do not re-integrate blindly.\n'
            'The legacy v42_3 archive lacks a current BUILD_MANIFEST, so quarantine for manual review.\n'
            ).encode())
        for x in available:
            z.write(source_dir/x['filename'],arcname='source_zips/'+x['filename'])
    return {'count':len(available),'source_bytes':sum(x['bytes'] for x in available),
            'bundle_bytes':bundle_path.stat().st_size,'bundle_sha256':sha(bundle_path.read_bytes())}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source-dir',required=True);ap.add_argument('--out',required=True);ap.add_argument('--catalog',required=True)
    a=ap.parse_args();print(json.dumps(build(a.source_dir,a.out,a.catalog),sort_keys=True))
