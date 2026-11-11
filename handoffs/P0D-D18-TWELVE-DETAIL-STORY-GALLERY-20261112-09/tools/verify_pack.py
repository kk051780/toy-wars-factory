import pathlib,hashlib,json,sys
R=pathlib.Path(__file__).resolve().parents[1]
def verify(root=R):
    m=json.loads((root/'BUILD_MANIFEST.json').read_text('utf-8'))
    assert set(m)=={'files','format','game_id','packet_id','public_source_allowed','work_id'}
    assert (m['format'],m['game_id'],m['work_id'],m['public_source_allowed'])==('P0D_PUBLIC_SOURCE_V1','TRAP_RAIDERS','p0d-siege-v19',True)
    filenames={str(x.relative_to(root)) for x in root.rglob('*') if x.is_file() and '__pycache__' not in str(x)}
    assert filenames-{'BUILD_MANIFEST.json'}=={f['path'] for f in m['files']}
    for f in m['files']:
        assert not pathlib.PurePosixPath(f['path']).is_absolute() and '..' not in pathlib.PurePosixPath(f['path']).parts
        p=root/f['path'];raw=p.read_bytes()
        assert len(raw)==f['size'] and hashlib.sha256(raw).hexdigest()==f['sha256']
    print('PUBLIC_SOURCE_V1',len(m['files']),'/'+str(len(m['files'])),'PASS')
if __name__=='__main__':verify()
