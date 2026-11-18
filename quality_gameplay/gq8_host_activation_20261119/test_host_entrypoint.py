#!/usr/bin/env python3
"""Regression: official 55 scripts contain an inert Host; fixed source only changes its Rojo class."""
import json,os
from pathlib import Path
from tempfile import TemporaryDirectory
from repair_host_entrypoint import inspect,flatten,repair,HOST
base=Path(os.getenv("GQ8_REAL55_BASELINE","artifacts/official55"))
assert inspect(base/"EGGRUMBLE_REAL55.rbxlx","ModuleScript")
try:inspect(base/"EGGRUMBLE_REAL55.rbxlx","Script")
except AssertionError as e:assert "P0_HOST_NOT_AUTOSTARTED" in str(e)
else:raise AssertionError("original P0 should fail")
with TemporaryDirectory() as d:
    out=Path(d)
    facts=repair(base,out)
    assert facts["source_bytes_changed"]==0 and facts["source_count"]==55
    before=flatten(json.loads((base/"EGGRUMBLE_REAL55.project.json").read_text()))
    after=flatten(json.loads((out/"EGGRUMBLE_REAL55_HOST_ACTIVE.project.json").read_text()))
    assert before.keys()==after.keys()
    assert [k for k in before if before[k]!=after[k]]==[HOST]
    for route in before:assert (base/before[route]).read_bytes()==(out/after[route]).read_bytes()
print("GQ8_ORIGINAL_REAL55_P0_RED_FIXED_SELECTED_SOURCE55_PASS")
