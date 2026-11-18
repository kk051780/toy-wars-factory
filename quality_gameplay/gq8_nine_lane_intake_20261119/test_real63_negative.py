#!/usr/bin/env python3
"""Adversarial receipt tests for immutable current official Real63 source selection."""
from __future__ import annotations
import argparse, copy, json, tempfile
from pathlib import Path
from verify_real63 import verify

p=argparse.ArgumentParser()
for key in ("real62", "real63", "off62", "receipt"):
    p.add_argument("--" + key, type=Path, required=True)
p.add_argument("--expected-head", required=True)
a=p.parse_args()
original=json.loads(a.receipt.read_text(encoding="utf8"))
assert verify(a.real62,a.real63,a.off62,a.receipt,a.expected_head)["source_count"]==63

def denied(label,mutate):
    data=copy.deepcopy(original)
    mutate(data)
    with tempfile.TemporaryDirectory() as td:
        target=Path(td)/"bad.json"
        target.write_text(json.dumps(data),encoding="utf8")
        try: verify(a.real62,a.real63,a.off62,target,a.expected_head)
        except ValueError as e: assert str(e).startswith("RED_"),(label,e)
        else: raise AssertionError("MUTATION_WAS_ACCEPTED_"+label)

denied("fake_head",lambda d:d.update(candidate_git_head="f"*40))
denied("fake_formal",lambda d:d.update(official_rc_adopted=False))
denied("fake_untested_mobile",lambda d:d.update(android15min="PASS"))
denied("fake_paid",lambda d:d.update(robuxtx_enabled=True))
denied("host_disabled",lambda d:d.update(host_original_class="ModuleScript"))
denied("second_damage",lambda d:d.update(direct_damage_site_added=1))
denied("source_hash",lambda d:d["on_sources"][0].update(sha256="0"*64))
denied("duplicate",lambda d:d["on_sources"][1].update(route=d["on_sources"][0]["route"]))
print("GQ8_REAL63_EIGHT_ADVERSARIAL_PROVENANCE_MUTATIONS_REJECTED")
