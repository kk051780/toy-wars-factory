# P0D S1 — 同一試合内の古いSNAPSHOTによる初回ガイド巻き戻り防止

work_id: p0d-siege-v19 · game_id: TRAP_RAIDERS · release_id: P0D-S1-KIDS-RC01
Issue: https://github.com/kk051780/toy-wars-factory/issues/237

**用途：オプションの独立した2ファイル候補と原ソースでの結合QA。公式RCを書き換えない。**

現状の初回ガイド `FirstMinuteModel.consume` は、古い試合番号（serial）を拒否するが、**同じ試合番号の古いスナップショット**には順序判定がない。通信が逆順で届くと、子どもがすでに卵を持っている／得点したのに古い説明へ戻る可能性がある。これは実機で確認された不具合ではなく、**元ソースで確認された状態遷移の弱点**である。

## 2箇所に限る互換型プロトコル補強

1. `candidate/src/server/Game.server.luau`：既存の `snapshotFor` でサーバー専用の整数 `snapshotUpdateId` を都度1増やし、従来の`SNAPSHOT`に`updateId`を追加。試合終了・再戦・役職変更時も初期化しない。別Remoteや権限の移譲はしない。
2. `candidate/src/shared/FirstMinuteModel.luau`：クライアントのCoach状態に `lastUpdateId` を保持。古い番号・同一番号・負数・小数・文字列・NaNを拒否する。未採番の旧SNAPSHOTは、新規Coachが最初の採番パケットを受け取るまで従来通り受け付ける。採番後の未採番到着は拒否。該当した不正データでは表示状態を一切更新しない。

**変更しないもの：** 卵、攻撃、役職、城、罠サーバー判定、D07/D08ボスOFF、チーム判定、RemoteEventの本数、データ保存、ゲーム内課金、HUDのボタン配置。

## 実際に行うQA

- 正規RC Game/MapBuilder/Rules/Lobby/Config/GuardianTrapの6本と既存に採用候補のGuardian Coachを、元の`#235`ネイティブLuauテストに乗せ同じVMで結合する
- 公式元ソースGame Git blob `7c5229f600f17537bc1bbbb0b96b6a2435875374` とCoach Git blob `967ea52df79884e6c73e3e0952d5a97de0d1796e` を固定取得し、候補ファイルがそれぞれ**厳密な2箇所／4箇所の文字列置換**のみと一致するか判定
- REAL Gameから送られる初回LOBBY→役職変更後の古いLOBBY、卵を持つ→得点後の古い携帯中状態を逆順投入して拒否を確認
- 再戦跨ぎのupdateId単調増加と、後から届く未採番・不正ID拒否、旧プロトコルからのアップグレード互換
- 不正なGame/Coachソース6種類の意図的変更を元ソースの一時テスト版で検知。Python単体・SHA256固定・実native Luau CIを要求

採用判断は唯一の #220 統合担当。GitHub ActionsのPASSはRoblox Studio実機・スマホ2台・ネットワークの自然遅延・画面の視認性・OWNERの公開承認の代わりではない。通信順序の保障はCoachの画面案内についてであり、**HUD全体への共通対策を意味しない**。候補未採用なら公式RCは従来通り。

main / 公式RCの直接変更、merge、Roblox公開、課金・支出、OWNER Codexの直接起動、P0ABC/CAS/5自動化の変更は禁止。
