# TRAP RAIDERS — D16 Visual EXACT original keyless 23rd source intake

**Purpose:** transport/security-only. This stand-alone Python script verifies **the 23rd original-source delivery** (D16 VISUAL_REPLICA) from a **pinned immutable Git commit**, checks the full manifest + each source byte/SHA, enforces the expected original Luau code identities/APIs, then stages all 18 original-source files into a *new directory outside the clone* with a `SOURCE_RECEIPT.json`. The original author already recovered the source at #218 [comment 6777098576](https://github.com/kk051780/toy-wars-factory/issues/218#issuecomment-6777098576). This helper itself is **not a 24th original source**.

- Game `TRAP_RAIDERS`, work `p0d-siege-v19`, method `PUBLIC_SOURCE_V1` (Issue #218 top).
- Original visual packet: `P0D-D16-VISUAL-REPLICA-ORIGINAL-PUBLIC-RECOVER-20261111-01`.
- Fixed source commit `226a5664ed50131868391289723c130d35abf48f`.
- Original manifest SHA256 `f6d18f35db3b089c897d988b2524d36a17be42af6e71fa0ba18ccc792b0d9030`.
- Original `ScaleFxCore` is a **separate** 22nd packet at `584b11ef24cf3d44695d86b505207491bbd3844e`, with separate staging helper at `72fa23177c1fdce8433a9ecc565787d1ca5dcd6e`.
- Cleanroom visual `356dcd0d26aecf7bb5ab3e7d7a697e78a59db74e` is a different implementation: **never install both**. Existing D16 cleanroom scale core `883ca3b...` and cleanroom D08 gates `ac503...`/`187722...` do NOT match the original ScaleFx API.

## OWNER Windows Codex — source receipt only (after D07 real PC QA)

Use an **isolated Git clone**, never the current PC game directory, and a **previously nonexistent output** directory. Do not execute scripts directly from an unreviewed source packet. Check this intake script first.

```powershell
$clone = Join-Path $env:TEMP 'TRAP_RAIDERS_23RD_SOURCE_CLONE_NEW'
$receipt = Join-Path $env:TEMP 'TRAP_RAIDERS_D16_VISUAL_23RD_RECEIPT_NEW'
git clone https://github.com/kk051780/toy-wars-factory.git $clone
# If the commit is not present, fetch its specific immutable source branch from #218;
# never substitute a moving main HEAD or a lookalike source candidate.
python tools/verify_visual_original.py --repo $clone --output $receipt
```

Run `tools/verify_visual_original.py` from this helper's immutable package, not the original remote package. It reads Git blobs (`git show` at pinned commit) and writes **only** to the new receipt folder. No AES key/password is needed. Expected content includes real Luau `ScaleFxClientPolicy`, `ScaleFxSnapshotBridge`, `ScaleVisualReplica` and optional `ScaleFxClientBootstrap`. It does **not** use Roblox Studio, update game files, attach RemoteEvents, change physics, grant XP, or enable live events. `PINNED_ORIGINAL_SOURCE_RECEIVED__NOT_STUDIO_TESTED` is **not** game acceptance.

Do not accidentally mount old live Remotes/duplicated client event listeners. Original visual uses a display-only server snapshot with `remainingSeconds` from the server round clock; do not convert `expiresAt` with client `os.clock()`. PC integrator must inspect and decide whether any D16 visual already exists; if yes, document `NO_OP` rather than overwriting.

### Historical original ZIP recovery remains blocked for three other packets

Original plaintext ZIP metadata exists, but raw bytes could **not** be obtained in this conversation. Metadata does not prove file bytes. This helper does not recover/decrypt them:

| Packet | Expected owner ZIP name | Expected ZIP SHA256 |
|---|---|---|
| D14 SEATS | `TRAP_RAIDERS_D14_SeatReference_v2.zip` | `475616bd21e88164158db88b3a97e33d4a9b1ce9aaa872fa7a816adf485c9fd3` |
| D16 CLOCK RAIN | `TRAP_RAIDERS_D16_CLOCK_RAIN.zip` | `bcee9a949dc897b1d9a54557a93959ccd8b0e068223310594a8d27ec4fdcea62` |
| D16 GLIDE AUTH | `TRAP_RAIDERS_D16_GLIDE_AUTH.zip` | `872e8f9ec5ef38535ee3b295bf301a612e2063835e85cae67ab87bb370aee2cc` |

When owner PC original ZIP bytes become accessible, reuse the **existing** read-only [7-archive original ZIP locator](https://github.com/kk051780/toy-wars-factory/tree/4cd58e6e4a9cfdf22d11c4da78183fce4e8192b1/handoffs/P0D-KEYLESS-D14-D16-ORPHAN-SOURCE-LOCATOR-20261110-01). Do not create another scanner, guess decryption keys, or count a cleanroom alternative as byte-identical to the original ZIP. Canonical `PUBLIC_SOURCE_V1` GitHub fixed-commit/manifest readback is required for each original.

**QA:** `python -m unittest discover -s tests -v`. The 19 local tests use synthetic temporary Git clones and do not establish actual OWNER Windows intake, Roblox Luau parser, Studio, 2-client or mobile QA. No main/merge/paid/publication/PC data edit/P0-A/B/C CAS, five Automations or other author branches.
