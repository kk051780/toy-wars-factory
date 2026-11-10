# Offline QA scope — S1 RC source/wiring only

| Gate | Expected proof | Local fixture |
| --- | --- | --- |
| Source bytes | Receipt path/size/SHA match actual game code | valid / modified / deleted / added |
| Exact release plan | SHA256 of exact plan bytes pinned in receipt; unit/commit/destination match | modified plan / commit spoof |
| Singleton source authority | Exactly one declared `round`, `event_chooser`, `damage` | duplicate / missing authority |
| Rojo placement | Every source Lua/Luau reachable by `$path`; source scripts mounted into correct ServerScriptService or Starter* subtree | missing map / path traversal / unmounted / wrong side |
| Windows-safe paths | No symlinks, noncanonical path, file/folder case collisions | alias / shadow paths |
| Honest labels | Source build only; Studio and release not approved | false Studio/live publication claim |

**Hard boundary:** Each test under `tests/` uses a **synthetic fixture**, not true P0-D gameplay Luau or Roblox Studio. Thus offline QA above supports the build mechanism but DOES NOT imply actual gameplay works. When #220 releases its RC source tree, rerun the same checker on that exact RC+plan and store the output as an immutable independent QA receipt. Do not claim `CHAT_RC_READY` before the separate scenario QA and owner/integrator release gates pass.
