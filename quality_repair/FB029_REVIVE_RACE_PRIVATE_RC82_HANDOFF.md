# FB029: Mage resurrection spawn-order race repair / all-FB020…029 cumulative gate

**2026-11-15 OWNER「つぎ」**。FB028の正しいPlaytest Placeを固定親として読み、魔法使いの前線蘇生と既存 `assignSpawn` の scheduler が競合して、死亡地点への蘇生が通常のチーム拠点に上書きされる実コード上のリスクを修復。

## 実コードの改修（企画書ではない）
- Server-owned `fb029ReviveArrival[ally]` を **`Player:LoadCharacter()` より前**に登録。TEAM/round-epoch/5秒expiry/本当の死亡地点を保存し、クライアントには位置を送信しない。
- 元 `assignSpawn` が復活を処理するとき、ticketを一回だけ消費して従来の拠点スポーンに優先させる。Ticket不正（別ラウンド/別TEAM/期限切れ/Studio外/LOBBY）は元スポーンを使う。成功時のみ read-only 属性 `FB029ReviveSpawnApplied` に round serial を記録する。
- Original `fb027Tick` の既存Game0.5秒tickで未消費ticketのexpiry/team/phaseをclean。PlayerRemovingでもclear。
- **源コード再現器** `quality_repair/fb029_revive_spawn_race_patch.py` は元private .rbxlx SHA256固定、Game1 sourceだけ実変更、他81のbyte-exactを照合、XML再書込み/期待Place SHAまでfail-closed検証。ユーザーには完成Placeとpatcherを同一ZIPで納品。

## 出自・物
- 親FB028 `.rbxlx`: 865812 bytes / SHA256 `7981960d1f3027d7c411f7ce9de4e3e467011d59183d758cab77b2fa717d352d`
- **FB029 `.rbxlx`: 867450 bytes / SHA256 `f43d1a0a9b5577fc3022541d929d34fa0c5fead829a43fdd20afa855b77f7511`**
- **PRIVATE ZIP**: `TRAP_RAIDERS_RC82_FB029_REVIVE_RACE_FIX_PLAYTEST.zip`, 239666 bytes / SHA256 `6a876ad83e2d4dbcefbb3694bdbf4675cd7fcc1a15da8aad123b73e7c9667b9d`
- FB028 original Game Git Blob `a49992ce07392aef2a2e014ad8d5de5c6797177f` → FB029 `163b32e04853f24e4c8b27003b24ed068904501f`。
- 82 Script source XML解析、Gameのみ1本変更、他81本 byte-exact。より古いprivate品質ゲートRC82との累積差分は**5原本(Game/LobbyDojoIsland/Owner361CastleBattlefield/SevenJobsRules/TrapRaidersHUD)のみ**、残77 source一致。**旧候補のsource-lockを現在の正式RCと同一だと偽らない**。正式RC HEADは今回GitHub照会時 `d2f3ed1a47558fdaf07be0181c83c698bdb2ce34` のままで、認証済B writerによる成果統合は0。

## QA
- 実82源、Game1, 同じ再ビルドbyte-exact、誤親/二重実行拒否、Round/Team/TTL/phase/Studio制約、FB020-28全機能の元ソース保全、ZIP byte&CRC、リモート一意、サーバーのspawnスケジューラ順序を**純Python model**で両順/負例比較→**55/55 offline source and model checks PASS**。
- Native Luau/Roblox Studio/Rojo/Android/実Human revival/OWNER FUN は **NOT_RUN**。ソース差分を正式採用済/実機合格と扱わない。
- 新たに複数のRuntime authority/Client Remote/課金/メイン変更を追加しない。#297 Game作者が元源ハンクだけを既存AUTH/CLAIMで取り込み、#220 B sole writerが最新同HEAD native/Rojo/source-lock・非force CASのうえ真正RC統合。YELLOW記録の上開発RCは前進、RED重大エラーは停止。
- **Studio再試験:** 2client 片方が魔法使い、味方が死亡→22stud内でX。死亡中のLoadCharacterと自動Respawn済の2ケース、両者で本当のbeacon位置に出現するか、別TEAM/phaseの不正な復帰なし、試合終了後のticket残留なし、F9/Attribute確認。実測出来なければPRODUCT_NO_GO。
