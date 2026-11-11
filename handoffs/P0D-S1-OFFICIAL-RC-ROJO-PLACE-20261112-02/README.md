# TRAP RAIDERS — Actual official S1 RC to Rojo Place integrity QA

- Official RC source commit **5dc6c958ea5549b1e859d6d250e6179e731181fb**, path `releases/P0D_S1_KIDS_RC01/` (not a new release and not an unsynchronized handoff candidate).
- This isolated QA branch holds a **byte-identical 33-file Git-blob snapshot** of that official RC at `official_src/` and a separate `OFFICIAL_SOURCE_LOCK.json` identifying the exact Git SHA1 blob and size of each of the 33 upstream files. The source is NEVER changed.
- The independent Python verifier confirms official source-lock Git blobs (33/33), strict official six-key public game manifest (32/32 SHA256), and exact real Rojo 7.7.1 (pinned Linux release SHA256 `00feb4fa0829a1dd72b49df2639da519a352bfe13cadcd83969e2ba2bb5693c4`) exported Roblox XML Place.
- Validate **all 20 Luau sources exactly** in the generated .rbxlx and the Game server 1 / client LocalScript 3 / module 16 service mapping. Run 9 explicit negative XML tamper tests against real output; no fake pass.
- CI uploads the `TRAP_RAIDERS_S1_OFFICIAL_RC.rbxlx` and JSON source receipt to **GitHub Actions private artifact** for sole #220 integrator to inspect. The workflow must not overwrite or merge into `rc/p0d-s1-kids-rc01`.
- SUCCESS means a Rojo export of the exact pinned official RC can be constructed. It **does not** prove Roblox Studio runtime, real 2-player/phone gameplay, activation of disabled D07/D08, human first-minute comprehension, or owner release approval. Both flags in original Game remain intentionally false.
- No main/RC writes, paid services, publishing, Windows Codex, existing 5 Automations or P0A/B/C protected changes.
