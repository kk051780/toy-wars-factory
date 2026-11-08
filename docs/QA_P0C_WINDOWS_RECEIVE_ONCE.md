# P0-C / C2A — One-shot Windows GitHub receipt (not a Codex runner)

P0-C owner instruction: https://github.com/kk051780/toy-wars-factory/issues/204#issuecomment-6718344277

This child draft adds a Windows-targeted single-GET preflight atop protected PR211. It does not modify PR211, the game, or main.

## Allowed operation
* From an explicitly chosen, trusted Windows workspace, a human *may* execute: `python -m tools.system_p0c_windows_receive_once --comment-id <GITHUB_COMMENT_ID>`. It only performs one GET to the pinned GitHub issue-comment REST endpoint and prints a JSON diagnostic; it has no persistence, loop, shell, Codex API, Roblox operations, or write actions.
* CLI is intentionally disabled off Windows for real network calls; tests supply an offline fake provider and never access real GitHub.
* Actual GitHub comment metadata previously observed through official GitHub API identifies user `kk051780` with OWNER association and the ChatGPT GitHub connector app slug. These metadata are *checked but not cryptographic proof or authorization*.
* One intent body must consist solely of `P0C_READONLY_INTENT_V1` followed by the C1 strict JSON command object. The CLI never accepts an arbitrary URL.
* Even success reports `READ_ONLY_GITHUB_RECEIPT_MATCHED_NO_EXECUTION` with owner_authorized=false, codex_execution_authorized=false, may_run_commands=false, pc_action_executed=false.

## Not available yet
No unattended Windows polling, no scheduled task or service installation, no GitHub→Windows automatic notification, no stateful replay store or signed owner command, no Codex remote invocation. Never infer these capabilities from offline test success. No program can grant itself tool permissions from a user-authored Issue comment.

## C2B / C3 gates
Independent authenticated security audit of exact child PR head, parent PR211 and CI; explicit local OWNER opt-in; real single-comment GitHub→Windows read-only receipt proof. Then separate design review for authenticated one-time instruction delivery, durable dedupe, original CAS lease and host permissions. No unattended source writing, Roblox Save/Publish or model spending.
