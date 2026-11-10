# P0-D / P0-A 提案：鍵探索停止、固定の秘密受領経路へ（2026-11-10 JST）
**STATUS: PROPOSAL FOR SHARED P0 CONTRACT, NOT AUTOMATICALLY ADOPTED BY OTHER CHAT LANES.**
work_id=`p0d-siege-v19` / Public repository=`kk051780/toy-wars-factory`

## Problem observed in genuine PC evidence
The OWNER Windows Codex report [#213 #6766018726](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6766018726) explicitly marked the **GOROGAN VISUAL** packet `P0D-D07-GOROGAN-VISUAL-20261110-01` (commit `5128e288...`) and **GOROGAN SERVER AI** packet `P0D-D07-GOROGAN-SERVER-AI-20261110-02` (commit `80483ad...`) **BLOCKED: keys not available to Windows**. Those missing AES-GCM keys cannot be guessed and a valid public ciphertext does not provide plaintext on its own. Do not report Windows restore PASS without genuine AES tag authentication + expected ZIP SHA.

## Two explicitly different safe delivery methods

### Method A — owner-local KEYLESS original ZIP for design/art/other author-owned deliverables
- Source creator keeps original confidential bytes private in ChatGPT conversation/Library.
- Give OWNER a **single normal ZIP** (no external key and no nested historical ZIPs), with a public-safe SHA256 and manifest. Owner downloads directly to Windows **Downloads** or `%USERPROFILE%\TRAP_RAIDERS\handoff\inbox\`.
- An independently reviewed **public-safe deterministic verifier script** reads only those two known paths, checks fixed outer ZIP SHA + internal manifest SHA/path safety, and stages into `%USERPROFILE%\TRAP_RAIDERS\handoff\staged\` without touching the game.
- NEVER upload the unencrypted commercial ZIP to a public branch, Issue, PR or CI artifact. Integrity SHA is **not confidentiality**. Nonautomatic PC receipt until OWNER downloads it.
- D18 V7 is a working implementation of this pattern: [README](https://github.com/kk051780/toy-wars-factory/issues/219) and `tools/p0d_d18_receive_no_key.py`.

### Method B — existing GitHub AES ciphertext + strictly fixed OWNER LOCAL key files
- If an original packet owner already encrypted a GitHub envelope, that packet remains encrypted. The real key comes only from the original authorized sender/OWNER, through a private channel.
- **Proposed deterministic key landing path:** `%USERPROFILE%\TRAP_RAIDERS\handoff\secrets\<exact_packet_id>.key` on owner's Windows PC; the UI/docs may use a separate safe local import script and OS file permissions; the actual key bytes are NEVER on GitHub/Issues/CI/logs/command args.
- Each packet manifest needs `packet_id`, `work_id`, `ciphertext fixed commit`, `ciphertext sha`, `expected restored ZIP sha`, `key_source=OWNER_LOCAL_ONLY`, and the exact **non-secret key filename**; the restorer verifies against those IDs/AES-GCM AAD. Do not search across dialogs, repos, entire disks or other users' secrets.
- Missing/ambiguous/unreadable key => `BLOCKED_KEY_UNAVAILABLE` and stop just that packet. Never force decrypt, invent a substitute key, reuse unrelated keys or reduce cryptographic checks.
- The original D07 packet authors should either re-provide their actual original keys privately through this fixed route **or** repackage the actual private source as owner-local KEYLESS ZIP for Method A. **Another ChatGPT lane cannot reconstruct lost AES-GCM plaintext from the ciphertext**.
- This is a **proposal**, not license for the D18 chat to change other packet owner's secret management. Reviewer, authorization and P0-A CAS gate remain required for code integration.

## Acceptance and fail-safe states
`PUBLIC_METADATA_VERIFIED` is separate from `OWNER_PRIVATE_BYTES_RECEIVED`, `SHA_RESTORED_PASS`, `PC_STAGE_PASS`, `STUDIO_INTEGRATION_PASS` and `STUDIO_CLOSED_VERIFIED`. A GitHub readback alone meets only the first state.

Source/control boundaries: no direct main write, unreviewed merge, Roblox publication, real money, public secret/code exposure, automated PC commands, P0-A lock bypass or extra costs. The action to run Codex belongs only to OWNER.
