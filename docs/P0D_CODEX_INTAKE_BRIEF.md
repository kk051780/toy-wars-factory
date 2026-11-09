# TRAP RAIDERS P0-D | Windows Codex read-only intake v1

**2026-11-10 JST.** This is a public-safe, source-free index of previously sealed artifacts. The actual cumulative game source and unpublished Roblox Studio Place reside only on the OWNER's PC. A GitHub Issue, downloaded encrypted JSON, offline Python PASS, or registry entry is **not** authorization to edit/merge/publish any Roblox game.

## What was actually checked

- 12 distinct `packet_id`s, representing 12 of 17 representative feature groups (D06–D17). One large v40–42 packet spans four groups, D16 has three additive packets, and D17 has two. Thus **12 packets != 12 finished functions** and multiple packets in one group must not be counted as extra completed functions.
- GitHub connector fetched the **ciphertext JSON and README at the immutable commit for each item**, 24/24 public-safe files. Git Blob SHA-1 and envelope `packet_id`/`game_id`/`zip_sha256` metadata were cross-checked; none of these files was decrypted or executed by this intake audit. Remote GET can be repeated by PC using `--verify-remote`; that mode is opt-in and only reads pinned public raw content. No keys are stored here.
- Existing real PC v37 QA was reported `PARTIAL_NOT_READY` in issue #213. That is not automatically promoted by new packages. For every reference packet, `WINDOWS_RESTORE=NOT_TESTED`, `LUAU_PARSE=NOT_TESTED`, `STUDIO_INTEGRATION=NOT_TESTED`, `STUDIO_QA=NOT_TESTED`.

## PC Codex precise handoff plan (only when OWNER directly instructs)

1. Re-read [#218](https://github.com/kk051780/toy-wars-factory/issues/218), [#213](https://github.com/kk051780/toy-wars-factory/issues/213), [#217](https://github.com/kk051780/toy-wars-factory/issues/217) and the newest **actual** local `CHECKPOINT`, `RESUME`, `BUILD_MANIFEST`, `FEATURE_MATRIX`, `QA_REPORT`, original source SHA and Studio-saved Place SHA. Do not replace a newer saved version with historic v37 SHA `c56459c29595f5ecde5521565862d0a4ea3c8a426a35cbb1d539ad6e08fd4741`.
2. Back up current real PC source and Place, verify the originally owned Studio instance(s) only. **First finish v37 final saved-Place test**: true 2/3-client blue/red egg theft → drop → recover → score → rematch; authenticated anti-spoofing; 7 jobs and S1–S4 regression; audio listening; iPhone landscape emulator. Physical-phone tests remain NOT_TESTED if unavailable. Investigate `ChatScript` error without assuming repaired.
3. When v37 is genuinely accepted by OWNER, receive **only the v39-H1 packet** `v39-h1-chatlead-ref-20261110` at pinned commit `baa29df8bc3f10f94792fcb135b3ee2a136ad8b8`. Decrypt with OWNER-private key in a trusted local directory using reviewed safe `restore_handoff_safe.py` from `d37eec1b653d060ae27568ddcd5f501da9662081`. Supply expected `game_id`, `work_id`, `packet_id`, zip SHA from registry; no forced overwrite, no archive extraction before manifest/path inspection, no remote script execution.
4. Re-verify the decrypted ZIP SHA/manifest, inspect the Luau and local game differences, integrate **one bounded feature slice** with server authority, then actually run Studio/QA and record exact source/Place SHA. Only after v39 QA consider v43-A neutral NPC. For all later D07–D17, evaluate collisions: `D08+D12+D16` share a **single** event chooser; `D03+D11` share NPC ownership; `D06+D10` have separate reward rules but must share one trusted RoundEnd; D17 cosmetic entitlement cannot be claimed by the client. Inspect dependency chain before one-packet intake.
5. Post statuses separately: `PUBLIC_GITHUB_CIPHERTEXT_READBACK`, `WINDOWS_RESTORE_SHA_VERIFIED`, `LUAU_PARSE`, `STUDIO_INTEGRATED`, `STUDIO_QA_PASS`, `STUDIO_CLOSED_VERIFIED`; attach test evidence without exposing private sources or keys. Any missing check remains NOT_TESTED. Stop → Edit → Save → normal Quit → verify the correct owned Studio PID absent. No main push, merge, Roblox publication, real transaction or additional spend without separate OWNER approval and protected P0-A gates.

## Run the intake tool (read-only)

```powershell
python tools/p0d_intake_audit.py --registry docs/P0D_INTAKE_REGISTRY.json
# Network check is optional, read-only, public GitHub only:
python tools/p0d_intake_audit.py --registry docs/P0D_INTAKE_REGISTRY.json --verify-remote
python -m unittest discover -s tests
```

**No remote Windows PC access exists in this ChatGPT conversation.** These commands prepare an intake registry and stop at the boundary; they do not trigger any Windows Codex or Roblox Studio actions.

## Next ChatGPT work

New packets and PC evidence should be added to #218 using the existing `P0D_CLAIM` and `P0D_DELIVERY` format; a curator then **revalidates and pins** additions in a new intake registry version. Never promote stages based only on a textual `PASS` claim, and never coerce a private key into an Issue, GitHub branch, public environment variable, or README.
