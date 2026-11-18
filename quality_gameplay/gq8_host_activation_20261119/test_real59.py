#!/usr/bin/env python3
"""Negative original Real59 host test + byte-exact 59-source repair regression."""
import json,os
from pathlib import Path
from tempfile import TemporaryDirectory
from repair_real59 import assemble,verify,flat,HOST,PROJECT,PLACE
base=Path(os.getenv("GQ8_REAL59_BASELINE","artifacts/official59"))
verify(base/PLACE,"ModuleScript")
try:verify(base/PLACE,"Script")
except AssertionError as e:assert "P0_HOST_NOT_STARTED" in str(e)
else:raise AssertionError("expected original real59 P0 failure")
with TemporaryDirectory() as d:
    out=Path(d)
    evidence=assemble(base,out)
    before=flat(json.loads((base/PROJECT).read_text()))
    after=flat(json.loads((out/"EGGRUMBLE_REAL59_HOST_ACTIVE.project.json").read_text()))
    assert len(before)==len(after)==59
    assert [key for key in before if before[key]!=after[key]]==[HOST]
    assert (out/before[HOST]).read_bytes()==(out/after[HOST]).read_bytes()
    assert evidence["source_bytes_modified"]==0
print("GQ8_OFFICIAL59_INACTIVE_HOST_NEGATIVE_AND_SOURCE59_EXACT_PASS")
