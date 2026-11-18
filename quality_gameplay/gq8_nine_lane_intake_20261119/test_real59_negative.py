#!/usr/bin/env python3
"""Hostile mutation tests against a genuine SAME-HEAD Real59 built Place."""
import argparse
import copy
import json
import tempfile
from pathlib import Path
from verify_real59 import verify

p = argparse.ArgumentParser()
p.add_argument("--place59", type=Path, required=True)
p.add_argument("--off55", type=Path, required=True)
p.add_argument("--receipt", type=Path, required=True)
p.add_argument("--expected-head", required=True)
args = p.parse_args()
good = json.loads(args.receipt.read_text(encoding="utf8"))
verified = verify(args.place59, args.receipt, args.off55, args.expected_head)
assert verified["source_count"] == 59 and verified["nine_source_domains_selected"] == 9

def blocked(label, change):
    fake = copy.deepcopy(good)
    change(fake)
    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "hostile.json"
        path.write_text(json.dumps(fake), encoding="utf8")
        try:
            verify(args.place59, path, args.off55, args.expected_head)
        except ValueError as error:
            assert str(error).startswith("RED_"), (label, error)
        else:
            raise AssertionError("RED_MUTANT_ACCEPTED_" + label)

blocked("fake_formal_rc", lambda x: x.update(official_rc_adopted=False))
blocked("stale_head", lambda x: x.update(candidate_head="0" * 40))
blocked("fake_publish", lambda x: x.update(roblox_published=True))
blocked("source_hash", lambda x: x["on_sources"][0].update(sha256="0" * 64))
blocked("duplicate_route", lambda x: x["on_sources"][1].update(route=x["on_sources"][0]["route"]))
blocked("changed_off55", lambda x: x["off_sources"][0].update(bytes=x["off_sources"][0]["bytes"]+1))
blocked("fake_baseline", lambda x: x.update(baseline55_exact_sources_unchanged=False))
print("GQ8_REAL59_SEVEN_HOSTILE_MUTANTS_DETECTED_SOURCE_ONLY_PASS")
