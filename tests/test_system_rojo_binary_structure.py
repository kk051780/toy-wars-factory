"""Test-first RBXL v0 header counts and chunk ordering; does not load a real place."""
import struct
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import rojo_rbxl_gate as gate

def binary(kinds=("INST","PROP","PRNT"), declared_classes=1, oversize_chunk=None):
    out = gate.MAGIC + struct.pack("<HIIQ", 0, declared_classes, 5, 0)
    for i, kind in enumerate((*kinds, "END")):
        body = b"</roblox>" if kind == "END" else b"x"
        compressed = 0
        uncompressed = len(body)
        if oversize_chunk is not None and i == oversize_chunk:
            compressed = len(body)
            uncompressed = gate.MAX_BYTES + 1
        out += struct.pack("<4sIII", kind.encode().ljust(4, b"\0"),
                           compressed, uncompressed, 0) + body
    return out

class BinaryStructureTests(unittest.TestCase):
    def valid(self,kinds,classes=1):
        data=binary(kinds,classes)
        got=gate.inspect(data)
        self.assertEqual(got["chunk_types"],[*kinds,"END"])
        self.assertFalse(got["engine_verified"])
        self.assertFalse(got["source_attested"])
    def invalid(self,kinds,classes=1):
        with self.assertRaises(ValueError):
            gate.inspect(binary(kinds,classes))

    def test_one_class_count_matches(self):
        self.valid(("INST","PROP","PRNT"))
    def test_two_instances_chunks_match_header(self):
        self.valid(("INST","INST","PROP","PRNT"),2)
    def test_optional_metadata_strings_before_instances(self):
        self.valid(("META","SSTR","INST","PROP","PRNT"))
    def test_optional_shared_strings_without_meta(self):
        self.valid(("SSTR","INST","PROP","PRNT"))

    def test_header_overdeclares_instance_classes(self):
        self.invalid(("INST","PROP","PRNT"),2)
    def test_header_underdeclares_instance_classes(self):
        self.invalid(("INST","INST","PROP","PRNT"),1)
    def test_prop_before_first_inst_is_denied(self):
        self.invalid(("PROP","INST","PRNT"))
    def test_inst_after_props_is_denied(self):
        self.invalid(("INST","PROP","INST","PRNT"),2)
    def test_prnt_before_prop_is_denied(self):
        self.invalid(("INST","PRNT","PROP"))
    def test_prop_after_prnt_is_denied(self):
        self.invalid(("INST","PRNT","PROP","PROP"))
    def test_inst_after_prnt_is_denied(self):
        self.invalid(("INST","PROP","PRNT","INST"),2)
    def test_meta_after_inst_is_denied(self):
        self.invalid(("INST","META","PROP","PRNT"))
    def test_sstr_after_prop_is_denied(self):
        self.invalid(("INST","PROP","SSTR","PRNT"))
    def test_sstr_before_meta_is_denied(self):
        self.invalid(("SSTR","META","INST","PROP","PRNT"))
    def test_bounded_decompression_header_is_required(self):
        with self.assertRaises(ValueError):
            gate.inspect(binary(oversize_chunk=0))

if __name__=="__main__":
    unittest.main()
