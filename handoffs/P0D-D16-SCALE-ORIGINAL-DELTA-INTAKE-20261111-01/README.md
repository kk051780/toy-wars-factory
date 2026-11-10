# TRAP RAIDERS — D16 original ScaleFx keyless delta intake

Independent, read-only **incremental** staging helper for the **already keyless, exact-original** D16 ScaleFx source package. This does **not** produce a 23rd legacy recovery or replace the original author’s source. It only verifies and stages its **pinned GitHub commit** without an AES key, password, or developer-owned secret. It never accesses the live game checkout or Studio.

- Original packet: `P0D-D16-SCALE-FX-ORIGINAL-PUBLIC-RECOVER-20261111-01`, immutable commit `584b11ef24cf3d44695d86b505207491bbd3844e`.
- Original manifest SHA256: `2d5050efe5952aea82720a4b06ead61684da01d6f7286f26ddd3ff41740d264f`.
- This staging helper rejects partial/non-original files, wrong packet, symlinks, overwrites, nonmatching SHA and Git refs other than full SHA.
- **Do not combine with incompatible cleanroom core** `883ca3b790c938587c5d9c305a887a1ffff1249f`, or adapters V1 `ac50372942712503f836fb84d6331ef3bcc4b8f2` / V2 `1877222d4817153435bc5cfacdf1bb4e90d75aff`. Their `new`/`begin`/time APIs differ. Actual Windows integrator must evaluate a new original-compatible adapter if required.

## OWNER Windows Codex, after direct instruction only

```powershell
# Use a brand-new disposable folder, not the live PC game repo.
git clone https://github.com/kk051780/toy-wars-factory.git $env:TEMP\p0d-original-scale-src
# If the commit is unavailable in that clone, obtain its exact pinned branch from #218 using git fetch.
python tools/verify_original_scale_delta.py --repo $env:TEMP\p0d-original-scale-src --output $env:TEMP\p0d-scale-verified-NEW
```

Run this Python script from **this helper packet**; the original-scale commit must already exist in the disposable clone. If it fails, do not weaken the SHA check: preserve baseline and report `BLOCKED`. The script writes only to a **nonexisting, external** staging directory, leaves repo untouched, and emits `SOURCE_RECEIPT.json`. No secret key or private Place required.

**Scope:** transport and SHA/API conflict gate only. Does not claim Windows execution, native Luau parser, Roblox Studio, 2-client QA, actual model scaling, event authenticity, gameplay release or billing. Current original ScaleFx is cosmetic-only; server event chooser is separate.

Test: `python -m unittest discover -s tests -v`. Generated with `P0D_PUBLIC_SOURCE_V1` and verified under pinned Git commit, not a moving branch.
