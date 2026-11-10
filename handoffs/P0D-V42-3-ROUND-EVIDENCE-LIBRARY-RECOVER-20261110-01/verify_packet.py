"""Read-only standard-library verifier for this CHAT-LEAD reference ZIP.
Use independently of v42.1/v42.2's BUILD_MANIFEST format.
"""
import hashlib
import json
import pathlib
import sys
import zipfile


def verify(zip_path):
    archive = pathlib.Path(zip_path)
    if not archive.is_file() or archive.stat().st_size > 10_000_000:
        raise ValueError('MISSING_OR_OVERSIZED_ZIP')
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        if len(names)!=len(set(names)) or any(pathlib.PurePosixPath(n).is_absolute() or '..' in pathlib.PurePosixPath(n).parts or '\\' in n or n.endswith('/') for n in names):
            raise ValueError('BAD_ZIP_ENTRIES')
        if 'PACKET_MANIFEST.json' not in names:
            raise ValueError('MISSING_MANIFEST')
        if any(i.file_size > 1_000_000 or (i.compress_size and i.file_size / i.compress_size > 200) for i in z.infolist()):
            raise ValueError('UNSAFE_ZIP_SIZE')
        m=json.loads(z.read('PACKET_MANIFEST.json'))
        expected=set(m['files'])|{'PACKET_MANIFEST.json'}
        if set(names)!=expected:
            raise ValueError('UNEXPECTED_OR_MISSING_FILES')
        if m.get('game_id')!='TRAP_RAIDERS' or m.get('work_id')!='p0d-siege-v19' or m.get('release_ready') is not False or m.get('studio_qa')!='NOT_TESTED':
            raise ValueError('BAD_ID_OR_STATUS')
        for name,record in m['files'].items():
            blob=z.read(name)
            if len(blob)!=record['bytes'] or hashlib.sha256(blob).hexdigest()!=record['sha256']:
                raise ValueError('HASH_MISMATCH: '+name)
        return {'ok':True,'files':len(m['files']),'studio_qa':m['studio_qa'],'release_ready':m['release_ready']}


if __name__=='__main__':
    try:
        print(json.dumps(verify(sys.argv[1]),sort_keys=True))
    except (ValueError,KeyError,IndexError,zipfile.BadZipFile) as ex:
        print(f'FAIL: {ex}',file=sys.stderr)
        raise SystemExit(1)
