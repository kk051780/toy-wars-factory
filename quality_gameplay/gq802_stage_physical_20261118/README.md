# GQ802 | #803 既存ランダム地形 manifest → Studio 6区画物理追加マップ

**FEATURE_ID:** GQ802_STAGE_PHYSICAL_ANNEX_V1 (new physical adapter only). **REUSE:** #803 source git blob `696d2312ef7408e26b03281caede7606472c155b`. **CLAIM:** #218 comment 6978019016. **RC writer:** #220 authenticated B writer only.

## 実装済みの範囲
- #803 の純Luau StageManifestPolicy を**変更せず**に使用。ServerScriptService 同一ディレクトリ内で一回だけ乱数生成し、`validate()` 通過時だけ物理化。
- Studio の既存 TEAM / BR `TacticalBattlefield` の東外側に6枚の衝突判定がある歩行可能な地形板を配置。3本の地上入口、南北の連結橋4本、幻想区画の接続橋1本、各地形板あたり3本の非接触オブジェクトで合計32 Parts。モバイル用上限48 Parts。
- 25プレハブ名の抽選結果を立体物の属性・区画識別に反映し、空・海・夢・時間・冥界・宇宙等の外観色を分ける。現時点で完成済み25種類のアートモデルではない。回復・アイテム・報酬は**配置しない**。
- 城・卵・ホストの原フィールドを動かさない。天候は将来の既存Realmに委譲するメタデータのみ。重力・時間・HP・キル・得点・Store・Teleport・新Remoteは操作しない。
- ユーザが指定するSeed/再抽選 API は作らず、ServerScript 一回の抽選のみ。
- 世界と一緒に scene が破棄される。追加3源だけを除外すれば OFF36 へ完全復帰できる。

## 重要な限界と受入
この adapter は **外側に追加した歩行可能な試作の地形**であり、元のゲームフィールドを6分割・置換する最終メインステージビルダーではない。城・卵・Swarm の経路探索とレベルマッチングは現在の権限を維持。Studio 2-client / Android 実動作・機種性能・FUN・アートは未検証。原作者の個別ACKは必要ないが、プライベート RC 同一SHA native/Rojo/Source/Class/OFF と既存 #220 認証 CAS は必須。正式RCの変更はこのPRで行わない。

## Native CI
1. #803 immutable StageManifestPolicy を固定 SHA からダウンロード・Git blob照合。180シード／6区画／地上3経路＋異常manifest・接続路を故意に壊したミュータントはRED。
2. 現正式RC Core36 の同一HEAD成功 Actions `44232589275` からRBXLXとSHA receiptを取得。**既存の36ソース/classを同一byteで再抽出**。
3. ON39に元作者1 ModuleScript＋物理計画1 ModuleScript＋Studio-only1 Scriptを選択。OFF36は元の36本を保持。Native 39/36 compile・Rojo source/class/rollback・場所の真のbyte/SHA receipt検収。
4. 新候補のみの成果物をアップロードし、正式RCのPlace/ZIP容量と混同しない。Bによる正式選択後のみ正式RCの進捗に含める。

**ROLLBACK** ON39からこの3 sourceを除外して既存Core36へ戻す。production publishとmain書込み禁止。
