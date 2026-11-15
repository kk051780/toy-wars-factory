# FB024：物理3Dロビー／7職展示台／本人出撃ゲート（PRIVATE RC82）

**2026-11-15 OWNER「つぎ」実装スライス**。FB023拾得アイテム累積Placeを実親として、元のゲーム以外を生成し直さず、既存 LobbyDojoIsland + Game + TrapRaidersHUD の3 Lua源だけを最小変更してStudioで試せるものにした。関連 #364 #219 #470 #220 と作者 #297/#376。

## 完成ファイル
- 親 `TRAP_RAIDERS_RC82_FB023_LOOT_PLAYTEST.rbxlx` 809461 B / SHA256 `113b9e33b8ec80cc3d41bdaa13ee40bcbece7a9597f6cea6e9ef3beaa8211677`
- **新試遊** `TRAP_RAIDERS_RC82_FB024_PHYSICAL_LOBBY_PLAYTEST.rbxlx` **818203 B**, SHA256 `0c88d572f7fb08df0595ebed5d8cb71d689852ed8db88ee7ffbf7b472bf72b15`
- **ZIP** `TRAP_RAIDERS_RC82_FB024_PHYSICAL_LOBBY_PLAYTEST.zip` **230014 B**, SHA256 `a58b3a7aea6ffdbd192a67abd4e185a37edfd035dbf478f58067c8894e1daf76`
- ZIP contains exact .rbxlx, complete reproducible patcher `SOURCE_PATCH.py` and source lock `RECEIPT.json`, with `README.txt`. PRIVATE OWNER download delivered in ChatGPT. Source changes 3/82, other79 exact unchanged.
  - Game prior Git blob `522d07bb79c3262b97c791a41092a75261353463` → `9e712afc6e64b9bc382365c4f11aca844d36446d`
  - LobbyDojoIsland `0ea8a0957841bcbd92def235726cc9a21be1231f` → `ce15db886d35089558e48da7fb5661365ba041f4`
  - TrapRaidersHUD `65737fe0dcb51c7bf04371738b23bec1bfec625f` → `3af56301667b783a23f9c641f9b6b6289df0f44f`

## 真正の遊べるLuau変更（文字の企画のみではない）
1. `LobbyDojoIsland.build`に赤青それぞれ7職（計14）3D展示台を組み込み。2/7色分け武器preview + 地面と本物のProximityPrompt、人物の動線から徒歩で到達するY=41/Z=400。サーバが明示した各チームの職を展示。7職の名前は戦士/魔法使い/暗殺者/トラッパー/建築士/魔獣使い/ゾンビ使い。
2. 赤青それぞれ1個ずつ**物理出撃ゲート**（Z=367）。近づきE/タッチで本人がREADY=true/false。従来の中央READY大型UIはStudioロビーで非表示。初回とRESULTS後のREADY=falseを維持し、強制出撃を禁止。
3. **Game元サーバ正本1本の関数を再利用**：既存`selectSevenJob`と`applyReady`にStudio物理Prompt権限経路を用意。入力は`ProximityPrompt.Triggered(player)`からのみ、team/ACTIVEでないphase/生存/実root位置距離12stud/lobby位置と実職の7件を照合する。RemoteEventやclient-provided seqを増やさず、Gameの重複職拒否、職装備、ACK、試合READYに接続。プレイヤーが近づけない/異なるTEAMの展示台は発火不可。既存Remoteのseq契約は変えない。
4. **HUD**のロビーに表示される旧職業選択大型パネル、出撃ボタン、チーム役割・モード選択・所有装備重ね表示、top/statusをStudio物理ロビー中だけ隠し、ACTIVEバトルHUDと非Studioの旧フォールバックを保全。大画面を導入する代替は作らない。

## QA & 修復継続
- **44/44** source inventory/XML再parse/親SHA pin/source byte exact/false Ready/Server authority/物理距離/Team/ZIP byte&CRC/2重実行拒否/書込み偽陽性拒否の静的テストPASS。
- **Native Luau / Rojo / Roblox Studio 1/2 client / Android / OWNER FUN = NOT_RUN**。前のゲーム見た目/操作の実機合格を静的成功で宣言しない。
- 保護: FB020風走り、FB021職武器/攻撃、FB022城門/屋内、FB023拾得8実spawn、Egg/Score/HP/Persist/唯一Remoteを保持。
- 次: まずStudio実機でロビー出現→職展示台取得→武器装備→READY→ソロAI開始→試合後自動READY falseを証明。既存作者 #297/#376、単一 auth B writer #220がsource-exactで正規RCに採用後、#470/#420 Android/FUN比較→OWNER再試遊。残P0魔獣AI/7職フル能力。

**状態** PRIVATE_REAL_SOURCE+STATIC_PASS、正式RC採用0・Studio=NOT_RUN・OWNER_ACCEPTED=0。公開binary/元ゲームソース全文を本repoへ無断pushせず、MAIN/merge/Roblox publish/課金なし。
