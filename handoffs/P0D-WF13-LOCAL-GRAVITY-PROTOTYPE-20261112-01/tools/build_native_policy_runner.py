"""Assemble the ORIGINAL pure numeric Luau module into a native Luau CLI test script."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "src/WF13Policy.luau"

def main():
    source = SOURCE.read_text(encoding="utf-8")
    assert source.startswith("--!strict\n")
    assert source.rstrip().endswith("return Policy")
    source = source.replace("--!strict\n", "", 1)
    cases = r"""
local function close(a, b)
    return math.abs(a - b) <= 0.001
end
local cases = 0
local function ok(value, message)
    cases += 1
    assert(value, "WF13 native policy case " .. tostring(cases) .. ": " .. message)
end

ok(Policy.insideEllipsoid(0, 0, 0, 82, 58, 82), "inside center")
ok(Policy.insideEllipsoid(41, 0, 0, 82, 58, 82), "edge inclusive")
ok(not Policy.insideEllipsoid(41.01, 0, 0, 82, 58, 82), "outside ellipsoid")
ok(not Policy.insideEllipsoid(0, 29.01, 0, 82, 58, 82), "above ellipsoid")
ok(not Policy.insideEllipsoid(0, 0, 0, 0, 58, 82), "zero dimension")
ok(not Policy.insideEllipsoid(0/0, 0, 0, 82, 58, 82), "reject NaN")
ok(close(Policy.upwardForce(100, 196.2, 0.35), 12753), "real world-relative gravity compensation")
ok(Policy.upwardForce(-1, 196.2, 0.35) == 0, "invalid mass")
ok(Policy.upwardForce(100, 196.2, 0.95) == 0, "forbid unrealistic near zero g")
ok(Policy.upwardForce(100, 0, 0.35) == 0, "zero world gravity")
ok(close(Policy.landingForce(100, 196.2, 0), 6867), "start exit fade")
ok(close(Policy.landingForce(100, 196.2, 1), 3433.5), "half exit fade")
ok(Policy.landingForce(100, 196.2, 2) == 0, "landing fade expires")
ok(Policy.landingForce(100, 196.2, -1) == 0, "negative time rejected")
local x, y, z = Policy.clampVelocity(100, 60, 0)
ok(close(x, 48) and y == 30 and z == 0, "clamp horizontal and rising")
local x2, y2, z2 = Policy.clampVelocity(0, -200, 100)
ok(x2 == 0 and y2 == -34 and close(z2, 48), "clamp fall and lateral")
local x3, y3, z3 = Policy.clampVelocity(2, 3, 4)
ok(x3 == 2 and y3 == 3 and z3 == 4, "normal velocities unchanged")
local a, b, c = Policy.clampVelocity(math.huge, 9, 1)
ok(a == 0 and b == 0 and c == 0, "nonfinite velocity fail closed")
print("WF13_NATIVE_ACTUAL_POLICY_PASS cases=" .. tostring(cases))
"""
    script = "local Policy = (function()\n" + source + "\nend)()\n" + cases
    output = Path(sys.argv[1] if len(sys.argv) > 1 else "/tmp/wf13_native_policy.luau")
    output.write_text(script, encoding="utf-8")
    print("WF13_NATIVE_RUNNER_CREATED source_file=", SOURCE, "bytes=", len(script.encode("utf-8")))

if __name__ == "__main__":
    main()
