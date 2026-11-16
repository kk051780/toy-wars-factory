#!/usr/bin/env python3
"""Cross-domain GQ499 deadline / GQ492 spectator static source contract.

Not an engine playtest. Validates source authority and lifecycle hooks on the
actual source-selected 31-script project plus the immutable original client.
"""
import argparse
import json
from pathlib import Path

HOST_ANCHORS = (
    'session.world.Name=mode.."_Arena"',
    'model.Name="Castle_"..entry.id',
    'player:SetAttribute("EGGRUMBLE_Eliminated",true)',
    'RoundReplay.schedule(session,session.closeRound)',
    'session.world:Destroy()',
    'Deadline.expire(session.rules,deadlineLease,os.clock(),deadlineId)',
    'ResultService.showIfFinished(session,queue,mode)',
    'session.refresh=function()',
)
CLIENT_ANCHORS = (
    "if not RunService:IsStudio() then return end",
    'lobby:FindFirstChild(mode .. "_Arena")',
    'candidate:FindFirstChild("Castle_" .. tostring(player.UserId))',
    'player:GetAttribute("EGGRUMBLE_Eliminated") ~= true',
    "if not ownArena then",
    "exitSpectate()",
    'player:GetAttributeChangedSignal("EGGRUMBLE_Eliminated"):Connect(refresh)',
    "RunService.Heartbeat:Connect(function(dt: number)",
)

def validate(host: str, client: str) -> dict:
    for marker in HOST_ANCHORS:
        if marker not in host:
            raise ValueError("RED_GQ492_HOST_DEADLINE_BRIDGE_MISSING " + marker)
    for marker in CLIENT_ANCHORS:
        if marker not in client:
            raise ValueError("RED_GQ492_SPECTATOR_BRIDGE_MISSING " + marker)
    if ':FireServer(' in client or ':InvokeServer(' in client:
        raise ValueError("RED_GQ492_SPECTATOR_REMOTE_AUTHORITY")
    return {
        "result": "SOURCE_CONTRACT_ONLY_NOT_STUDIO_VERIFIED",
        "host_deadline_anchors": len(HOST_ANCHORS),
        "spectator_recovery_anchors": len(CLIENT_ANCHORS),
        "original_only_studio": True,
        "actual_studio_2client": "NOT_TESTED",
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    from admit_spectator import source_map
    selected = source_map(json.loads(args.base.read_text(encoding="utf-8")), args.base)
    if len(selected) != 31 or "EGGRUMBLE_LobbyCastleModesPreview" not in selected:
        raise ValueError("RED_NOT_CURRENT_CANONICAL31")
    host_path, host_class = selected["EGGRUMBLE_LobbyCastleModesPreview"]
    if host_class != "Script":
        raise ValueError("RED_NOT_SINGLE_SERVER_HOST")
    result = validate(host_path.read_text(encoding="utf-8"),
                      args.original.read_text(encoding="utf-8"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print("GQ492_GQ499_DRAW_SPECTATOR_BRIDGE_SOURCE_ONLY_PASS")

if __name__ == "__main__":
    main()
