#!/usr/bin/env python3
"""Seven adversarial source/commerce/Host mutations against official Real62 receipt."""
import argparse, copy, json, tempfile
from pathlib import Path
from verify_real62 import verify

p=argparse.ArgumentParser()
for name in ("active59","real62","off59","receipt"):
    p.add_argument("--"+name,type=Path,required=True)
p.add_argument("--expected-head",required=True)
a=p.parse_args()
source=json.loads(a.receipt.read_text(encoding="utf8"))
assert verify(a.active59,a.real62,a.off59,a.receipt,a.expected_head)["source_count"]==62

def rejected(name,mutate):
    data=copy.deepcopy(source)
    mutate(data)
    with tempfile.TemporaryDirectory() as temp:
        path=Path(temp)/"negative.json"
        path.write_text(json.dumps(data))
        try:
            verify(a.active59,a.real62,a.off59,path,a.expected_head)
        except ValueError as exc:
            assert str(exc).startswith("RED_"),(name,exc)
        else:
            raise AssertionError("MUTANT_ACCEPTED_"+name)

rejected("fake_official",lambda d:d.update(official_rc_adopted=False))
rejected("stale_sha",lambda d:d.update(tested_head="f"*40))
rejected("Host_module",lambda d:d.update(host_class="ModuleScript"))
rejected("fake_paid_trade",lambda d:d.update(paid_trading=True))
rejected("source_hash",lambda d:d["on_sources"][0].update(sha256="0"*64))
rejected("duplicate_ledger",lambda d:d["on_sources"][1].update(route=d["on_sources"][0]["route"]))
rejected("false_mobile",lambda d:d.update(android="PASS"))
print("GQ8_REAL62_SEVEN_HOSTILE_SOURCE_AND_PRODUCT_CLAIM_MUTATIONS_REJECTED")
