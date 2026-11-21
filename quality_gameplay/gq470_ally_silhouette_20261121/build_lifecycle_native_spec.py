#!/usr/bin/env python3
"""Extract the REAL ally LocalScript shutdown function into a Luau native harness.
This exercises the canonical author source's teardown function, not a copied reimplementation.
Not Roblox Engine/Studio proof. No network, credentials, game assets or authority.
"""
from pathlib import Path
import sys

SOURCE = Path(__file__).with_name("EGGRUMBLE_AllySilhouette.client.luau")
text = SOURCE.read_text(encoding="utf-8")
if text.count("local function shutdown()") != 1 or text.count("local function isVisibleAlly") != 1:
    raise SystemExit("RED_CANONICAL_SHUTDOWN_SCOPE")
actual = "local function shutdown()" + text.split("local function shutdown()", 1)[1].split(
    "local function isVisibleAlly", 1
)[0]
if actual.count("table.clear(globalWatches)") != 1:
    raise SystemExit("RED_MISSING_WATCH_RELEASE")
if actual.count("connection:Disconnect()") != 1:
    raise SystemExit("RED_MISSING_DISCONNECT")
mode = sys.argv[1] if len(sys.argv) == 2 else None
if len(sys.argv) > 2 or mode not in (None, "--negative-drop-disconnect", "--negative-disable-fade"):
    raise SystemExit("USAGE: build_lifecycle_native_spec.py [--negative-drop-disconnect|--negative-disable-fade]")
if mode == "--negative-drop-disconnect":
    actual = actual.replace("connection:Disconnect()", "-- mutated omitted disconnect")
preamble = """-- Native-only stub harness extracted from real game LocalScript.
local stopped = false
local globalWatches = {}
local disconnected = 0
local cleared = 0
local function clearAll()
    cleared += 1
end
for i = 1, 6 do
    table.insert(globalWatches, {
        Disconnect = function(self)
            assert(self.done ~= true, "DOUBLE_DISCONNECT")
            self.done = true
            disconnected += 1
        end,
    })
end
"""
checks = """
shutdown()
assert(stopped == true, "SHUTDOWN_DID_NOT_SET_STOP")
assert(disconnected == 6, "STALE_PLAYER_LISTENERS")
assert(cleared == 1, "HIGHLIGHT_NOT_CLEARED")
assert(#globalWatches == 0, "WATCH_REGISTRY_NOT_CLEARED")
shutdown()
assert(disconnected == 6 and cleared == 1, "NON_IDEMPOTENT_SHUTDOWN")
print("GQ470_CANONICAL_SHUTDOWN_NATIVE_BEHAVIOR_PASS")
"""
# Execute the actual selected LocalScript's fade arithmetic, not a paraphrase.
lines = text.splitlines()
consts = ("local MAX_DISTANCE = 45", "local FADE_START_DISTANCE = 32",
          "local OUTLINE_TRANSPARENCY = 0.68")
for declaration in consts:
    if lines.count(declaration) != 1 and not (
        declaration.startswith("local FADE_START_DISTANCE") and
        sum(line.startswith(declaration) for line in lines) == 1
    ):
        raise SystemExit("RED_FADE_CONSTANT_" + declaration)
ratio = [line.strip() for line in lines if line.strip().startswith("local fade = math.clamp(")]
alpha = [line.strip() for line in lines if line.strip().startswith("effect.OutlineTransparency = OUTLINE_TRANSPARENCY +")]
if len(ratio) != 1 or len(alpha) != 1:
    raise SystemExit("RED_CANONICAL_FADE_FUNCTION")
if mode == "--negative-disable-fade":
    alpha = ["effect.OutlineTransparency = OUTLINE_TRANSPARENCY"]
fade_luau = """
local MAX_DISTANCE = 45
local FADE_START_DISTANCE = 32
local OUTLINE_TRANSPARENCY = 0.68
local function alphaAt(distance)
    local candidate = {distance = distance}
    local effect = {}
""" + "    " + ratio[0] + "\n" + "    " + alpha[0] + """
    return effect.OutlineTransparency
end
assert(math.abs(alphaAt(0) - 0.68) < 1e-6, "NEAR_ALLY_WRONG_OPACITY")
assert(math.abs(alphaAt(32) - 0.68) < 1e-6, "FADE_START_WRONG")
assert(alphaAt(38) > alphaAt(32) and alphaAt(38) < alphaAt(45), "NO_PROGRESSIVE_FADE")
assert(math.abs(alphaAt(45) - 1) < 1e-6, "FADE_END_NOT_INVISIBLE")
assert(math.abs(alphaAt(55) - 1) < 1e-6, "FADE_LIMIT_NOT_CLAMPED")
print("GQ470_CANONICAL_FADE_NATIVE_BEHAVIOR_PASS")
"""
sys.stdout.write(preamble + "\n" + actual + "\n" + checks + "\n" + fade_luau)
