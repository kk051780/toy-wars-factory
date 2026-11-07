# Studio read-only smoke check — PR #187 candidate only

This manual tool inspects the source-pinned four-toy game candidate (PR #187, HEAD `35d4e0fc2a72a6bfc442561f4222e7497df15975`). It does not edit the open place, publish to Roblox, send HTTP traffic, read secrets, or establish any verified engine QA. It is not a replacement for hosted engine, 2-client or Android evidence.

## Optional Studio test (no owner PC work required for ordinary development)

1. Open the `twf_4toy_factory_throughput_NOT_ENGINE_VERIFIED.rbxlx` artifact from [Actions #42329210093](https://github.com/kk051780/toy-wars-factory/actions/runs/42329210093) in an authorized Roblox Studio PC; pin the actual artifact origin and candidate before interpreting output.
2. Paste `tools/studio_readonly_smoke_v2.lua` into View > Command Bar in **Edit** mode; inspect Output lines starting `TWF_SMOKE_`. It must report **PARTIAL** because Play checks do not run.
3. In **Play / Server** command context, rerun after the server and workshop are ready. The HUD is client-only, so Server stays PARTIAL even when its checks succeed.
4. In **Play / Client** command context rerun. The private ServerScriptService source is unavailable to a client and is deliberately SKIPPED, not reported as missing. The script chooses `Players.LocalPlayer` rather than a potentially unrelated player. This phase must also report PARTIAL. Review each PASS/FAIL/SKIP entry across all contexts rather than treating any phase as an engine attestation.
5. Stop and investigate any INCOMPLETE/FAIL or a skipped player check. Never infer success from logs from different place versions.

## Automatically included native Lua mock regression

`lua5.4 tests/auto/studio_smoke_mode_reporting_spec.lua`

The repository's existing `bootstrap-quality.yml` enumerates `tests/auto/*_spec.lua`, so this test joins the normal offline QA without modifying workflows. Its **10 deterministic mocks** exercise Edit, server Play and client Play mode classification, privacy boundary, foreign-first player isolation, missing server script, wrong 3D printer label, missing world, player-not-loaded and non-Studio rejection. Passing mocks are not Roblox execution.

## Development cycle / provenance

- **Work type:** isolated manual CONTROLLER QA diagnostic; source-pinned to PR #187. Not a new game mechanic; characters changed: none. Consult P0 Issue #57 for unattended author permissions and Issue #182 for FREE FIRST.
- **Files added:** `tools/studio_readonly_smoke_v2.lua`, `tests/auto/studio_smoke_mode_reporting_spec.lua`, `docs/STUDIO_SMOKE_v2.md`. Existing gameplay source and protection policy unchanged.
- **Behavioral defect:** a client does not receive ServerScriptService descendants; checking them as required caused false FAIL; using the first player could check an unrelated person's HUD.
- **Offline reproduction/evidence:** 10/10 local native Lua 5.4 mocks on 2026-11-07; hosted GitHub CI and any Roblox runtime must be evaluated independently at the exact new branch head.
- **Size:** new source ~9.1 KB, new test ~6.9 KB, doc ~2.7 KB, zero deletion of previously accepted code.
- **Safety:** no extra spending, no credential operations, no main direct write, no reviewer self-approval, no public release.
- **Next actor/task:** registered independent REVIEWER examines source and current HEAD Actions, then authorized actor may integrate under the existing strict provider-native gate; private Roblox engine access remains separately BLOCKED.
