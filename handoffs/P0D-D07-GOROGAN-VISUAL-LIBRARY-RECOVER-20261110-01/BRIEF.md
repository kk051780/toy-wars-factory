# D07 Minimal 3D Gorogan / OWNER-Codex Brief

**Choice:** one original giant, one stage, no gameplay changes. S1 (then S3 if S1 passes) must display a 20-stud low-poly Gorogan in a short server-decided neutral boss event. The presentation uses a yellow glowing core, moss texture from stock Roblox materials, neon impact ring, 2-second readable telegraph, and automatic fade/remove at <=14 seconds or true RoundEnd.

**Candidate UX:** A child should see the giant coming, understand the ring and avoid it, with a no-flash/reduced-motion option. Display is deliberately not a real attack: no deceptive win/loss changes. No stock/third-party asset purchase required.

**Acceptance (Studio, NOT performed here):** first final v37 saved Place QA; v39 bonus ledger QA; 1 external valid START event, 0 client-initiated spawns; 2 clients observe same server event, 1 Gorogan per round; 2s warning becomes ACTIVE, <=3 stomps, 14s max local TTL; abnormal seq/round/stage/coords ignored; death/replay/round transition clears local model; no Raycast/Touch/Collide and no game HP changes; 20-second mobile emulator FPS with low detail and reduced motion ON/OFF; local Studio instance normal stop/save/quit/PID disappearance. If any of these fail, block incorporation, record failure; no public deploy.

**Dependencies:** D01/D02/v37; old v40 ChaosEventCore **single event authority**, prior v39. No D08/D12 weather scheduling, D16 effects, D17 catalog, D15 traps or NPC behavior edits.
