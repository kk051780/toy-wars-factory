"""Source-exact negative QA for owner-photo SevenRoleCombat:401 crash."""
from __future__ import annotations
import hashlib
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from patch_real69_userid import PINNED_SHA256, BUG, FIX, from_real69_zip, patch_source


def verify(archive: Path) -> None:
    original = from_real69_zip(archive)
    assert hashlib.sha256(original).hexdigest() == PINNED_SHA256
    patched = patch_source(original)
    assert patched != original and len(patched.splitlines()) == 1513
    assert patched.count(FIX.encode()) == 1
    assert BUG.encode() not in patched
    assert patched.count(b'InvulRuntime.filterDamage(') == original.count(b'InvulRuntime.filterDamage(')
    # Same function output and server-controlled damage path, just correct Player identity.
    for mutant in (original.replace(BUG.encode(), FIX.encode()), original + b'\n-- drift\n', patched):
        try:
            patch_source(mutant)
        except AssertionError:
            pass
        else:
            raise AssertionError("FAIL_OPEN_DRIFT_MUTANT")
    print("PASS: pinned REAL69 69/69 source inventory; 1-line fix; 3 drift mutations rejected")
    print("candidate_sha256=" + hashlib.sha256(patched).hexdigest())


if __name__ == "__main__":
    assert len(sys.argv) == 2, "usage: python test_real69_userid.py REAL69_20261120.zip"
    verify(Path(sys.argv[1]))
