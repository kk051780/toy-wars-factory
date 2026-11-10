import importlib.util, io, json, pathlib, stat, unittest, zipfile, hashlib
P=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('verify_module',P/'tools/verify_packet.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

def pack(entries):
    f=io.BytesIO()
    with zipfile.ZipFile(f,'w') as z:
        for name,content in entries:
            z.writestr(name,content)
    return f.getvalue()

class SecureArchive(unittest.TestCase):
 def test_missing_manifest(self):
    with self.assertRaises(ValueError):v.verify(pack([('a','a'),('b','b'),('c','c'),('d','d'),('e','e')]))
 def test_absolute(self):
    with self.assertRaises(ValueError):v.verify(pack([('/a','a'),('b','b'),('c','c'),('d','d'),('BUILD_MANIFEST.json','{}')]))
 def test_zip_slip(self):
    with self.assertRaises(ValueError):v.verify(pack([('../a','a'),('b','b'),('c','c'),('d','d'),('BUILD_MANIFEST.json','{}')]))
 def test_windows_slash(self):
    with self.assertRaises(ValueError):v.verify(pack([('a\\b','a'),('b','b'),('c','c'),('d','d'),('BUILD_MANIFEST.json','{}')]))
 def test_duplicate_name(self):
    with self.assertWarns(UserWarning):
        blob=pack([('a','x'),('a','z'),('c','c'),('d','d'),('BUILD_MANIFEST.json','{}')])
    with self.assertRaises(ValueError):v.verify(blob)
 def test_case_duplicate(self):
    with self.assertRaises(ValueError):v.verify(pack([('A','x'),('a','z'),('c','c'),('d','d'),('BUILD_MANIFEST.json','{}')]))
 def test_drive_path(self):
    with self.assertRaises(ValueError):v.verify(pack([('C:one','x'),('b','y'),('c','c'),('d','d'),('BUILD_MANIFEST.json','{}')]))
 def test_dot(self):
    with self.assertRaises(ValueError):v.verify(pack([('a/./b','x'),('b','y'),('c','c'),('d','d'),('BUILD_MANIFEST.json','{}')]))
 def test_bomb(self):
    with self.assertRaises(ValueError):v.verify(pack([('a',b'a'*160_000),('b','y'),('c','c'),('d','d'),('BUILD_MANIFEST.json','{}')]))
 def test_empty_zip(self):
    with self.assertRaises(ValueError):v.verify(b'')
 def test_wrong_manifest_packet(self):
    m={'schema_version':1,'packet_id':'bad','classification':'REFERENCE_ONLY','files':{}}
    with self.assertRaises(ValueError):v.verify(pack([('a','x'),('b','y'),('c','c'),('d','d'),('BUILD_MANIFEST.json',json.dumps(m))]))
 def test_invalid_sha(self):
    data={'a':b'x','b':b'y','c':b'c','d':b'd'}
    m={'schema_version':1,'packet_id':v.PACKET_ID,'classification':'REFERENCE_ONLY','files':{n:{'size_bytes':len(b),'sha256':'0'*64} for n,b in data.items()}}
    with self.assertRaises(ValueError):v.verify(pack(list(data.items())+[('BUILD_MANIFEST.json',json.dumps(m))]))
 def test_valid(self):
    data={'a':b'x','b':b'y','c':b'c','d':b'd'}
    m={'schema_version':1,'packet_id':v.PACKET_ID,'classification':'REFERENCE_ONLY','files':{n:{'size_bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()} for n,b in data.items()}}
    info=v.verify(pack(list(data.items())+[('BUILD_MANIFEST.json',json.dumps(m))]))
    self.assertEqual(info['files'],4)
    self.assertEqual(info['studio_qa'],'NOT_TESTED')

if __name__=='__main__':unittest.main()
