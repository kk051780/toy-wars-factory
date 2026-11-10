# P0-D keyless recovery ledger — public-safe tools only

This folder is **not a gameplay source delivery**. It verifies a user-private, **unencrypted** ZIP that includes four original sources recoverable in the current ChatGPT conversation. Commercial game Luau/source files and the keyless ZIP are **not** present in this PUBLIC repository.

* Prepared source packet IDs: D13 Siege, D17 Privacy Metrics, D14 CART rail motion 02B, D14 OUTBOUND server visual publisher.
* Current recoverable sources: **4 packets / 35 original source files**. Local ZIP verification and Python regression **31/31 PASS**. Plaintext original ZIP digests match the previous encrypted packet envelopes.
* GitHub destination requirement for **this safe private staging option**: `kk051780/trap-raiders-private-source`, visibility `PRIVATE`; currently not created. Repo owner must create once and grant Codex/ChatGPT app access. A separate existing P0-D PUBLIC_SOURCE_V1 proposal exists in #218; this folder does not assert that a request for “no keys” automatically gives permission for irrevocable PUBLIC disclosure.
* Never put a per-packet key or recovered secret in public issues. This material is purely integrity tooling, **no PC Studio work**.

Test: `python -m unittest discover -s tests -q` (the source-bundle verification is skipped in this public-only copy). For actual recovery, run `python tools/keyless_migrate.py --bundle-root <private unpacked ZIP>`, then optional `--stage-to <authenticated clean PRIVATE repo checkout>`.

The authoritative #218 issue includes all delivery-mode decisions; if two rules conflict, do not silently change the disclosure scope. Escalate to OWNER rather than publish source to public under an inferred permission.
