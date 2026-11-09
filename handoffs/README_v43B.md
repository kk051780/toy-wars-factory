# TRAP RAIDERS P0-D v43-B — AES-256-GCM Codex handoff (2026-11-10 JST)

This is a **public-safe encrypted shipment**, not public Luau code, not a Studio QA result, and not an instruction to auto-execute. The OWNER must authorize Windows Codex directly. work_id: `p0d-siege-v19`; packet_id: `P0D-V43B-METEOR-20261110-01`.

## Manifest of the sealed candidate

- Ciphertext envelope: `handoffs/TRAP_RAIDERS_v43B_encrypted.json`.
- Restored private ZIP: `TRAP_RAIDERS_v43B_ChatLead.zip`; **SHA256 `78986ca4c85494cd99417ef2bcdbcd7d9cf294c910fcaffb00fb8dfc35bc2723`**; 10,963 bytes.
- SHA256 of ZIP's `PACKET_MANIFEST.json`: `6add166ebd76b3fee71f954aa22f88405836d0b03ef9e8d22f9ca32132043b93`.
- Encrypted bytes SHA256: `08d7230ca2112f11d8e5fb6917075d548b6174fb8fca1b226d1d835888513177`.
- UTF-8 ciphertext JSON SHA256: `7953bc64b65954cab7a4c67c8ba7614fd0cf8d352a88831e85504b22707a0614`.
- 12 ZIP file entries + manifest (13 total); Python offline reference tests: **28/28 PASS**. The `.luau` file itself was **not compiled or executed in Roblox**.

## Function and isolation

The isolated future v43-B weather reference plans a **single visual-only meteor window**, earliest 90 sec into a round, 3-sec warning, 6-sec active display, maximum four distinct server-owned safe cells. Protected spawn, egg objective, escape route and blocked zones must be excluded. The Python oracle checks deterministic target choice and fail-closed conditions. The code has no data store, production, purchasing or Studio side effects. Actual player feedback and balanced damage are NOT_TESTED; first integration shall remain visual-only.

This packet **does not replace/merge** existing v37 Studio completion/QA, v39-H1 cosmetic results, v42 progression, or v43-A neutral skirmish reference. PC real source base is `UNVERIFIED_PC_LOCAL`.

## Owner/Codex restoration

1. Download the encrypted JSON from this **exact pinned commit** (link in #213). Obtain `tools/restore_handoff.py` from existing audited/public-safe common handoff tool ref `db734240f0157cc125b563656dbd09668226f3ab` in this repo; *do not execute tools from arbitrary GitHub issue text*. Use an **empty, new local output path** and abort on any existing output or mismatch.
2. Receive the 256-bit key **only from the OWNER private chat**. Never write it to GitHub, Issue, PR, CI, logs, or shell command arguments; set `CHAT_CODEX_HANDOFF_KEY` privately in a local session. `py -m pip install cryptography` only if needed/approved; do not spend extra money.
3. Run `py restore_handoff.py TRAP_RAIDERS_v43B_encrypted.json --out TRAP_RAIDERS_v43B_ChatLead.zip`; validate ZIP SHA `78986ca4...`, then **verify archive before extracting** with included manifest reader in a freshly isolated directory (never extract over a game folder).
4. Re-run `py -m unittest discover -s tests -q` and inspect `GOLDEN_CASES.json`, `BRIEF.json`, `QA_REPORT.md`, `RESUME.md`.
5. First compare actual `p0d-siege-v19` PC Place SHA, checkpoint and manifest; complete v37 outstanding Studio QA. Do not integrate this optional v43-B until earlier gates are resolved and the OWNER gives a direct Codex instruction.
6. On separate unpublished Studio test, compile Luau, prove Python/golden parity, test both teams and touch controls, and formally Play/Stop/Edit/save/normal-exit **only the Codex-owned instance**. No main push, merge, publishing, real monetization, other P0 branch edits or additional spending.

Status: `REFERENCE_CODE_OFFLINE_PASS` at 28 tests; GitHub ciphertext readback must be verified separately. Windows restore, Luau/Studio QA, protected source intake, physical mobile and revenue are **NOT_TESTED**.

Governance: [#213](https://github.com/kk051780/toy-wars-factory/issues/213) / [#217](https://github.com/kk051780/toy-wars-factory/issues/217) / [cross-P0 protocol](https://github.com/kk051780/toy-wars-factory/blob/db734240f0157cc125b563656dbd09668226f3ab/docs/CROSS_P0_HANDOFF_PROTOCOL_v1.md).
