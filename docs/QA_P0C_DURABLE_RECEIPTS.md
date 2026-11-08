# P0-C D1 — Durable one-shot receipt ledger (offline candidate)

This new standard-library Python module offers an **opt-in** SQLite durable record for a single GitHub Issue #204 read-only intent. It is added to the existing stacked DRAFT PR212 as an **unwired standalone library and tests**, not a Windows installation.

Algorithm: validate incoming GitHub comment with the existing strict P0-C C1/C2A helpers; check the explicit local database path in an existing directory with exact filename; SQLite BEGIN IMMEDIATE, single INSERT with PRIMARY KEY work_id, UNIQUE nonce and UNIQUE comment_id, COMMIT; duplicates, SQLite errors and malformed comments return BLOCKED. One test uses concurrent threads and checks exactly one winner. Crash after commit but before receiving response leaves record present, and retry blocks.

Safety: "read-only" describes the *remote GitHub/PC command execution* path, not local storage; **the opt-in ledger writes a local SQLite metadata record**. No command, Codex, network, Studio, filesystem change outside the selected SQLite DB (SQLite may create journal files), Windows install, auto-run or backend service. No connection to scan_once or any PC executable yet. No new secrets or raw command body persisted; SHA256 digest, work_id, nonce, comment_id and receipt UTC only. No GitHub writes.

Limitations: SQLite is **local single-host idempotency**, not distributed/cryptographic owner authentication and not #123 cross-host CAS. If a ledger is deleted, replaced, has unsafe permissions, is moved, or an alternative host executes, replay prevention does not hold. A spoofed host name is not trusted identity. A verified GitHub comment metadata label is not an authorization or digital signature. A successful record is not a permission to execute a task.

Next review: independent security reviewer of exact PR212 head and CI, then a separate owner-approved Windows one-shot test with a known safe/isolated directory. Later integration into a reviewed receiver may pass fetched source comments into this API only after owner identity and host permission are verified. Never auto-execute from Issue text. Codex stays short-use bridge for Studio-only actions.
