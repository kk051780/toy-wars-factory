# PRIVATE-only keyless recovery option for historical source packets

This is a **keyless fallback/transition mode**, not a change to the existing game mechanics or a release decision.

* Set up `kk051780/trap-raiders-private-source` as **Private** from GitHub's `New repository` menu. Existing `toy-wars-factory` stays Public for issue/QA metadata.
* Grant the connected GitHub App and OWNER's Windows Codex account access once; there is **no AES password or packet decryption key to distribute**.
* Download the **PRIVATE** ChatGPT ZIP (4 packs) locally. Verify with `python tools/keyless_migrate.py --bundle-root .` in its extracted root.
* With `gh` authenticated and a clean checkout of the exact Private repo on a new non-main branch, stage with:

  `python tools/keyless_migrate.py --bundle-root <private-bundle-root> --stage-to <private-repo-checkout>`

* The verifier fails closed if `gh repo view` cannot establish visibility PRIVATE or if branch/origin/check-out does not match. Review `git diff/status` and commit/push **only to the dedicated non-main branch**. The tool does **not** commit/push/merge.
* The public #218 report contains hashes and PRIVATE fixed commit only. `PRIVATE_READBACK_PASS` is not `STUDIO_PASS`.

Other legacy encrypted packets cannot be decrypted without keys just by changing the rule. The creating ChatGPT chat or OWNER PC must supply the original plaintext ZIP, or rebuild equivalent source under a **new identity** with fresh tests. Never assert byte-identical recovery without the original ZIP.
