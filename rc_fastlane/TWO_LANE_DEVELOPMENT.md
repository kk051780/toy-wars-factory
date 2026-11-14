# P0D 2部隊並列開発・最新版受入契約 V1（2026-11-14）

OWNER指示: 「RC統合と統合前までの状態を作る2部隊制にする。並列作業。RC統合役は最新版を取り込む仕組みにして」

## 役割

| 部隊 | 作業すること | 編集範囲 | 完了条件 |
| --- | --- | --- | --- |
| A 準備班 PREP（#219/#250、WORKER、機能作者） | キャラ、フィールド、戦闘、仕掛け、収集、UXの実Luau/3D、固定SHA、独立QA、OFF切戻しを並列で完成 | 各自の feature/p0d-prep-*-* ブランチのみ | 最新RCを基準にした非draft PR＋同HEAD成功CI＋明示READY契約 |
| B 正式RC統合班（#220唯一の認証済みwriter、METAは最新候補監視支援） | PREPの最新版を検出・査読し、既存RCに最小差分で積み上げる | Bの本人認証とリースがある場合に限り rc/p0d-s1-kids-rc01 をCASで更新 | 新公式HEADのLuau/Rojo/独立QA成功、実Place/ZIP容量、台帳、ACK |

AはBの統合中も別機能を作り続ける。BはAの機能を作り直さず、原作者のソースを固定SHAで採用する。各チャットの独立試作・Stage・PRが増えても正式RCに未採用ならRC進捗は増やさない。

## A → B の機械可読な受渡し

1. 最新の正式RC HEADからPREP専用feature branchを分岐し、実ゲームの最小差分を作る。仮のPlaceだけ・仕様だけではREADYにしない。
2. 既存Game/Remote/Store/score/HP/XP/save/eggの権威は単一とし、編集が必要なら既存スクリプトの差分へ限定。ソースlockと機能ごとのOFF切戻しを準備。
3. RC宛てPRを非draftで作成。実HEADの本当のActions「P0D canonical RC fast-lane Studio build」がsuccessになった後、PR本文に次の単一契約を記載する（最新のコミットをpushしたらPINNED_HEADを更新して再CI）。

P0D_PREP_READY_V1

PINNED_HEAD: <PR最新40桁SHA>

BASE_RC: <基準の正式RC40桁SHA>

FEATURE_IDS: NEW_FEATURE_ID

SOURCE_LOCK: rc_fastlane/SOURCE_LOCK.json

ROLLBACK: Turn the feature flag OFF and rebuild exact previous source

FEATURE_IDSは今回**新しく受け入れる**機能IDだけ。既存のゲーム全機能を改めて列挙しない。SOURCE_LOCKは実ファイル/生成器が指すJSONと一致すること。Sourceryの重大P0/P1未解決はREADY扱い禁止。

## Bが「最新版」を受け取る手順

- tools/p0d_two_lane_queue.py は最新公式HEADを読み、現在の未完PRを取得し、READY契約・非draft・同一base SHA・同一head SHA・git compareがbehind0のfast-forward・最新の同HEAD Actions successを確認する。
- 一つのFEATURE_IDに複数の候補があれば、**適格かつ実ソースHEADのコミット日時が新しい**1件を採用候補にする。PR本文の編集日時だけで新作扱いしない。別機能IDの適格候補はPREP内で並行維持する。CI失敗・旧RCベース・旧SHAや重複候補は除外する。**採用候補は承認済みではない**。
- .github/workflows/p0d-two-lane-intake.yml は正式RC更新・RC宛PRの変更で読取専用スキャン＋テストを自動実行し、P0D_PREP_INBOX.jsonを7日保存。GitHub ActionsにはRC/main書込権限を与えない。
- Bは候補を選び直す直前に公式HEADとwriter認証/リース/Sourcery実害・sourceの固定blobと依存を再GET。既存のGame/Remote/Storeを二重生成せず必要な差分だけ統合し、force=false＋expected SHAのCAS更新を実行。
- **公式RCのHEADが一度でも変わったら**、他候補は新公式RCへの追従と新HEAD CIが必要。旧候補の成功CIを流用しない。新公式HEADのLuau、Rojo、保存・権威、negative、rollbackが成功した時だけ#220でINTEGRATOR_ACK/RC採用とする。
- 旧ネストPRの全マージ、Aによる正式RC書込み、Actionsの自動merge、main変更、Roblox公開、有料設定や課金、無断PC/Codex操作は禁止。

## 並列進捗と容量の毎回報告

- A: FEATURE_ID、準備完了数/対象数、実source HEAD、独立テスト/CI、OFF rollback、PREP_READY件数、B待ち件数。
- B: 正式RC40桁HEAD、source本数、企画RC採用の分子/分母/%、工程加重率、同一HEAD Actions ID/結論、実物Place (.rbxlx) と成果物 ZIP **別々のbyte**、前回差分、Studio2client/Android/FUN、S1旧75/100の検証状態。
- 企画のIDEA/SOURCE/RC/STUDIO/FUNは証拠別。PREPが完成しても正式RCの採用率を水増ししない。初回公開前にはOWNER本人のStudio2client/Android/再ログイン/面白さ評価が別途必要。
