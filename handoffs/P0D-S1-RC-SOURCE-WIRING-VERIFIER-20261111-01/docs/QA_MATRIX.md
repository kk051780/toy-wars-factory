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

## Pre-RC snapshot (V1.1 supplemental checks)

| Item | Evidence | Expected failure |
| --- | --- | --- |
| `BUILD_MANIFEST.json` source identity and complete file coverage | Actual file bytes exactly match `sha256`, `size`, and each file is listed once | mismatched, missing, extra, duplicate, invalid paths |
| `default.project.json` composition | Real paths exist and each script has a correct server/client mount | missing project, wrong mount, duplicate case |
| Source-only truthfulness | `docs/RELEASE_STATUS.json` explicitly indicates no Studio/game readiness and no approval | false `game_ready`, Studio PASS or owner release |
| Bootstrap | At least one `.server.luau` and `.client.luau` bootstrap is present | non-runnable source-only modules |

All `tests/test_source_snapshot.py` scenarios are synthetic, and a PASS on
those tests is **not** a pass against the integrator's actual source. The
integrator or an independent auditor must clone the pinned source commit,
run the snapshot tool against the real `releases/P0D_S1_KIDS_RC01` directory,
and capture the report before scoring the pre-RC source gate.

## V1.2 extra acceptance (multi-authority + duplicate-mount)

- Accept genuine one-unit plural `round`, `event_chooser`, `damage`, while still
  supporting the exact original singular schema.
- Reject a role duplicated inside one source declaration, claimed by a second
  unit, unrecognized, malformed, zero-length plural, or with both fields.
- Reject missing/stale/forged `source_units[].authorities` attestation in
  compatible-assembler receipts, without interpreting SHA evidence as runtime proof.
- Reject multiple Rojo `$path` entries that mount the **same** Luau/module twice,
  even on the same side of the client/server security boundary.

Scenarios above are synthetic fixture cases, separate from real game source QA.
