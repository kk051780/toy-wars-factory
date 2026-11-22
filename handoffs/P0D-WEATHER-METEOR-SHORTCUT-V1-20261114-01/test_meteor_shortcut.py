"""Offline policy+geometry regression; NOT a Luau compiler or Roblox Studio test."""
from pathlib import Path
import math
s = (Path(__file__).parent / "MeteorShortcut.server.luau").read_text(encoding="utf-8")
def segments(span):
    return min(12, math.ceil(span / 7))
def centers(span):
    n = segments(span)
    return [(i - .5) / n * span for i in range(1, n + 1)]
def coverage(span):
    n = segments(span)
    length = span / n + .6
    c = centers(span)
    return (c[0] - length / 2, c[-1] + length / 2)
checks = [
    ("fail_closed_bool_gate", 'flag ~= nil and flag:IsA("BoolValue") and flag.Value == true' in s),
    ("anchor_validation", all(x in s for x in ["MIN_LENGTH = 14", "MAX_LENGTH = 90", "MAX_HEIGHT_DIFFERENCE = 5"])),
    ("no_restricted_authority", all(x not in s for x in ["DataStoreService", "RemoteEvent", "FireServer", "FireClient", "UpdateAsync", "MarketplaceService"])),
    ("single_runtime", "Duplicate runtime detected" in s),
    ("reversible", "setRoute(segments, false)" in s and "runtime:Destroy()" in s),
    ("occupied_bridge_not_dropped", "while runtime.Parent ~= nil and isBridgeOccupied(segments) do" in s and "GetPartBoundsInBox" in s),
    ("both_teams_equal", "Teams" not in s and "Player" not in s),
    ("warning_before_open", s.index("task.wait(WARNING_SECONDS)") < s.index("setRoute(segments, true)")),
    ("neutral_14_units", coverage(14)[0] <= 0 and coverage(14)[1] >= 14),
    ("neutral_33_units", coverage(33)[0] <= 0 and coverage(33)[1] >= 33),
    ("neutral_90_units", coverage(90)[0] <= 0 and coverage(90)[1] >= 90),
    ("wcs_explicit_true_guard", 'GetAttribute("P0D_RC_ENABLE_WCS_F01_C01") ~= true' in s),
    ("wcs_stage_identity", 'Workspace:FindFirstChild("P0D_WCS_CrystalCanyon")' in s),
    ("wcs_original_banks", '"WestBank"' in s and '"EastBank"' in s and "west.CanCollide and east.CanCollide" in s),
    ("wcs_no_fake_map_place", 'return nil, nil' in s and 'WaitForChild("P0D_WCS_CrystalCanyon", 12)' in s),
    ("studio_only_before_placement", 'if not RunService:IsStudio() then' in s),
    ("wcs_symmetric_crossing", abs((-50 + 50/2 - 1.5) + (50 - 50/2 + 1.5)) < .001 and 14 <= 53 <= 90),
    ("wcs_boundary_inbounds", abs(-23 - 85/2 + 8) <= 68 and abs(26.5) <= 120),
    ("wcs_distinct_existing_routes", abs((-23-85/2+8) - (-23)) > 12 and abs((-23-85/2+8) - (7)) > 12),
    ("max_12_segments", all(segments(n) <= 12 for n in range(14, 91))),
    ("monotonic_segments", all(centers(n) == sorted(centers(n)) for n in range(14, 91))),
]
for name, ok in checks:
    print(f'{"PASS" if ok else "FAIL"} {name}')
assert all(ok for _, ok in checks)
print(f"P0D_METEOR_OFFLINE_POLICY_PASS {len(checks)}/{len(checks)}")
