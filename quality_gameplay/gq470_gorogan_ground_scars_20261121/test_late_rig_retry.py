#!/usr/bin/env python3
"""Source-only GQ470 regression: late child construction and overlapping boss rigs.

This confirms the retry/lifecycle wiring. Roblox streaming/ART still need real Studio.
"""
from pathlib import Path

SRC = Path(__file__).with_name("EGGRUMBLE_GoroganGroundScars.client.luau")
TOKENS = (
    "local candidates: {[Model]: boolean} = {}",
    'if candidate:IsA("Model") and candidate.Name == MODEL_NAME then',
    'if instance:IsA("Model") and instance.Name == MODEL_NAME then',
    "candidates[candidate] = true",
    "candidates[instance] = true",
    "task.defer(track, instance)",
    "local removingConnection = Workspace.DescendantRemoving:Connect(function(instance)",
    "if instance:IsA(\"Model\") and candidates[instance] then",
    "candidates[instance] = nil",
    "release(instance)",
    "removingConnection:Disconnect()",
    "table.clear(candidates)",
    "if not ownerModel then",
    "for model in pairs(candidates) do",
    "if model:IsDescendantOf(Workspace) then",
    "track(model)",
    "if ownerModel then break end",
    "candidates[model] = nil",
    "for _, entry in pairs(tracked) do update(entry) end",
    "task.wait(UPDATE_SECONDS)",
    "MAX_PARTS = if LOW_TOUCH then 4 else 6",
    "MAX_DISTANCE = if LOW_TOUCH then 100 else 140",
    "if ownerModel or tracked[model] then return end",
    "clearParts(entry)",
    "script.Destroying:Connect(function()",
)

def validate(source: str) -> None:
    assert source.startswith("--!strict\n"), "RED_NOT_STRICT"
    for token in TOKENS:
        assert token in source, "RED_LATE_RETRY_REQUIRED_" + token
    assert source.count("Workspace:GetDescendants()") == 1, "RED_REPEAT_FULL_WORKSPACE_SCAN"
    assert source.count("Workspace.DescendantAdded:Connect") == 1, "RED_DOUBLE_ADD_LISTENER"
    assert source.count("Workspace.DescendantRemoving:Connect") == 1, "RED_DOUBLE_REMOVE_LISTENER"
    assert source.count("local candidates: {[Model]: boolean} = {}") == 1
    assert source.count('Instance.new("WedgePart")') == 1, "RED_EXTRA_PART_CREATOR"
    assert source.count("task.wait(UPDATE_SECONDS)") == 1, "RED_UPDATE_TIMER_CHANGED"
    assert source.count("if ownerModel or tracked[model] then return end") == 1, "RED_TWO_BOSS_OWNERS"
    a = source.index("local addedConnection = Workspace.DescendantAdded:Connect(")
    b = source.index("local removingConnection = Workspace.DescendantRemoving:Connect(")
    c = source.index("script.Destroying:Connect(function()")
    d = source.index("task.spawn(function()\n    while alive do")
    assert a < b < c < d, "RED_EVENT_LIFECYCLE_ORDER"
    loop = source[d:]
    assert loop.index("if not ownerModel then") < loop.index("for model in pairs(candidates) do")
    assert loop.index("track(model)") < loop.index("for _, entry in pairs(tracked) do update(entry) end"), "RED_LATE_RETRY_AFTER_RENDER"
    assert loop.index("if ownerModel then break end") < loop.index("for _, entry in pairs(tracked) do update(entry) end")
    assert "Workspace:GetDescendants()" not in loop, "RED_FULL_SCAN_PER_TICK"
    assert "Instance.new(" not in loop, "RED_NEW_PART_LOOP_SCOPE"
    removing = source[b:c]
    assert removing.index("candidates[instance] = nil") < removing.index("release(instance)"), "RED_PENDING_LEAK"
    cleanup = source[c:d]
    assert cleanup.index("addedConnection:Disconnect()") < cleanup.index("folder:Destroy()")
    assert cleanup.index("removingConnection:Disconnect()") < cleanup.index("folder:Destroy()")
    assert cleanup.index("table.clear(candidates)") < cleanup.index("folder:Destroy()")

def run() -> int:
    src = SRC.read_text(encoding="utf-8")
    validate(src)
    mutations = [
        ("local candidates: {[Model]: boolean} = {}", "-- model cache removed"),
        ("candidates[candidate] = true", "-- ignore initial rig"),
        ("candidates[instance] = true", "-- ignore in-flight rig"),
        ("task.defer(track, instance)", "-- no initial queued attempt"),
        ("Workspace.DescendantRemoving:Connect", "Workspace.DescendantAdded:Connect"),
        ("candidates[instance] = nil", "-- retain unloaded rig"),
        ("release(instance)", "-- never release unloaded boss"),
        ("removingConnection:Disconnect()", "-- leak removal listener"),
        ("table.clear(candidates)", "-- retain old candidates"),
        ("if not ownerModel then", "if false then"),
        ("for model in pairs(candidates) do", "for model in pairs(tracked) do"),
        ("if model:IsDescendantOf(Workspace) then", "if true then"),
        ("if ownerModel then break end", "-- no boss cap"),
        ("candidates[model] = nil", "-- leak streamed rig"),
        ("for _, entry in pairs(tracked) do update(entry) end", "-- visuals never updated"),
        ("task.wait(UPDATE_SECONDS)", "task.wait(0)"),
        ("if ownerModel or tracked[model] then return end", "if false then return end"),
        ("then 4 else 6", "then 40 else 60"),
    ]
    for i, (before, after) in enumerate(mutations, 1):
        assert before in src, f"RED_NOOP_MUTATION_{i}"
        changed = src.replace(before, after, 1)
        assert changed != src, f"RED_NO_CHANGE_{i}"
        try:
            validate(changed)
        except AssertionError:
            continue
        raise AssertionError(f"RED_ACCEPTED_LATE_RIG_MUTATION_{i}")
    print(f"GQ470_GOROGAN_LATE_CHILD_AND_REPLACEMENT_SOURCE_{len(mutations)}_MUTANTS_PASS_ENGINE_NOT_TESTED")
    return len(mutations)

if __name__ == "__main__":
    run()
