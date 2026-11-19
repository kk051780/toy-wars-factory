# FB028｜建築士の実橋が自分の体で設置拒否される不具合を実修正

OWNER「つぎ」(2026-11-15) への実装優先P0スライス。前FB027のStudio実Placeを直接検査した。橋の配置前重なり検査 `workspace:GetPartBoundsInBox` が配置者自身の足・体にも命中し、ルート開始点からの橋設置を誤って拒否するバグがある。

**実修正:** 既存 `Game` の `fb027CreateBridge` 中にある重なり判定1箇所に「プレイヤー自身のCharacterから生成されたパーツは除外」を追加する。他人のHumanoidとの衝突拒否は維持する。橋の長さ27stud・材質・衝突・レール・28秒消滅・TEAM・卵と城からの距離規則は変更なし。元Gameの唯一Remote/得点/卵/HP/他7職能力は変更なし。

## 真正PRIVATE Studio PlaceとSourceLock
- 元FB027 Place 865446 B / SHA256 `5987a2e0d59ddc703975c10c3e017ed62faf25d9b0d62131da0430bb550aace6`
- **修復FB028 Place 865812 B / SHA256 `7981960d1f3027d7c411f7ce9de4e3e467011d59183d758cab77b2fa717d352d`**
- ユーザーに渡したPrivate `TRAP_RAIDERS_RC82_FB028_BRIDGE_REPAIR_PLAYTEST.zip`: 240103 B / SHA256 `f49e27f20aa53aabebf6f16a8f2f2cdee1453937b81e14bb64157819bd9364e4`
- 全82 LuaU Sourceを実Placeから抽出し、**Gameだけ1本変更・他81本完全一致**。Game元blob `a8f5acc19ce59991c42aec3a9e2e2da847cfe2d5`→新blob `a49992ce07392aef2a2e014ad8d5de5c6797177f`。
- 親SHA誤り拒否・出力上書き拒否・2回適用拒否・一意Remote/他81Source一致・7職/魔獣/拾得/ロビー/城・既存FB027蘇生/罠の保全・配置判定の自分/他人/NPCのモック、**33/33 SOURCE/論理チェック PASS**。
- 正式なNative Luauコンパイラはこの実行環境に存在せず、**Native Luau・Rojo・Roblox Studio 1/2client・Android/ART/FUNは未実施**。この33テストはエンジン挙動の保証ではない。

## 実コードの場所
- Public GitHubの **source-exact差分再現器**: `quality_repair/fb028_bridge_self_overlap_fix.py`。プレイ可能な非公開Place全体やGame原文は公開Repoに転載しない。USER配布のPrivate ZIP内には、この再現器、静的テスト、実Studio Placeが全て同梱。
- Draft PR #476はゲームのAUTH writerではない。既存城作者#366とGame作者#297がこの**小さな変更ハンクのみ**を最新版へ再baseし、認証済RC writer #220が最新同HEAD native/Rojo/SourceLock + 非force CASで正式RCへ統合する。

**状態** PRIVATE_REAL_SOURCE_FIX + STATIC_REGRESSION_PASS、OFFICIAL_RC_ADOPTED=0、STUDIO_NOT_RUN、OWNER_ACCEPTED=0。RED構文/SourceLock/単一権威/CASのみ停止。YELLOWは負債に記録し非公開RC開発を進める。ソース修正と公式採用の同一視禁止。
