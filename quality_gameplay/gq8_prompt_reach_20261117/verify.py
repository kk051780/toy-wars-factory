#!/usr/bin/env python3
"""Exact original-author source-lock and reversible single-Guard selector."""
import argparse
import hashlib
from pathlib import Path

EXPECTED_GIT_BLOB = "ac51ce2077814c7509b8eaf6dafbd05b04a9a1fe"
OLD = [
    "local function positionValid(actor:Player,part:BasePart):boolean\n",
    " if not actor.Parent or not part.Parent then return false end\n",
    " if (near-root.Position).Magnitude>MAX_DISTANCE+EXCESS_RADIUS then return false end\n",
    " if not positionValid(actor,part) then return false end\n",
]
NEW = [
    "-- Server-owned prompt parameters are the authorization boundary, not a global\n-- 16-stud allowance that may exceed the actual gate's configured reach.\nlocal function configuredReach(part:BasePart,verb:string):number?\n local selected:ProximityPrompt?=nil\n for _,child in ipairs(part:GetChildren()) do\n  if child:IsA(\"ProximityPrompt\") and child.Enabled and child.ActionText==verb then\n   -- A duplicate action on the same part is ambiguous: fail closed.\n   if selected then return nil end\n   selected=child\n  end\n end\n if not selected then return nil end\n local distance=selected.MaxActivationDistance\n if type(distance)~=\"number\" or distance~=distance or distance<=0 then return nil end\n return math.min(MAX_DISTANCE,distance)\nend\nlocal function positionValid(actor:Player,part:BasePart,verb:string):boolean\n",
    " if not actor.Parent or not part.Parent then return false end\n local reach=configuredReach(part,verb)\n if not reach then return false end\n",
    " if (near-root.Position).Magnitude>reach+EXCESS_RADIUS then return false end\n",
    " if not positionValid(actor,part,verb) then return false end\n",
]

def select(original: str) -> str:
    result = original
    for before, after in zip(OLD, NEW):
        assert result.count(before) == 1, ("AMBIGUOUS_SOURCE", before)
        result = result.replace(before, after, 1)
    return result

def blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def check(original_path: Path, selected_path: Path) -> None:
    data = original_path.read_bytes()
    assert blob_sha(data) == EXPECTED_GIT_BLOB, "PINNED_ORIGINAL_SOURCE_CHANGED"
    original = data.decode("utf-8")
    chosen = selected_path.read_text(encoding="utf-8")
    assert chosen == select(original), "NON_AUTHOR_SOURCE_OR_SCOPE_CHANGED"
    reverted = chosen
    for before, after in reversed(list(zip(OLD, NEW))):
        assert reverted.count(after) == 1, "NONEXACT_ROLLBACK"
        reverted = reverted.replace(after, before, 1)
    assert reverted == original, "OFF_MUST_MATCH_AUTHOR_BYTE_EXACT"
    assert "local reach=configuredReach(part,verb)" in chosen
    assert "if not reach then return false end" in chosen
    assert "if selected then return nil end" in chosen
    assert "reach+EXCESS_RADIUS" in chosen
    assert "MAX_DISTANCE+EXCESS_RADIUS" not in chosen
    assert "if not positionValid(actor,part,verb)" in chosen
    print("GQ8_PROMPT_REACH_SINGLE_GUARD_SOURCE_LOCK_ROLLBACK_PASS")

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--selected", type=Path, required=True)
    a = p.parse_args()
    check(a.original, a.selected)

if __name__ == "__main__":
    main()
