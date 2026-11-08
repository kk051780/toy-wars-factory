# P0-C C2B — One-shot discover-latest, with zero Codex execution

Owner: https://github.com/kk051780/toy-wars-factory/issues/204#issuecomment-6718344277

This patch extends **existing PR212**, not another PR. New opt-in Windows CLI can find active, dedicated P0C comment intent on GitHub Issue #204, without requiring a comment ID: `python -m tools.system_p0c_windows_scan_once --scan-once`.

**Private-repository credential**: on a real Windows host, this program requires a GITHUB_TOKEN environment variable containing a narrowly scoped read-only GitHub token with access to this repo's Issues comments. It will fail closed if absent; never log the value. Do not create/export/share an unrestricted personal access token or disable GitHub authentication for convenience. Use an existing approved credential if available; otherwise report BLOCKED_CREDENTIAL_MISSING and request explicit host authorization for a least-privilege credential. The CLI neither reads git credential files nor invokes gh or any shell process.

**Behavior**: Windows-only real network scan; fixed API host and Issue #204; bounded <=5 pages, 100 comments/page; HTTPS GET only; redirects explicitly refused before sending to another host; no arbitrary URLs, write actions, local files, polls, persistent process, Codex/Studio calls, shell/subprocess, or startup registration. GitHub metadata checks and C1 JSON intent format are diagnostic, not proof of owner authorization. All success statuses still have owner_authorized=false / codex_execution_authorized=false / may_run_commands=false.

**Testing**: `python -m unittest discover -s tests -p "test_system_p0c_windows_scan_once.py" -v` (mocked, offline) and full CI. Tested candidate comments are fixtures, never automatically issued or executed.

**NEXT**: separate authenticated reviewer validates parent PR211 and PR212 exact head. On verified Windows with explicit OWNER opt-in perform one read-only test from a single ChatGPT-origin Issue comment. Until that is observed, status is SOURCE_ONLY; not live ChatGPT→Windows relay. Later bounded, explicitly activated polling process would be required to eliminate per-command manual input. Such unattended process is NOT installed, activated, or approved here.
