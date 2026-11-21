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
mutant = len(sys.argv) == 2 and sys.argv[1] == "--negative-drop-disconnect"
if len(sys.argv) > 2 or (len(sys.argv) == 2 and not mutant):
    raise SystemExit("USAGE: build_lifecycle_native_spec.py [--negative-drop-disconnect]")
if mutant:
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
sys.stdout.write(preamble + "\n" + actual + "\n" + checks)
