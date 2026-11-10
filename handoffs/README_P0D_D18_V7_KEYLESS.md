# P0-D D18 v7 — ONE-FILE OWNER-LOCAL KEYLESS HANDOFF
as_of: 2026-11-10 JST | game_id: TRAP_RAIDERS | work_id: p0d-siege-v19
packet_id: P0D-D18-COLLECTION-ATLAS-20261110-01
revision: WAVE5_NO_KEY_HANDOFF_V7
owner_lane: P0D-CHAT-MARKET-COLLECTION-ATLAS (DESIGN_ONLY)

## The one file and its immutable evidence
**OWNER PRIVATE DOWNLOAD, NOT stored in this PUBLIC GitHub repository:**
`TRAP_RAIDERS_D18_V7_NO_KEY_OWNER_TRANSFER.zip`
- size: **571,217 bytes**
- **SHA256: `0e1d696161b16b2c63370c6021421ecdf22b12f3108932a47e06da366ba56fb5`**
- No password, AES decryption key, external hidden key file, network secrets, nested prior-version ZIPs, or ZIP encryption.
- Confidential unpublished business/creative data inside! Store only in the owner's ChatGPT private Library or local Windows PC; **never commit its plaintext to this public repo**.
- ChatGPT private Library: `/TRAP_RAIDERS/企画室/TRAP_RAIDERS_D18_V7_NO_KEY_OWNER_TRANSFER.zip`.
- Contains original 648-entry JSON, 66 curated editorial entries in one flattened 648-entry JSON, new 12 item overlay, 12 Japanese original hero stories, 33-sheet Excel, summary, tests, owner-local intake guide, public-safe verifier source and per-member SHA manifest. 10 ZIP entries with no nested archives.
- Excel v7 separately in private Library `/TRAP_RAIDERS/企画室/TRAP_RAIDERS_COLLECTION_ATLAS_648_v7.xlsx` (322,348 bytes; sha256 `1b316a5b8e922231e19d749b26cb3931de497d37ce4d19addaf07c4f60837e2a`).

## Single owner action (Windows PC, not Android)
On the PC that runs Codex, open the ChatGPT artifact link and **download the above one ZIP**. Keep its exact filename in **Downloads**, or explicitly move it to:
`%USERPROFILE%\TRAP_RAIDERS\handoff\inbox\TRAP_RAIDERS_D18_V7_NO_KEY_OWNER_TRANSFER.zip`

No other secret or key is needed. PC Codex must not search Gmail/GitHub Secrets/entire hard drives for a key.

## Windows Codex actions (only after OWNER explicitly instructs)
1. Re-read latest #218 coordination, #213 true Studio/local saved Place, #217 release/CAS. Protect current local checkpoint and previously working game. Read current priority work, do not preempt PC tasks.
2. Fetch this branch's **immutable commit**, inspect `tools/p0d_d18_receive_no_key.py` (pinned file SHA256 `9a09954fc3f1ef67b83ade428b84d7221237b7d9ef59e2a697b020905c8fad48`; use GitHub blob readback). Only this public-safe source verifier is fetched from public GitHub; not the confidential ZIP.
3. Run with Python 3 on the owner's PC from the isolated workspace:

```powershell
py -3 tools/p0d_d18_receive_no_key.py --expected-sha 0e1d696161b16b2c63370c6021421ecdf22b12f3108932a47e06da366ba56fb5 --verify-only
py -3 tools/p0d_d18_receive_no_key.py --expected-sha 0e1d696161b16b2c63370c6021421ecdf22b12f3108932a47e06da366ba56fb5
```

