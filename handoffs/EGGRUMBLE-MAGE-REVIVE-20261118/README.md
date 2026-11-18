# BATTLE-765｜魔法使いの蘇生（TEAM戦・実ソース候補）

## 今回の一次実装
既存7職/城/卵/中立/戦闘の権限を取り上げず、既存V3 Hostに2箇所の装備後hookだけ追加。新しい ModuleScript `EGGRUMBLE_MageRevive` を1本増やす真正31→32構成。元30ゲームソースbyte同一・既存Hostに小さなrequire/hookのみ。正式元31へ完全復元できる。

- チーム戦で生存中の本人が実ダメージを受け、HPが最大の20%以下になり、**同じTEAM・同じ試合に生存魔法使いがいる場合のみ**「ダウン状態」に移行。HP0の瞬間撃破は元の死亡とし、後からDiedしたアバターを無理に起こさない。
- ダウンした味方は60秒行動不能。既存の `Humanoid:TakeDamage` に対する限定ForceField保護を使い、倒れた味方が攻撃連打で即消滅しないようにする。スキルToolは一時利用不可、通常装備と移動は蘇生で復旧。
- 味方魔法使いが12stud以内のPromptを3秒押し続けると、サーバーが同チーム・生存・現在試合・実距離14stud・遮蔽物LOS・被蘇生者60秒内・40秒CDを**再検査**。成功すれば最大HP35%以上へ回復し、再び行動可能。
- 魔法使いがいないソロ/BRには理不尽なダウン待ちを入れず通常の元ゲーム死亡処理のみ。ダウン後60秒経過すると元ゲームの死亡へ戻す。城陥落、別アバター、試合終了、死亡、退室で専用状態と監視を解除。
- 既存魔法使いの回復魔法(+25HP・AI等の原作者#510修正)は一切変更しない。「戦闘中の治癒」は即時HP補給、「蘇生」は実際の救助Prompt・40秒CDと役割が異なる。無課金・無料Lv1からTEAMで利用可能。

## 限界と必要な実機ゲート
**一次スライスとしてのダウン判定は生存のままHP20%以下になった時点**。一撃で0になったキャラクターや他の所有者が直接Health=0にする経路では通常死亡し、蘇生可能ダウンに変換しない。これは二重死亡/既存Host respawn破壊を避ける安全側仕様。全攻撃の「HP0直前ダウン」を実現するには元Combat/Host単一のダメージ受理APIに統合する必要があるため、#220/正式Combat担当が別途対応。これを完全な蘇生完成と誤報しない。
ForceFieldは `Humanoid:TakeDamage` に有効だが、直接HP代入や独自HPアダプターには効かない。既存の装備ツール有効/無効や他担当の自然回復 #775 との同時実行は、正式Hostへ一本化した後のStudio2client/Androidで再検証が必要。
ユーザーの最重要指令「通常攻撃ではすぐ死なない」「魔法使いは蘇生できる」は将来の元Combat単一入口への接続を条件に、完全受入とする。

## QA・統合
- `compose_mage32.py` は正式31本の真正抽出ルートだけを入力し、Host `SevenRoleCombat.equip` 直後にこのModule `attach` を2回付ける。元Combat・HP/スコア・Store不変更。他30 byte exact。
- `--off` は元31を完全復元。
- `make_mage_vm.py` は本物のLuauからNative VM harnessを作り、TEAM/敵側/自己蘇生不可・LOS・40秒CD・60秒強制元死亡・3秒Prompt設定と変異REDを検証。
- 固定Luau Native32/31、Rojo32/31 Source/Class、同HEAD元正式31参照、OFF31をCIで検証。
- #220 sole authenticated writer が #775のHost回復hookとこちらの蘇生hookを**重複のない一つのHost**へ合成し、真正同HEAD/非force expected-SHA CASで正式RCへ採用。前原作者の個別承認は不要。main/Publish/課金不可。
- Roblox Studio 2client・低性能Android15分・本人FUN/ARTは未検証であり、ソース成功だけで完了とはしない。
