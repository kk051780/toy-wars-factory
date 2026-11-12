# P0-D / TRAP RAIDERS S1 V6 — verified OWNER PC Studio QA transport (NOT a gameplay pass)

This non-RC handoff was produced independently on 2026-11-12. Git source baseline is exact official RC 1263a03701211a652b99b91d2339575dc8104eff, but the included **review-only** Rojo file has three SOURCE-ONLY optional improvements (Japanese map labels, Guardian first-minute trap help, Guardian mobile right-side button). Source selection and actual Rojo build are fully audited by #231.

**Artifact source:** actual successful GitHub Actions https://github.com/kk051780/toy-wars-factory/actions/runs/43207102745, artifact ID 13939980172. Real retrieved ZIP contains exactly a 156849-byte Roblox Place XML with SHA256 4854d44d3bf0f3b9266f23b3a18aa8cda028575d0b3d400775f2f9d4df73f63c. Complete 21/21 real embedded Luau scripts are byte- and Git-blob-matched to fixed CI source SHA 64bd4d1110bdf59df12fffb2edd051f2c8a25b3e. Review source branch exact SHA 09e118c9af3a7f30c2763b956ab80c4056d2a09d also matches 22/22 game source/project blobs. The package does NOT carry keys or private Roblox account data.

**Deliverable:** a fresh user-attached local zip \`P0D_S1_V6_Studio_QA_Safe_Transfer_20261112.zip\`, 54,544 B, SHA256 75b8a701d5ea09ea4d065f8eb3e6136d766f191f9d79e07973f8775d2b6b51d8. The full zip contains real \`.rbxlx\`, original exact-source audit, local 26-scenario NOT_TESTED card, Japanese operator checklist, manifest, offline stage program and 17 actual local Python unittest negative tests. It was unpacked into a **fresh** temporary folder and the 17 tests all passed again. This zip is provided directly in the ChatGPT conversation; sandbox attachments are NOT GitHub-hosted files. If unavailable, regenerate the exact place from CI source branch and re-verify the SHA.

### SHA256 inventory of the local ZIP entries

| File | Bytes | SHA256 |
|---|---:|---|
| TRAP_RAIDERS_S1_V6_THREE_UX_REVIEW.rbxlx |156849|4854d44d3bf0f3b9266f23b3a18aa8cda028575d0b3d400775f2f9d4df73f63c|
| SOURCE_AUDIT.json |5352|e5415d986fb15da8e054954b997bc0e616b1227e195141dba6868eb8f5a04ad3|
| STUDIO_QA_CARDS.md |4155|0fca3f0238da44a9ec2fb94dbd2521632b891b713cfa06a125a04f8529456d2c|
| SCENARIOS_NOT_TESTED.json |3188|62882c6eb152788e3671b28e840c96d0a6ce719b4fcb66d6b22d83dd744b6866|
| README.md |4079|7361c812ffb374fa06515a90436b7215746929b4db8e01c5171fa3f6b4fd7a65|
| prepare_studio_qa.py |6677|f8d16eaab68f1d32537c61a57ec2c65187a9e9ed2d10f402b53b95285b3deeef|
| test_prepare_studio_qa.py |5909|393a08ea0a84a12ab371214a0aac736abeb932215fede191827552bbdc3e2461|
| TRANSFER_MANIFEST.json |1180|26b8bdc44ca071aac06b8fd2753869d551e8b38c36ba30ac88ebed56f416a134|

### How OWNER can run later on Windows, without Codex

1. Unzip entire bundle to a fresh private folder. Do not overwrite existing Windows Place/PC checkpoint or Git HEAD.
2. Python: \`python prepare_studio_qa.py\` is **offline inspection only** and must print \`SOURCE_INSPECTION_PASS_NOT_STUDIO\`. There is zero Studio/Roblox interaction.
3. Back up the actual current Windows PC latest place/checkpoint separately; confirm its SHA. Create an empty QA parent folder and run \`python prepare_studio_qa.py --prepare --destination C:\TRAP_RAIDERS_QA\`; an **exclusive** new subfolder \`P0D_S1_V6_QA_4854d44d3bf0\` is created, refusing overwrite/symlinks/relative or missing destinations. Repeating will reject.
4. Open ONLY the newly created copy in Roblox Studio without publishing. Test actual 2-client attack/egg/win/rematch, Guardian trap, team-scoped server authority, physical mobile thumbstick and UI, initial 60 seconds with human, FPS, save/reopen, normal Studio exit. Record private raw logs, no personal data in GitHub.
5. \`SCENARIOS_NOT_TESTED.json\` contains 26 IDs, **all still NOT_TESTED**. User/Studio QA updates only a separate real evidence record with actual timestamps/hashes. The official #220 current final receipt validator is pinned to an older RC and cannot legitimately be used as a PASS for this new binary; the sole integrator must adopt the new RC and revise authorized boss scope/pins first.

### Actual tests and blockers

Local Python \`test_prepare_studio_qa.py\`: **17/17 PASS** (integrity baseline, inspect no side effects, isolated copy, second copy denied, 2 game corruption cases, forged audit PASS, forged scenario PASS, duplicate scenarios, missing audit, tampered docs, bad dest relative/missing/symlink, source symlink, CLI missing dest, manifest exact). Fresh-unzipped retest **17/17 PASS**, ZIP encrypted entries **0/8**. **GitHub CI for this handoff kit itself: NOT_RUN**; historical actual CI for the underlying game artifact: PASS. Real Studio 2client/mobile/physical engine: **NOT_TESTED**, game official global score only prior audited 75/100 (delta0), S1 boss D07/D08 OFF, release APPROVAL NO.

Collision protection: this packet is ONLY source artifact safe transport and operator QA kit. It neither replaces #220 exclusive Studio evidence validator, nor #218 S1 passive client probe, nor the already completed #231 3-way Rojo build, nor separate ongoing five-source integration. No writes to official RC/main/merges/Roblox publish/payments/protected P0 A/B/C or 5 scheduled automations.
