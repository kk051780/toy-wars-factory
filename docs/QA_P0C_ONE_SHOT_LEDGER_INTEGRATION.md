# P0-C D1 manual one-shot read-only receipt integration

This candidate is on protected DRAFT PR212 and has NOT been installed or executed on the Windows PC.

Without any ledger:
python -m tools.system_p0c_windows_scan_once --scan-once

With explicit local metadata persistence, only after independent review and OWNER opt-in:
python -m tools.system_p0c_windows_scan_once --scan-once --receipt-ledger ABSOLUTE_EXISTING_DIR/p0c-readonly-receipts.sqlite3

The selected parent directory must already exist and be owner-controlled; SQLite may briefly create a journal. First valid receipt gives READ_ONLY_RECEIPT_RECORDED_NO_ACTION and repeat gives READ_ONLY_REPLAY_BLOCKED_NO_ACTION. The record only contains work ID, nonce, comment ID, body SHA256, and UTC observation timestamp.

This is optional and does NOT activate a receiver, process commands, wake Codex, control Studio, configure autostart, perform GitHub writes, or authenticate the sender. A local DB is not cross-host CAS, and deleting or corrupting it invalidates replay guarantees. The output intentionally keeps replay_history_verified=false, and all PC execution authorizations remain false. GitHub OWNER/App metadata is never a signature.

Codex quota must be saved for one compact Windows/Studio MCP bridge operation when separately authorized. All source code and CI continue in GitHub/ChatGPT.