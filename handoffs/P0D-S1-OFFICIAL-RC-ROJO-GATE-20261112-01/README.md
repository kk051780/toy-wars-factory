# P0-D S1 RC01-B — Actual official release source Rojo Place gate

**Game:** TRAP_RAIDERS; **release:** P0D-S1-KIDS-RC01; **exact owner-integrated source commit:** `5dc6c958ea5549b1e859d6d250e6179e731181fb`.

This independent, isolated-branch test uses the **actual official release** `releases/P0D_S1_KIDS_RC01/` tree — not merely the separate handoff candidate from prior Rojo CI. The selected release head is immutable-pinned. The only extra branch changes are this verification packet and an Actions workflow. The writer of the release itself remains exclusively the #220 CHAT-INTEGRATOR; main, official RC branch, Roblox publication, spending, and P0-A/B/C are untouched.

The verifier is adapted (for official RC path and manifest) from the previously proven source-only [Rojo gate](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6808056894), which compiled an equivalent 20-source candidate. The adapted program is not itself assumed successful until the **new exact-RC Actions run** returns success and its output is examined.

## Fixed integrity and topology
- Official source commit: `5dc6c958ea5549b1e859d6d250e6179e731181fb`
- Official RC BUILD_MANIFEST SHA256: `81cd35eb89593f6e84ccbc3d9dca1cadda4a06edfee488afc7375eaee6864311`
- Exact `src/` tree: `01aede07b64973a32ba02647c10a9e8b8f8c3285`
- Native Rojo version: 7.7.1, release ZIP SHA256 `00feb4fa0829a1dd72b49df2639da519a352bfe13cadcd83969e2ba2bb5693c4`
- 32 manifest files + manifest; 20 source Luau embedded in one `.rbxlx`, exactly 1 server Script, 3 client LocalScripts, 16 ModuleScripts, correct original source bytes and Roblox service location.
- Invalid XML, modified source, missing HUD/first minute coach, wrong class/service and duplicate Game script must FAIL.

## Execution and evidence

An Actions job on the isolated `handoff/p0d-rc01b-official-rojo-source-gate-20261112-01` branch should check immutable official source ancestry and unchanged release paths, verify this public test packet, download and SHA-check official Rojo, run `rojo build releases/P0D_S1_KIDS_RC01/default.project.json`, inspect real XML Place bytes, and upload a **review-only** `.rbxlx` plus a machine-readable source receipt.

If the workflow remains queued, fails or cannot be read, report `NOT_VERIFIED`; do not count an artifact by name alone. An `.rbxlx` being built is **not** Roblox Studio two-client/mobile/physics validation, does not enable either D07/D08 boss flag, and never implies OWNER approval for live release.

Original native/independent official source QA and current 70% global audit: [Issue #220](https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-6808174562). Never silently infer real engagement, retention or earnings from source QA.
