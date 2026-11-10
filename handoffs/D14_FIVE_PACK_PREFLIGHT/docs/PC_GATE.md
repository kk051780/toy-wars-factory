# OWNER direct Windows Codex — D14 encrypted import gate

This is a **deferred, non-executing** brief. First read latest #218/#213/#217 and PC CHECKPOINT/RESUME; verify current saved Place/Source/ZIP SHA, backup. Latest verified report: [v43-A S1 PC scoped QA #6758415195](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6758415195). A subsequent [OWNER request #6765606390](https://github.com/kk051780/toy-wars-factory/issues/213#issuecomment-6765606390) puts v43-A cold restart and D07 Gorogan ahead of D14. Unless OWNER explicitly changes that, **do not launch D14 Studio yet**.

At D14 turn:

1. Fetch this *public-safe* tool/manifest at its immutable commit; run 41 unittest checks and `--receipt`. Report GitHub ciphertext+README `5/5` or exact rejection without claiming AES/Studio success.
2. Stage all five ciphertext-only assets in an owner-only empty directory, OR stage only core three with separate explicitly checked manual workflow. The tool stages five atomically and has no `--subset` to avoid silently skipping dependencies.
3. Check whether each of five packet-specific OWNER secrets is actually available. `NO_KEY` is HOLD, not a reason to fabricate a replacement package or attempt other keys. Never log/export/upload keys. Existing CART_RAIL private key may be accessible to OWNER from this ChatGPT conversation; other four keys originate from other chats.
4. Restore **only one** full reference packet with `restore_handoff_safe.py` pinned to `d37eec1b653d060ae27568ddcd5f501da9662081`, enforcing game/work/packet/ZIP SHA. Validate SHA manifest and Luau parse; DO NOT overwrite source, and reject superseded D14 sources by commit.
5. Audit genuine D14 seats existing API before adding motion or visuals. Cart order: SEATS → CART_RAIL → VISUAL. Treat RAFT/RIDER as *optional* after independent reviewed integrations. Only one canonical seat authority, one server-owned pose stream; never grant clients movement or damage authority.
6. Use [triad trace validator](https://github.com/kk051780/toy-wars-factory/tree/5b93243006c486faf5bbe8867ce7d2702f0c0917/handoffs/D14_TRIAD_CONTRACT) on **sanitized genuine server trace** only after the PC has run Studio tests. Synthetic trace PASS is not real-game QA. Test 2/3 clients, seat 0/2..2/2, disconnect/reconnect, death, egg-carry blocks, replay, stale round/seat epoch, cart track collision, camera/motion/mobile FPS, controlled rider detach if enabled.
7. Save Place/source/checkpoint/QA to *new* local version, record SHAs. Stop→Edit→Save→normal Quit, verify only owned Studio PID has exited. Report anonymized statuses and hashes to #213/#218. Full release remains gated; no main/merge/publish/spend.

Never use GitHub comments or this document as an automatic Windows Codex trigger. OWNER explicitly directs any PC changes.
