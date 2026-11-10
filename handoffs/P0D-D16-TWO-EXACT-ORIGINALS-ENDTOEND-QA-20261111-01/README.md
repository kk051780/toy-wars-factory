# TRAP RAIDERS — D16 exact-original pair end-to-end verification

**Game:** `TRAP_RAIDERS` / `p0d-siege-v19`

This is **NEW read-only QA code**, *not* a migrated old source, a new game feature, a Roblox plugin, or another event scheduler. It tests that the two **already keyless, genuinely recovered original** source packets cooperate correctly without adopting their conflicting cleanroom alternatives.

| Exact original (source bytes unchanged) | Immutable GitHub commit |
| --- | --- |
| D16 SCALE-FX | `584b11ef24cf3d44695d86b505207491bbd3844e` |
| D16 VISUAL-REPLICA | `226a5664ed50131868391289723c130d35abf48f` |

The CLI requires those **two actual source directories** and SHA256-checks three original Python oracles byte-for-byte before importing them. It runs real `ScaleFx` -> `ScaleFxSnapshotBridge` -> `ScaleFxClientPolicy` behavior with independent server/client clocks. It cannot silently run on substitute cleanroom code.

## Use on the OWNER Windows Codex PC

1. **First** complete/preserve any current D07 Studio QA checkpoint. Do not overwrite the latest real PC Place, source, or local HEAD.
2. Fetch the exact two fixed GitHub source commits using the authorized read-only keyless intake process into **two new isolated directories**. The prior Windows 21/21 source receipt **does not include** these 22nd/23rd original packs.
3. From this QA package root, with Python 3.10+:

```powershell
python tools/run_exact_pair_qa.py --scale-root "C:\Temp\P0D_D16_SCALE_ORIGINAL" --visual-root "C:\Temp\P0D_D16_VISUAL_ORIGINAL" --json-out "C:\Temp\D16_ORIGINAL_PAIR_RECEIPT_NEW.json"
```

Replace the example roots with directories containing, respectively, `reference/scale_fx.py` and `reference/bridge.py` + `reference/client_policy.py`. The JSON output path must **not already exist**. No credentials, encryption key, internet access, write to game source, or Studio are required by this CLI. Exit 0 = original-oracle contract PASS; exit 2 = BLOCKED/FAIL.

Run local package safety tests independently:

```powershell
python -m unittest discover -s tests -p "test_*.py" -q
```

## What success means

- Source hashes of three historical Python oracles match the source manifests from the immutable originals.
- 252 end-to-end offline checks exercise GIANT_ONE/MINI_ALL, 1600/700 milliscale, eight-second local expiry, subset target removal, canonical roster, duplicate/scope/round rejection, server cleanup, late and replayed packets, and 200 clock-offset scenarios.
- This **does not** verify the whole archived source package, native Luau runtime, Roblox Studio, game HUD, physics, mobile fps, PC source integration, or controlled merge/production publication.

**Critical integration boundaries:** the original SCALE-FX API uses `ScaleFxCore.new(matchId)` and `begin(state,matchId,eventId,kind,actorId,roster,nowSeconds)`. Do **not** install cleanroom Core `883ca3b7...` or its D08 V1/V2 gates alongside this original. The separate optional original-compatible D08 source gate at `71d682e63ebb2de80c39aaeafdf0cf420202cc68` is not installed or exercised here. Source-provenance proof is separate from actual server authority. Keep all client remote events display-only. No `main` writes, merges, live Roblox publishing, spending, P0-A/B/C authentication changes or Automation changes.

See `docs/OWNER_PC_QA.md` for follow-on native/Studio checks.
