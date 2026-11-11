# S1 integrator RESUME/checkpoint — 2026-11-12

- OWNER selected this Chat as new sole integration writer via [#220](https://github.com/kk051780/toy-wars-factory/issues/220#issuecomment-6807677640), superseding the inactive previous Chat instance's write role only.
- Prior **official** SHA: `35d7d0525388e885aac8281eff2315a59831e0cf` (15 source/files + manifest; 80/80 original offline).
- Source-only 30-file candidate SHA: `b103389e2089f9ff5a08984fe2f8f6f02aa8b1bc`, independent original SHA256 30/30 PASS (source QA not real engine).
- First Git blob subtree adoption commit: `17ffd5c28bf15aeefa5f524291534f064f74029f`; git RC update used `expected_sha=35d7d0525388e885aac8281eff2315a59831e0cf`, `force=false`, successful. This derived from original unchanged `src` candidate Git tree `b95f91fcf802607ff9d5f45a816553b295f68b8a`. Check `git rev-parse HEAD` again before any next write.
- This docs/receipt overlay will be a **second** RC commit, with manifest and source source-lock consistency. No modifications to any `src/*.luau`.
- S1 core is runnable in concept/source but unverified by final actual engine. D07/D08 gated flags OFF. Studio, human play and live publication NOT DONE.
- On a branch collision or mismatched SHA, stop; never force-overwrite another Chat's update. The prior old baseline remains retrievable as its immutable 40-char Git commit.
- Latest owner Windows private PC Place/source may differ from this standalone source and is protected. Chat import is not a PC restore; preserve both.
- To roll back for review, inspect `35d7d0525388e885aac8281eff2315a59831e0cf` on a new disposable branch; never force-reset current official RC and never edit main.
- Next integration action: independent QA on true current official RC source and first itemized #220 score. Codex only after near-final and direct OWNER instruction.
