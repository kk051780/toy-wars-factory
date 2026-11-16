# EGGRUMBLE — 7職×3技の武器動作・神憑き6秒の実装／受入ゲート

Date: 2026-11-16. SOURCE-only Draft PR #482; main/正式RC/Roblox Publishは変更しない。

## なぜこの実装を優先したか

武器を持っていても振らなければ「どの職業も攻撃が同じ」という品質欠陥が残る。今回の実コードは既存「7職21技同一試合」のサーバ権威・命中判定を使い、**発動確定時のモーションを全21技に区別**する。攻撃が空振りでも腕の攻撃モーションは出る一方、命中フラッシュ/KOと局所カメラ揺れは真のHP変化時だけとする。

## 実コード差分

1. `EGGRUMBLE_SevenRoleCombat.luau`
   - 生存・職業・所有城・試合ACTIVE・スキルの各別CDを通過した後、サーバが一つの文字列属性 `EGGRUMBLE_SkillCastSignature` に `ROLE:A|B|C:monotonic-sequence` を書く。クライアントに攻撃権限なし。21技は既存の威力・範囲・追加効果を維持。
   - 武神の神憑き・魔獣使いの巨大餌の強化残時間を **Player属性から現在のCharacter属性へ移動**。死亡後の別キャラに強化を継承させない。
   - 武神C発動時は `DivineMantle.activate(p,6)` を呼び、6秒間の神威変身を付与。武器は従来の `WeaponSilhouettes` を利用し、魔獣・呪術召喚が独立AIではない制約は変わらない。
2. `EGGRUMBLE_ProceduralSkills.client.luau`（StarterPlayerScripts）
   - サーバー確認済みの発動属性だけを読むLocalScript。R6/R15旧Jointの `Motor6D` と最新の `AnimationConstraint` を両方検索し、`RunService.PreSimulation` でAnimator姿勢に控えめな腕・胴の動きを加算。C0/C1/Attachmentを直接書き換えない。
   - 7職のA/B/Cで動作が区別される。**武神:抜刀横斬り／突撃／両腕を上げる神憑き**、**魔法:杖を掲げ両手に魔力**、**暗殺者:双刃を交差**、**超能力者:両腕で念動操作**、**科学者:電磁銃を狙う**、**魔獣使い:爪を振り下ろす**、**呪術師:杖で呪印を描く**。A約0.26秒/B約0.48秒/C約0.82秒の姿勢アニメーション。
   - 16人まで、カメラから130stud以下だけを描画、死亡・退室・連打時には前の変位を解除。古いフレームを引きずって腕がねじれないよう直前適用変位を差し引く。
3. `EGGRUMBLE_DivineMantle.luau`（ServerScriptService ModuleScript）
   - 神憑きを発動した**本人のAvatarに付く**金色の神輪・左右炎・3つの神印・Highlight。最大6形状/人、サーバ同時8変身まで。着色Partは無当たり/無質量/非固定、`WeldConstraint`で主人公に追随する。
   - 6秒タイムアウト、`Humanoid.Died`、城陥落、職業再装備時には変身モデル・接続を解除し、神憑きの期限を0に戻す。見た目の同時数が上限に達しても、サーバ側の正当な6秒強化が無効にならない。
4. `EGGRUMBLE_V3_STUDIO.project.json` と `tests/test_v3_studio_project_wiring.py`：本モジュールとローカルスクリプトをStudioの正しい層に接続。別の新しいGame/HD/Remote/Storeは作らない。
5. `tests/test_procedural_skill_divine_gate.py`：実発動の正当性、R6/R15/AJU両対応、7職違い、強化の死亡安全性、Rojoレイヤーを検査。

## QAゲート/未達

- SOURCE静的テストと公式open-source Luau CLIによるネイティブ構文解析・ルール57件・21技バランスを同HEADで確認し、失敗したら作者の隔離SOURCEを修正する。
- 実際のStudioで R6/R15/Avatar Joint Upgrade をそれぞれ試遊し、通常の走り・泳ぎ・しゃがみアニメと重ねても腕が埋まらない、モーションが欠落しない、物理挙動や連打が破綻しないかを必ず確認。**本チャットではStudioエンジンの実行証拠なし**。
- 低端末Androidで戦闘中15分中央値>=30fps・p10>=25fpsを実測。目視「派手そう」ではなく、実際の子どもの爽快感、命中・手応え・音・敵撃破を先行ヒット作品と比較。Roblox audioの権利許諾済み素材が未指定なので**新しい音アセットは架空IDで実装しない**。
- 7職のアニメーションは原案ベースの**手続きポーズ試作**であり、独自手付けAnimationClipや神将・武将の豪華衣装、八岐大蛇の神獣や独立魔獣AI、完全新規3D Meshは未完成。完成の判断は#420アート品質と#470実装品質ゲート及びOWNER実機受入。
- #218共有台帳、#219企画室、#470品質修復、#420アート＋Android、#220認証RC統合担当へ、同じPR/HEADを周知し、元7職作者との二重開発は禁止。main/merge/Publish/課金は不許可。

