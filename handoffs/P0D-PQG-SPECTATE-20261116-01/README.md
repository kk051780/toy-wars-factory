# EGGRUMBLE castle-elimination spectator (independent quality lane)

P0D #470 / #218 / original author #482 / B official integrator #220.

## Why this slice, and ownership
Current private V3 host sets `EGGRUMBLE_Eliminated=true` and teleports a defeated castle owner to the lobby while the match remains active. No survivor-observation flow is present in the mapped V3 client scripts. This slice adds **only a client-side, elimination-gated castle observer**. It does not recode any 7-role abilities, terrain, core castle geometry, giant, bot AI, item, lobby queue, result scoring or ART A01. Respect #482 (gameplay author), #484 (composition), #485 (art), #487 (score), #488 (cross-domain evidence).

## Actual source delta
- New `EGGRUMBLE_Spectate.client.luau`: after own castle elimination, find the **specific existing mode arena containing own castle**. Present a small, temporary observation panel with left/right taps or arrow keys. Camera points to existing castle models in that arena only. On match cleanup or elimination-flag reset, remove overlay and restore local player's camera.
- Add precisely one mapping to the existing original-author private V3 Rojo project. No other mapped source or original-author Game file is edited.
- No new Remote, HP, damage, reward, save, inventory, matchmaking or purchase authority. Only Studio private preview runs it. The display is invisible to active players.

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