If the current checkout lacks `tools/p0d_d18_receive_no_key.py`, use this handoff branch's fixed-commit file (do not expect it in main). The verifier checks **only two exact input paths** (Downloads and inbox) when no `--archive` is supplied; it never scans the disk. **If neither exists, or both exist, it stops**. SHA mismatch, bad inner digest, duplicate member, archive traversal, symlink, encrypted ZIP, excessive decompression, wrong game/packet, malformed catalog, or stale output folder all **FAIL CLOSED**.
4. After validation, extraction only to:
`%USERPROFILE%\TRAP_RAIDERS\handoff\staged\D18_V7_0e1d696161b1`
No automatic copy into Roblox Studio, game source, GitHub source, main, real wallet, or any production gameplay.
5. Inspect `catalog_flat_648_v7.json` (648 records, **66 individually authored**, **60 of 72 flagships**). Run `py -3 test_editorial_v7.py` from that staged directory. It has **110/110 structural design tests PASS** in the authoring environment. No claimed Studio/Luau/children preference test.
6. Separate public-safe receiver tests `tools/test_p0d_d18_receive_no_key.py`: **11/11 synthetic negative/positive tests PASS**; specifically wrong SHA, bad inner SHA, zip-slip, duplicate member, two candidate files and duplicate staging are rejected.

## New v7 editorial content and integrity
- Each original category still has exactly 108 entries: BE/SP/VE/WE/ZO/TR; 12 worlds. No legacy source ID/name/rarity/category overwrites; original V1 base ZIP SHA `72486fad3490cb1e71de1f11b7afe55385f95587d305eb61e4ad44395aa82dda`.
- Prior v2 six COMMON + v3/v4/v5/v6 48 flagship + **new v7 twelve flagship** = **66/648** distinctly curated drafts, **60/72** curated flagship drafts. **582/648** entries and **12/72** flagships still require real editorial rewrite.
- New IDs: ZO009,TR018,BE027,SP036,VE045,WE054,ZO063,TR072,BE081,SP090,VE099,WE108. Preserve all original identifiers and rarity.
- The 12 new stories are each independently authored with distinct flaw, silhouette, keepsake, 3-scenes, quiet idle/tap/defeat/victory, always-available FREE unlock proposal, optional linked story illustration and mobile part budget. These are CONTENT PROPOSALS, NOT implemented quests, paid rights, or NPC abilities.
- Don't implement each rarity as extra PvP HP/damage/speed/hitbox. No paid random eggs, manipulated scarcity, copyrighted third-party character imitation, or forced purchase UI.

## Cross-P0 missing-key approach (existing CODE ENVELOPES, not D18)
The D18 local ZIP is intentionally keyless. The original D07 GOROGAN VISUAL packet (`P0D-D07-GOROGAN-VISUAL-20261110-01`) and AI packet (`P0D-D07-GOROGAN-SERVER-AI-20261110-02`) are **still AES-encrypted** in public GitHub and were marked **KEY_MISSING** in the Windows PC #213 report. This D18 change does NOT recover their keys.
To avoid future searches, ask the **original packet author/OWNER** to either:
- A: securely deliver one **owner-local plaintext original ZIP** (not on public GitHub) with a fixed SHA, where the author actually possesses the original; or
- B: securely stage each original key at a **fixed per-packet local file location** beneath `%USERPROFILE%\TRAP_RAIDERS\handoff\secrets\<packet_id>.key`, unreadable in public; have the authorized owner-side verifier read that exact path, validate packet_id/AAD/ciphertext/ZIP SHA; never log the secret and never guess/bruteforce it.

If no authentic key and no owner-local author archive exist, keep those specific D07 packets **BLOCKED**. Never remove encryption from ciphertext or publish source/keys to bypass the gate. A proposed cross-P0 policy note is kept in this branch; adopting it for other workers requires their owners/guards to review.

## State and boundaries
`DESIGN=66/648` / `FLAGSHIPS=60/72` / `AUTHORING_STRUCTURAL_TEST=110_PASS` / `RECEIVER_SYNTHETIC_TEST=11_PASS` / `PUBLIC_SOURCE_FILE=PINNED` / `PRIVATE_ZIP=NOT_ON_PUBLIC_GITHUB` / `WINDOWS_OWNER_FILE_TRANSFER=NOT_OBSERVED` / `PC_RESTORE=NOT_TESTED` / `STUDIO=NOT_TESTED` / `REVENUE=UNKNOWN`.

No main writes, unreviewed merge, production Roblox publication, purchases, P0-A/CAS bypass, secret disclosure or extra spending.
