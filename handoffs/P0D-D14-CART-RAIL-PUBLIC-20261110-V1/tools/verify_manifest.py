"""Read only check SHA/size of a restored private D14 reference packet."""
import hashlib, json, pathlib, sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
M=ROOT/'BUILD_MANIFEST.json'

def check():
    data=json.loads(M.read_text('utf-8'))
    assert data['game_id']=='TRAP_RAIDERS' and data['work_id']=='p0d-siege-v19'
    assert data['packet_id']=='P0D-D14-CART-RAIL-MOTION-20261110-02B'
    paths=set()
    for ent in data['files']:
        p=ent['path']; assert p not in paths
        paths.add(p)
        assert '..' not in pathlib.PurePosixPath(p).parts and not p.startswith('/')
        f=ROOT/p; assert f.is_file() and not f.is_symlink()
        b=f.read_bytes(); assert len(b)==ent['size'] and hashlib.sha256(b).hexdigest()==ent['sha256']
    return len(paths)
if __name__=='__main__':
    try:print('MANIFEST_PASS:',check(),'files')
    except Exception as e:print('MANIFEST_BLOCKED:',type(e).__name__);sys.exit(2)
