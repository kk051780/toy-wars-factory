# P0-D PC QA evidence gate — read-only handoff v1

**GAME** `TRAP_RAIDERS` · **WORK** `p0d-siege-v19` · **META-only** `P0D-META-PC-QA-GATE-20261110-01`

This is a **real runnable Python tool**, not an instruction that automatically triggers Windows Codex or Roblox Studio. Its only job is to inspect **files that the OWNER's PC already has**, compare SHA-256 values, and mark missing, stale, or contradictory PC QA evidence. It does **not** prove tests were performed, and it cannot declare game/Studio/publication acceptance. Use it after OWNER directly instructs the PC's existing Codex session.

## What it checks

* The **actual local saved Place** `.rbxlx`/`.rbxl` bytes and **actual cumulative ZIP** bytes exist inside a trusted, private snapshot directory and match their declared SHA-256 values. Never overwrite a newer save with historical `aebcdfac...` v39 evidence.
* Each of eight named scenarios has one of `PASS` / `FAIL` / `NOT_TESTED` / `BLOCKED` and is bound to **that same saved Place's SHA**. A `PASS` or `FAIL` must cite a readable local `*.txt`, `*.log`, or `*.json` evidence file whose bytes match a declared SHA-256. A `NOT_TESTED` scenario may not smuggle in a misleading evidence filename.
* Rejects duplicate JSON fields, absolute/traversing paths, symlinks in the private snapshot tree, mismatched saved files/log files, and oversized data. Report outputs use **exclusive create** and will not overwrite existing evidence or other files.
* The **three critical checks** for continued owner review: `v39_saved_place_2client`, `v39_reward_no_double`, `v39_spoof_remote_rejected`. If any QA scenario reports `FAIL`, returns `STOP_FIX_CRITICAL_OR_OTHER_FAILURE`. If a critical check is not `PASS`, returns `WAIT_FOR_CRITICAL_QA`. If all three are checked and pass, returns `OWNER_REVIEW_ONLY_NO_AUTO_STUDIO` — **not** permission for v43-A auto-integration.
* Full release requires all eight scenarios verified **plus** independent owner approval, and is **not** granted by this tool. The remaining five checks are final horizontal UI, same-account reconnect, real listening, real physical phone play and owned-PID exit. Don't confuse Studio mobile emulator FPS with a real phone.

## Windows Codex usage (only when OWNER directly instructs)

1. Read the newest [#218](https://github.com/kk051780/toy-wars-factory/issues/218), [#213](https://github.com/kk051780/toy-wars-factory/issues/213), [#217](https://github.com/kk051780/toy-wars-factory/issues/217) and **the actual PC checkpoint**. The existing PC #213 report at [comment #6753848890](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6753848890) documents v39 scoped Studio PASS, *not* complete final QA. If a newer PC save exists, take its current SHA and preserve the old one.
2. Independently perform the remaining **v39 final saved-Place 2-client and security checks** in an isolated unpublished test Place; collect local logs. No private game source or raw player identifiers go to public GitHub.
3. Copy this tool and the evidence *template* into a new **owner-only local** folder. Populate the template with **real relative filenames, real SHA values and actual recorded status**; keep logs, Place, cumulative ZIP and JSON within that private folder. `0`-filled SHA template values are NOT valid PC evidence.
4. On Windows/Python 3.14 or compatible interpreter run:

```powershell
python tools/p0d_pc_qa_gate.py --workspace "C:\private\p0d-qa-snapshot" --evidence "qa/pc_qa.json" --output "C:\private\p0d-qa-report-v1.json"
python -m unittest discover -s tests -p 'test_p0d_pc_qa_gate.py' -v
```

5. Read JSON fields `v43a_review_gate`, `release_gate`, `remaining_release_checks` and `disclaimer`. Exit code **0** means **files/checks agree and critical evidence is ready for OWNER review**, not Studio QA, game integration, public release, or permission to run v43-A. Exit **2** means incomplete/failing evidence or a validation error. Don't conceal those results. If v39 has security or reward failures, **STOP new integration** and work on fixing v39 first.
6. Only after OWNER accepts the real PC evidence, proceed to [existing v39→v43-A safe intake plan](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6754010059). The other chat owns D11 neutral capture trace validation; this gate **does not duplicate that work**.
7. Report to #213/#218 **only redacted statuses and file hashes**, no plaintext game source, private ZIP, AES keys, raw logs, player IDs, or absolute private paths.

## Evidence schema

See [`examples/P0D_PC_QA_EVIDENCE_TEMPLATE.json`](../examples/P0D_PC_QA_EVIDENCE_TEMPLATE.json). For each `PASS` or `FAIL` change a check record to:

```json
{
  "status": "PASS",
  "tested_place_sha256": "<actual saved Place SHA-256>",
  "evidence_path": "qa/v39_2client.txt",
  "evidence_sha256": "<actual local evidence file SHA-256>"
}
```

The tool validates file integrity **only**; the human/PC must separately establish that each log genuinely reflects the relevant test. The tool never accesses the network, executes subprocesses, launches Roblox Studio, obtains secrets, changes main, merges, publishes, sends payments or alters P0-A/B/C state. The folder must be trusted and non-shared; it does not protect against a privileged process maliciously replacing files while they are read.

## Test status and initial shipment

Synthetic tests: **28/28 PASS** under local Python unittest on 2026-11-10 JST. Real PC invocation: **NOT_TESTED**. Windows v39 status from Issue #213: `RESTORE_VERIFIED / SCOPED_STUDIO_PASS / GLOBAL_PARTIAL_NOT_READY`. v43-A Windows restore/integration: **NOT_TESTED**. This code is safe public metadata/QA helper only and must be kept on its own non-main handoff branch.
