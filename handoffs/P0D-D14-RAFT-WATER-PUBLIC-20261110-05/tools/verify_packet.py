"""Read-only SHA/size/CRC/path validation of a sealed P0-D source archive (no extraction)."""
import hashlib
import io
import json
import stat
import zipfile
from pathlib import PurePosixPath

MAX_FILES=128
MAX_UNCOMPRESSED=2_000_000

def verify(data: bytes):
    if not isinstance(data,bytes) or len(data)>2_000_000:
        raise ValueError('ZIP_INPUT_LIMIT')
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=z.infolist()
        if not infos or len(infos)>MAX_FILES:raise ValueError('ZIP_COUNT')
        names=set()
        total=0
        by_name={}
        for info in infos:
            name=info.filename
            if not name or name.startswith(('/','\\')) or '\\' in name or ':' in name or info.is_dir():
                raise ValueError('ZIP_UNSAFE_PATH')
            parts=name.split('/')
            if any(x in ('','.','..') for x in parts):raise ValueError('ZIP_UNSAFE_PATH')
            low=name.casefold()
            if low in names:raise ValueError('ZIP_COLLISION')
            names.add(low)
            mode=info.external_attr>>16
            if mode and stat.S_IFMT(mode) not in (0,stat.S_IFREG):raise ValueError('ZIP_SPECIAL_ENTRY')
            if info.flag_bits&1:raise ValueError('ZIP_ENCRYPTED')
            total+=info.file_size
            if total>MAX_UNCOMPRESSED:raise ValueError('ZIP_SIZE')
            by_name[name]=info
        if 'BUILD_MANIFEST.json' not in by_name:raise ValueError('MISSING_MANIFEST')
        if z.testzip() is not None:raise ValueError('ZIP_CRC')
        manifest_bytes=z.read('BUILD_MANIFEST.json')
        def object_pairs(pairs):
            out={}
            for k,v in pairs:
                if k in out:raise ValueError('DUPLICATE_JSON')
                out[k]=v
            return out
        doc=json.loads(manifest_bytes.decode('utf-8'),object_pairs_hook=object_pairs)
        if not isinstance(doc,dict) or doc.get('packet_id')!='P0D-D14-RAFT-WATER-MOTION-20261110-03':raise ValueError('MANIFEST_ID')
        items=doc.get('files')
        if not isinstance(items,list) or len(items)!=len(infos)-1:raise ValueError('MANIFEST_COUNT')
        seen=set()
        for f in items:
            if not isinstance(f,dict) or sorted(f)!=['path','sha256','size']:raise ValueError('MANIFEST_SHAPE')
            path=f['path']
            if path in seen or path not in by_name or path=='BUILD_MANIFEST.json':raise ValueError('MANIFEST_FILE')
            seen.add(path)
            actual=z.read(path)
            if f['size']!=len(actual) or f['sha256']!=hashlib.sha256(actual).hexdigest():raise ValueError('MANIFEST_SHA')
        if seen != set(by_name)-{'BUILD_MANIFEST.json'}:raise ValueError('MANIFEST_MISSING_FILE')
        return {'entries':len(infos),'source_entries':len(items),'manifest_sha256':hashlib.sha256(manifest_bytes).hexdigest(),'zip_sha256':hashlib.sha256(data).hexdigest()}
