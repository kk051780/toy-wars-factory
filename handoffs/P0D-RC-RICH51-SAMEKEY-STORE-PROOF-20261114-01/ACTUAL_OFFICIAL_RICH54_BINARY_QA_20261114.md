# P0D official RC rich54 actual binary audit — supersedes optional 53 rebase

**2026-11-14 JST; QA independent lane only. No official RC source writes, main merge, publication, paid API, PC/Codex, or automations.**

## SUPERSEDED — do not reapply old candidate patches

While this QA lane was reconciling the current official 53, the sole #220 RC integrator **already installed** the original sixskill durable DEV feature as a canonical **54-source RC profile**. Therefore the three pre-adoption rebase patches in this same folder are *historical evidence* and must **NOT be applied again** to current rich54. The private HUD rebase source is not required: the actual official54 HUD independently preserves human Idled warnings and renders SAVED only from original Game/Store-confirmed server status. Applying two HUD candidates would be duplicate work and risks a regression.

## GENUINE official artifacts downloaded and independently examined

- Immediately preceding official RC53: immutable HEAD `4b753cd34dd6629e599b0c256d2f8ab73c448cf0`, GitHub Actions `43489213284` completed SUCCESS, artifact `14068926474` ZIP SHA256 `a058a3e7d55fd4157cb5a51d654cddebddf9ba5ee3653d6903123b4a04302e1f`, real Place SHA256 `8e5fd93fedc799247eb9fbb0c61f8f4c59cb256a715631b779da818299c676fb`, **53** XML Luau Source entries.
- **FIRST SUCCESSFUL OFFICIAL RC54**: immutable CI HEAD `2e86ac4fd0d4cb67fd7c673dc4e891b2af6bdc2c`, Actions https://github.com/kk051780/toy-wars-factory/actions/runs/43491029567 completed SUCCESS, artifact `14068663217`, ZIP SHA256 `14b0a42089819f231473540355819494decff97c5e71cad893582f5490130469`, genuine unpublished Place **496794 bytes** / SHA256 **`1afdb2661b47eafa97985b27eaab5b0236d15f6f6e21863d089cebaf7e745758`**. Exactly 54 embedded original Roblox XML Script Source entries. No Studio engine execution claimed.
- Current canonical branch `rc/p0d-s1-kids-rc01` subsequently advanced for metadata to observed HEAD `54b73c9c699d1758f18f9e84a246ed66a3e7d185`. `ACTIVE.json` status says `RC_RICH54_SIX_SKILL_DEV_PERSISTENCE_COMPILED_BUILD_PASSED`, feature switch `SIX_SKILL_DURABLE.enabled=true` and original owner first-successful run `43491029567`. **The first verified 54 binary applies to its own exact build SHA, not automatically to any later metadata commit.**

## ACTUAL independently executed 26-case source, security and backward compatibility QA

`P0D_OFFICIAL_RICH54_INDEPENDENT_AUDIT.py` locally processed both genuine Places. **26/26 Python unittest PASS** incl negative mutated-Place rejection.

1. RC53→54 exactly ONE new `ModuleScript SixSkillAtomicProfile`, GitBlob EXACT original author `aeadd5a8e0d367ddfa639df161843f9a74637c87` (original author V4 Scheduler/XP models unchanged).
2. Exactly three original scripts changed: **one original Game**, **one original PersistentHatchStore**, **one V4TrialOverlay**. Remaining **50/53 original script bodies byte-identical**. New classes Script4, LocalScript9, ModuleScript41 =54.
3. New Store exact SHA256 **`c9e1c4d7a527939568127cdc7e3cee0ae2312580239b7b5bbe6bac4c657c39bf`**, equal to previously verified author alias-safe `5b06b...` patch. Original `U_<positive full UserId>` key and schema1 preserved. Unknown old `dojo`/`dojoV4` data fail-closed rather than silently losing; `trainingV4` clone+validate and canonical `UpdateAsync` callback exact. No new SetAsync key/writer.
4. `Game` retains ONE authoritative `remote.OnServerEvent:Connect`, original Game invokes `PersistentHatch.settleSixSkill(studioHatchStore,player.UserId,ticket)` only from original server-owned physical-pad+positive UID/Studio DEV store, uses JST midnight window split and server minted receipt. No second Game/Remote writer.
5. Original two RealmHunt scripts, H1 sky world, Musou Horde, egg mode, dojo rules, match UI, V4 preview bridge and original 6 model Luau scripts byte-identical. V4 bridge retains `IsFriendsWithAsync` real verified friend policy and no its own Store writer.
6. **Actual official54 V4 overlay retains** `player.Idled`, real `UserInputService.InputBegan`, and dynamic `baseWarning=if saved then...`, which resets the warning to the current server SaveStatus after real user input. It displays SAVED only when `P0D_V4_SaveStatus == "SAVED"`, otherwise the session preview. No artificial anti-idle/Remote/marketplace.
7. Negative modified .rbxlx SHA rejected. Guard does **NOT** assert Studio2client, Android, owner_FUN, real DEV DataStore login/rejoin success, or real paid release.

## Admission status / next high-value work

- **Source/native/Rojo pass** from sole #220 author Actions43491029567 and independent artifact+source audit26/26 PASS.
- **Production-grade persistent sixskill** still UNPROVEN: actual positive UserId Studio API save, leave/rejoin, two clients, Android/mobile and human FUN NOT_TESTED. Only DEV Store is wired; no public save authorized.
- Current owner FAST-RC policy: no per-feature Studio test before source adoption, but **owner Studio/API/FUN/Android batch is required before actual Roblox publication**.
- Next code work should target real in-game ability/power for four additional classes, seven true jobs, or another source-ready mechanic under SAME canonical Game and feature-level OFF rollback, while the 54 source stays as baseline. Do not build another parallel rich54 candidate or overwrite canonical Game.
- Historical public-quality S1 score 75/100 FUN_NO_GO is unchanged. No public Roblox publish/paid/main or P0-A/B/C/CAS automation changes.

**GitHub links**: original author rich54 fastlane source proposal https://github.com/kk051780/toy-wars-factory/tree/68625792b1882bd69db0342e46efd342d842bbcc/handoffs/P0D-LOBBY-V4-FOCUS-CAP-20261113-01/rc_fastlane_candidate ; canonical RC https://github.com/kk051780/toy-wars-factory/tree/rc/p0d-s1-kids-rc01/rc_fastlane .
