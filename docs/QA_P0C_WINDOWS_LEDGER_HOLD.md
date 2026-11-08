# P0-C C2E Windows ledger fail-closed safety decision

Source audit: https://github.com/kk051780/toy-wars-factory/issues/204#issuecomment-6719262373

The SQLite prototype uses path checking and later sqlite3.connect, which is not TOCTOU-safe when a Windows attacker can replace symlinks, junctions, ancestor reparse points or alter ACLs. This is not a validated Windows persistence implementation. The safe interim change is to disable ledger recording on sys.platform win32 at both CLI and library entry points, before provider fetch / path open. Do NOT claim this fixes the root path security problem. Standalone no-ledger scan is still a bounded no-write GitHub GET diagnostic. No Windows receiver is installed or active.

Enable Windows durable receipts only after fixed owner-only directory, ACL + reparse + race-safe open design, tamper handling and independent authorized host test. Alternatively design authoritative provider-backed CAS for execution claims. GitHub OWNER and connector labels are not execution consent; no command, Studio, Codex, merge, publish or paid API is authorized. Codex remains a short-use PC/Studio bridge only.
