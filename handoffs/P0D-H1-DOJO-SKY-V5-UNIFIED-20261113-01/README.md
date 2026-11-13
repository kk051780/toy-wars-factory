# P0D H1 private integrated preview — original 45-source Dojo + original V5 Sky Ground Docks

2026-11-13 JST | TRAP_RAIDERS | p0d-siege-v19 | adoption_id=P0D-FUN-H1-001

## Actual change

The previous #220 rich H1 private build has B42 egg contest, First90 waypoints,
Musou Horde V7, physical sky castle, latched one-player Studio trials, passive
four-step on-screen carry observer, plus *actual* Beast/Weapon AFK dojo pads.
Its original 45-source immutable baseline is commit
`79804116b0a144a33c6466340cfb476eefa3ca4d`.

This independent **candidate** preserves 44 out of those 45 actual Luau
files byte-for-byte, replacing only the already-present original
`server/H1FunWorld.server.luau` with the exact source from the other author's
V5 ground-dock world at commit `f607cf4de4ac50e1e886adbd5b9f6070fe5c0450`,
blob `7a90affd4eb7eebcdfba39d833a2875ff665d5cf`.
No second Game, Remote, Store, scoring authority, world, paid feature or
DataStore key is added.

The V5 scene adds **four symmetrical solid, free ground-to-sky ramps** to
reduce the potentially blocking ~1.9-stud original path lip. Existing
S1 eggs, role skills, Horde/Dojo and score logic are identical. Terrain,
character collision, prompts, real physical walking and camera are **not**
proven without Roblox Studio. V5 four grounded ramps are source-proven only.

## Reproduction and acceptance evidence

Run from a clean checkout of **this isolated branch**, never over an
existing generated dist:

```sh
python3 -B -m unittest discover -s handoffs/P0D-H1-DOJO-SKY-V5-UNIFIED-20261113-01/tests -v
```

The assembler recreates the prior 45-source game from its immutable
author sources, asserts the exact original World blob, copies the actual
V5 author source (SHA1 Git blob checked), and asserts the **only** source
difference in the entire 45-source private game is H1FunWorld.
A dedicated workflow additionally attempts **native pinned Luau compilation
45/45 and a genuine unpublished Rojo .rbxlx build with 45/45 exact source
readback**. Do not label those PASS until a successful Actions run is observed.

## Studio test requested (owner manual/private only)

Open the candidate .rbxlx from its own successful workflow artifact in a
separate unpublished Studio Place; first back up the user's existing Place.
Verify RED and BLUE from ground to sky without jumping, true egg carried on
sky and server deposit, no blocking at score prompt; also try Beast/Weapon
pad and 1v1 round then disconnect. Follow with two-client and mobile
landscape testing. Record actual Output and owner FUN impressions. On failed
physical approach, revert to original fixed 45-source private build; do
not mix more worlds or modify the user's current Place.

**Not tested here:** real Studio 1/2-client, Android, real user FUN, retention.
**Not selected:** #250 official RC adoption; original product's B42 private
baseline remains selected, optional H1 45/V5 is **not** selected. No automatic
launch, merge, main, publish, spending, paid features, Windows Codex, or
P0-A/B/C/CAS/5 automation modifications.

**Next owner:** #219 product DRI + #250 select after actual trial,
then #220 sole integrator reviews minimal diff and official SOURCE_LOCK.
No other chat may edit #220 official RC as a side effect of this candidate.
