# TWF-0005 — Gemini candidate custom patch gate trusted the wrong file header

Date: 2026-10-24. Scope: **draft PR #11 only; not merged or activated**.

## Finding and reproducible evidence

The original `tools/gemini_patch_gate.py` checked allowlisted paths from the `diff --git a/... b/...` summary but did not compare them with the `--- a/...` and `+++ b/...` file headers. A crafted diff could claim `src/combat.lua` in the summary while declaring `+++ b/.github/workflows/hijack.yml` as the actual destination. In a disposable local Git repository, `git apply --check` and `git apply` accepted that mismatch and created the workflow file. No real project workflow was modified by the reproduction.

This was a **gap in the custom pre-PR scanner**; it does not establish that gh-aw's separate `safe-outputs.allowed-files` protection would also be bypassed. No Gemini inference or Google API call was made.

## Root cause

Only matching `diff --git` summaries were inspected. Unexpected headers, a mismatched `+++` target, and traversal-like path components were not rejected. The scanner therefore had an incomplete view of the file paths that Git might apply.

## Correction (draft candidate only)

- Require each `diff --git` section to contain a valid summary and exactly one `---` / `+++` header, with matching paths or `/dev/null`.
- Reject traversal segments (`.`, `..`), empty segments, absolute paths and backslashes before allowlisting.
- Reject malformed headers, stray content, and rename/copy directives.
- Inspect added source lines that start with `++` (shown as `+++...` in a unified diff); exclude only actual `+++ ` file-header lines from credential scans.
- Add five offline regression cases: forged destination, traversal, malformed extra header, missing destination header, and a credential hidden on an added line beginning with plus characters.
- Preserve the existing second Gemini API review and all owner approval/release restrictions.

## Remaining limits

These are **static parser defenses**, not proof against all malicious patches or prompt injection. The custom Gemini review is **not equivalent** to GitHub's official threat detector. Actual Gemini API execution remains **NOT AUTHORIZED**. Roblox Studio, multiplayer and mobile testing remain unverified. Do not merge the draft solely on the basis of static QA.
