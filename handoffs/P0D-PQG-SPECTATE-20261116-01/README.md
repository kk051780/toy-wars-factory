# EGGRUMBLE castle-elimination spectator (independent quality lane)

P0D #470 / #218 / original author #482 / B official integrator #220.

## Why this slice, and ownership
Current private V3 host sets `EGGRUMBLE_Eliminated=true` and teleports a defeated castle owner to the lobby while the match remains active. No survivor-observation flow is present in the mapped V3 client scripts. This slice adds **only a client-side, elimination-gated castle observer**. It does not recode any 7-role abilities, terrain, core castle geometry, giant, bot AI, item, lobby queue, result scoring or ART A01. Respect #482 (gameplay author), #484 (composition), #485 (art), #487 (score), #488 (cross-domain evidence).

## Actual source delta
- New `EGGRUMBLE_Spectate.client.luau`: after own castle elimination, find the **specific existing mode arena containing own castle**. Present a small, temporary observation panel with left/right taps or arrow keys. Camera points to existing castle models in that arena only. On match cleanup or elimination-flag reset, remove overlay and restore local player's camera.
- Add precisely one mapping to the existing original-author private V3 Rojo project. No other mapped source or original-author Game file is edited.
- No new Remote, HP, damage, reward, save, inventory, matchmaking or purchase authority. Only Studio private preview runs it. The display is invisible to active players.


## Native behavioral acceptance — same-source execution, not engine certification
- [run #43801048568](https://github.com/kk051780/toy-wars-factory/actions/runs/43801048568) **SUCCESS** on source HEAD \`895caeef56492d4290101929ae916f67a73450c0\`: the unchanged **original spectator CLIENT LocalScript** is executed under the fixed pinned native Luau VM using explicit small Roblox API fakes. Real handlers tested: active no camera takeover; server-acknowledged castle elimination; 44x44 touch controls; keyboard consumed/not consumed; strict TEAM/BR arena isolation; player elimination reset; match arena deletion; camera type, subject, lookAt and Focus restoration.
- Negative control **three mutation variants rejected by actually executing** the modified real source: flipped elimination test, removed own-arena membership test, disabled GUI cleanup. Static proof is not used as gameplay evidence.
- Test generator \`tools/make_native_spectator_harness.py\`; CI \`.github/workflows/p0d-eggrumble-spectator-native-lifecycle.yml\`. The VM mocks cover those calls but **do not simulate Roblox's physical camera, replication timing, R6/R15, mobile safe areas or server disconnect**. Real Studio 1+15, 2+14, Android15min and OWNER FUN are still not tested.
- Next mandatory verification: same FINAL head 22-source and 27-source actual Rojo SourceExact results; original authors #482/#484/#485/#487 HEAD drift reconciliation (#490/#491), then sole authenticated #220 nonforce CAS official RC adoption.

## Rollback
Delete the single `EGGRUMBLE_EliminatedSpectate` mapping from the V3 project; no migrations. Discard this isolated draft. No official RC/main/Roblox publication change.

## Acceptance
- Static/structural Python checks are separate from real client motion. 7 contracts now include **at least 44×44 px** phone touch targets, while active-game GUI stays absent.
- Implemented two pinned CI workflows: (1) original 21 + spectator 1 = 22 actual native Luau and source-exact Rojo Place, (2) **reuse the unchanged original #484 26-source composer** (original #482 + #485 ART + #487 SCORE + #484 spatial fixes) and append only the spectator LocalScript for 27-source true Rojo verification. Do **not** claim the prior build's success for a later amended HEAD; verify latest same-HEAD runs before adoption.
- Actual Roblox engine/client camera behavior is still NOT_TESTED; native parser and Rojo XML are not Studio tests.
- TODO: Roblox Studio 1+15 and 2+14 clients: remove one human castle while another survives; cycle same-mode castles, verify other-mode non-leakage, respawn does not reset camera, and round end restores Player camera.
- TODO: Android low-end touch target size/FPS & #420 ART/FUN + OWNER acceptance.
- TODO: #220 genuinely authenticated source-selective CAS and same-HEAD official RC build/ACK.

**Not READY / not official RC integrated / not a claim of Studio PASS.**
