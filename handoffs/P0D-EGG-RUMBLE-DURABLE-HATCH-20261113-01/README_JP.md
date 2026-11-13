# EGG RAID RUMBLE｜無料孵化の永続保存：2モード共通 DEV DataStore 試遊候補

**2026-11-13 JST／Issue #282／内部ID TRAP_RAIDERS、公開名 EGG RAID RUMBLE**

## 何をつなげたか
元の#280完全H1ゲーム（卵1個奪取戦／卵5個4分得点戦／レア無料孵化／魔獣所有・装備／次試合に実3D偵察魔獣を呼ぶ）33本のソースから、既存のGame.serverとHUD.clientの2本だけ変更し、サーバー用の純粋なPersistentHatchStoreを1本追加。計34本。**ほかの既存31本はバイト単位で不変**、唯一のGameとS1Remoteも不変。#275の純Luau報酬ルール・#272の得点ルール・#279のモード投票ルールは再実装せず原本を利用。

## 保存方式
- Roblox公式 DataStoreService の `GetAsync` と **`UpdateAsync` のみ**。`SetAsync` による上書きで他サーバーの所持品を消さない。
- アカウントごと `U_<UserId>` の保存先。サーバーが `HttpService:GenerateGUID(false)`＋その試合番号で不変の `S<serverGUID>:<matchSerial>` 報酬記録を生成。同一番号の再試行は既取得として処理し二重増加させない。
- 無料孵化の抽選値は元Gameのサーバーだけが作る。クライアントにアイテム名・レア度・報酬番号・所持数を指定させない。
- UpdateAsyncコールバックは純粋な変換のみ（yield・Remote・乱数・外部呼び出し無し）。Roblox側の競合再実行や通信失敗後の再送でも同じ結果へ収束することを模擬検査する。
- 保存応答を確認した場合のみ画面で `✅ 保存サーバー応答あり`。読み込み中、Studio API禁止、一時保存、保存エラーは区別して表示。**保存応答ありは実機再ログイン検証完了の意味ではない。**
- 所持品 `starter_scout / forest_scout / star_scout` と現在装備を保存。元の図鑑 `discovered` は所有アイテムから復元する。既存原本の numeric epoch レシートは一時セッションのみ、永続レシートはこの保存モジュールが管理する。
- セッション中のDataStore障害では前のStudioのみの遊びを妨げないため一時所持を続ける。ただし『再ログインで失う可能性』を表示し、絶対に永続成功と称さない。
- 壊れた保存データ、未知のアイテム、未所有装備は**失敗として拒否**。2048個/ユーザーのレシート上限で静かに古いレシートを捨てず、移行が必要なことを明示。
- `BindToClose` に最大23秒の保全待機を入れるが、停止・ネットワーク障害下での100%保証はしない。

## OWNERのStudio検証手順（本チャットのChatはOWNER PC操作していない）
1. GitHub Actionsでテスト合格した私用 `.rbxlx` を、**実ゲームの公開Placeを上書きせず、別のテスト用Experience** として読み込む。公開・課金・mainマージをしない。
2. まず Studio APIアクセスOFFで起動し、従来戦と5卵戦、無償孵化→装備→実3Dスカウトが前のStudio一時モードとして引き続き使え、画面に**未保存**と明示されることを確認。
3. 後にOWNER承認の専用テスト用Experienceを別に準備できる場合のみ、Game Settings → Security → Enable Studio Access to API Services を有効化して検査。**Studio経由のDataStoreはそのExperience実データへの書き込み**。本実装は `EGG_RUMBLE_PRIVATE_STUDIO_HATCH_DEV_V1` と完全独立した専用テスト用データストア名を使用するが、Studio API設定自体は慎重に扱う。
4. UserIdが正の本物のテストアカウントと有効なAPIアクセスで、試合後に `✅ 保存サーバー応答あり` が表示されること、再入室時に OWNED/装備が戻ること、同一試合の報酬が二重付与されないことを実際に検証する。Studioの `Server & Clients` のダミーUserIdは負になる場合があり、今回の安全設定では**負のIDをDataStoreへ書かず一時セッション扱い**なので、ダミー2clientだけでは永続保存の本当の証拠にならない。
5. 2人対戦の個別クライアント確認、Androidタップ/負荷/ロビーUI、海空の卵運搬、再戦とFUN_GATE first90を別途検証。初回はあくまでオフライン/非公開試遊候補。

## まだ未完成・絶対に混同しない点
- Chat/CIでは **本物のRoblox DataStore API呼出し・Studio 2client対戦・実機再ログインを実行できていない**。今回の `UpdateAsync` は実コードを含むが実サービスの永続成功を認証していない。CIのモック保存は模擬の競合/障害ケースのみ。
- 永続保存は魔獣3種類（実際の能力は1種＋外観差）のみ。魔法、乗り物、武器・道具、ゾンビ、罠の**実戦使用・所有永続化は未実装**。
- 本スキーマのレシート上限2048と複数サーバーから同アカウントに同時書込みする場合の表示の一時的な古さ、API予算・停止等は将来本番の実負荷評価が必要。静かなデータロス/誤保存は絶対避ける。
- リリース専用 #220 の承認と、将来の安全な実ゲームID/PSEではなくRoblox Place/UniverseのRelease Gate設計が必要。**このソースのStudio限定コードを公開ゲームに適用しない。**

公式仕様参照： https://create.roblox.com/docs/cloud-services/data-stores と https://create.roblox.com/docs/cloud-services/data-stores/best-practices / https://create.roblox.com/docs/cloud-services/data-stores/error-codes-and-limits 。

進捗：本件はソース→ネイティブ/模擬DB検査→実機検証のうち**実機データ保存・スマホは未検証**。#220公式ゲーム75%、#222フィールド50%、公開FUN_GATE NO_GOから変化なし。main/RC/P0ABC/CAS/課金/公開/OWNER PC/Codex/5自動化の変更なし。
