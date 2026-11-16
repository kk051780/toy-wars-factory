#!/usr/bin/env python3
"""Patch exactly one verified lifecycle defect in an isolated 26-source RC candidate.

The author host's last-human PlayerRemoving invokes scene.closeRound(true)
from RoundReplay.abandonIfEmpty while ACTIVE, but closeRound() rejected every
non-FINISHED session, leaving the old arena/queue indefinitely occupied.
Never alter original author/quality source: patch only generated private output.
"""
import argparse
import hashlib
import json
from pathlib import Path

OLD = '''  session.closeRound=function()
   if sessions[mode]~=session or session.rules.phase~="FINISHED" then return end
'''
NEW = '''  session.closeRound=function(abandoned:boolean?)
   if sessions[mode]~=session then return end
   if session.rules.phase~="FINISHED" then
    -- The last human disconnected: no winner or result banner is invented.
    -- Refuse external/stale callers and preserve matches with remaining humans.
    if abandoned~=true or session.rules.phase~="ACTIVE" then return end
    for _,entry in ipairs(session.roster) do
     if not entry.isAI then
      local live=Players:GetPlayerByUserId(tonumber(entry.id) or -1)
      if live and joined[live.UserId]==mode then return end
     end
    end
   end
'''

# Independently proven original caller and identity fences; if author updates,
# fail the patch and reconcile rather than silently overriding new behavior.
REQUIRED = (
    'RoundReplay.abandonIfEmpty(scene,joined,function()',
    'scene.closeRound(true)',
    'if sessions[mode]~=session then return end',
    'sessions[mode]=nil',
    'queues[mode]={}',
    'queueEpoch[mode]+=1',
)

def apply(source: str) -> str:
    if source.count(OLD) != 1:
        raise ValueError("author lifecycle anchor drift: require exact once")
    for marker in REQUIRED[0:2] + REQUIRED[3:]:
        if source.count(marker) != 1:
            raise ValueError(f"author lifecycle caller/cleanup changed: {marker!r}")
    updated = source.replace(OLD, NEW, 1)
    if updated.replace(NEW, OLD, 1) != source:
        raise ValueError("unrelated host code changed")
    return updated

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--host", required=True, type=Path)
    p.add_argument("--receipt", required=True, type=Path)
    args = p.parse_args()
    before = args.host.read_text(encoding="utf-8")
    after = apply(before)
    args.host.write_text(after, encoding="utf-8")
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    assert receipt["status"] == "SOURCE_ONLY_NOT_OFFICIAL_RC"
    name = "EGGRUMBLE_LobbyCastleModesPreview"
    assert receipt["source_sha256"][name] == hashlib.sha256(before.encode()).hexdigest()
    receipt["source_sha256"][name] = hashlib.sha256(after.encode()).hexdigest()
    receipt["quality_overrides"].append("EGGRUMBLE_LobbyCastleModesPreview.last_human_abandon_ONLY")
    receipt["abandon_fix"] = {
        "issue": "LAST_HUMAN_ACTIVE_MATCH_NOT_CLOSED",
        "original_host_sha256": hashlib.sha256(before.encode()).hexdigest(),
        "private_patched_host_sha256": hashlib.sha256(after.encode()).hexdigest(),
        "test_scope": "source_patch_only; engine behavior unverified",
        "rollback": "restore original composed host",
    }
    args.receipt.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("GQ_EMPTY_HUMAN_RECOVERY_SOURCE_PATCH_PASS")

if __name__ == "__main__":
    main()
