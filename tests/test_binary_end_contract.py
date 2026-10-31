"""Additional boundary checks from rbx-dom's binary model v0 specification.

These synthetic bytes prove only static framing validation, NEVER actual Rojo or
Roblox Studio engine acceptance or external authentication.
"""
from pathlib import Path
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import rojo_rbxl_gate as gate

MAGIC=b"</roblox>"

def packet(*, payload=MAGIC, compressed=0, uncompressed=None, kinds=None, trailer=b''):
    if kinds is None:
        kinds=[('INST',b'class'),('PROP',b'props'),('PRNT',b'parents')]
    content=gate.MAGIC+struct.pack('<HIIQ',0,3,5,0)
    for name,body in kinds:
        content+=struct.pack('<4sIII',name.encode().ljust(4,b'\0'),0,len(body),0)+body
    if uncompressed is None:uncompressed=len(payload)
    content+=struct.pack('<4sIII',b'END\0',compressed,uncompressed,0)+payload
    return content+trailer

class BinaryEndContractTests(unittest.TestCase):
    def test_canonical_end_payload_accepted(self):
        report=gate.inspect(packet())
        self.assertEqual(report['chunk_types'][-1],'END')
        self.assertFalse(report['engine_verified'])
        self.assertFalse(report['published'])
    def test_empty_end_payload_refused(self):
        with self.assertRaises(ValueError):gate.inspect(packet(payload=b''))
    def test_different_end_payload_refused(self):
        with self.assertRaises(ValueError):gate.inspect(packet(payload=b'\0'*9))
    def test_trailing_data_after_correct_end_refused(self):
        with self.assertRaises(ValueError):gate.inspect(packet(trailer=b'junk'))
    def test_truncated_end_data_refused(self):
        with self.assertRaises(ValueError):gate.inspect(packet()[:-1])
    def test_end_chunk_cannot_be_compressed(self):
        with self.assertRaises(ValueError):gate.inspect(packet(compressed=len(MAGIC)))
    def test_end_chunk_length_metadata_is_exact(self):
        with self.assertRaises(ValueError):gate.inspect(packet(uncompressed=123))
    def test_duplicate_parent_chunk_refused(self):
        kinds=[('INST',b'1'),('PROP',b'2'),('PRNT',b'3'),('PRNT',b'4')]
        with self.assertRaises(ValueError):gate.inspect(packet(kinds=kinds))
    def test_duplicate_meta_chunk_refused(self):
        kinds=[('META',b'a'),('META',b'b'),('INST',b'1'),('PROP',b'2'),('PRNT',b'3')]
        with self.assertRaises(ValueError):gate.inspect(packet(kinds=kinds))
    def test_duplicate_sstr_chunk_refused(self):
        kinds=[('SSTR',b'a'),('SSTR',b'b'),('INST',b'1'),('PROP',b'2'),('PRNT',b'3')]
        with self.assertRaises(ValueError):gate.inspect(packet(kinds=kinds))
if __name__=='__main__':unittest.main()
