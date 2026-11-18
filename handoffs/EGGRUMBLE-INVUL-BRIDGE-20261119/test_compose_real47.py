#!/usr/bin/env python3
import tempfile
import unittest
from pathlib import Path
from test_compose_real46 import sample
from compose_real46 import flatten
from compose_real47 import make,NEW,HERO,RUNTIME_ROUTE,RUNTIME46_BLOB,exact_blob
RUNTIME46=Path("_prior830/handoffs/EGGRUMBLE-INVUL-BRIDGE-20261119/EGGRUMBLE_InvulRuntime.luau")
class CounterStack(unittest.TestCase):
 def test_real_source_selection_47_previous46_off():
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);original44,policy,_=sample(root)
   target=root/"new47"/"ON47.project.json"
   make(original44,policy,RUNTIME46,target)
   _,src47=flatten(target)
   _,src46=flatten(target.parent/"source46"/"ON46.project.json")
   _,src44=flatten(original44)
   self.assertEqual((len(src44),len(src46),len(src47)),(44,46,47))
   self.assertEqual(exact_blob(src46[RUNTIME_ROUTE].read_bytes()),RUNTIME46_BLOB)
   self.assertEqual(len(set(src47)-set(src46)),1)
   self.assertIn(NEW,src47)
   for route,source in src46.items():
    if route not in (HERO,RUNTIME_ROUTE):
     self.assertEqual(source.read_bytes(),src47[route].read_bytes())
   self.assertEqual(src47[HERO].read_text().count("atHum:TakeDamage(realDamage)"),1)
   self.assertEqual(src47[HERO].read_text().count("EGGRUMBLE_VisibleCounterTell"),1)
   self.assertEqual(src47[RUNTIME_ROUTE].read_text().count("Counter.react("),1)
   self.assertEqual(src47[NEW].read_text().count("session.swarm.damageFromPlayer("),1)
 def test_reject_runtime46_mutation():
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);original44,policy,_=sample(root)
   fake=root/"badRuntime.luau"
   fake.write_bytes(RUNTIME46.read_bytes()+b"-- extra")
   with self.assertRaisesRegex(ValueError,"RED_PRIOR46_RUNTIME_BLOB"):
    make(original44,policy,fake,root/"new47"/"ON47.project.json")
if __name__=="__main__":unittest.main()
