# GQ8 石巨人の真正HP可視化｜既存31ソース／近距離だけ

**FB-002/003/008/015、#470、#420**。現在の実サーバ石巨人は900HPを管理し、コアが青/赤へ変わるが戦闘中に残量が読めない。遠距離の大型HUD追加は禁止。そこで**既存** `EGGRUMBLE_NeutralStoneGiant` ModuleScriptにだけ、目線55stud以内、`AlwaysOnTop=false`、174×32pxの3D Billboardを1枚追加し、サーバ確定ヒット時の900→残り値だけ表示する。

- 毎試合・各モードの既存ボスにのみ表示、手動ヒットの判定・スキル・石巨人衝撃波壁遮蔽（GQ518）・HP/死亡/討伐回数・城/卵/アイテム/中立兵/ロビー・全スコアは一切変更しない。
- オリジナル `GQ518` 既存StoneGiantを1箇所選択しなおし、他30ソースはbyte-exact、OFFで57-flag現RCに完全戻し。モデル属性 `EGGRUMBLE_BossHealth` をスポーン直後から900で初期化（以前は初回ヒットまで未設定）し、ダメージ成功後にラベルのみ更新。ボス消滅時に眼球親へ連結したGuiも同時削除。
- Unityなど外部素材／新Game／新Remote／DataStore／課金／main／公開なし。実Studio GUIの見え方・重なり・Android FPSは未検証のためART/FUN/MOBILE/OWNER NO_GO。
- 合格条件：現在の31ソース全Luau Native compile、元の波動遮蔽保持、8つの真正Luauモック実行ケース＋破損変異RED、Rojo7.7.1 の31 Class/Source全一致、単一Source差分、OFF可逆、同一候補SHAのGitHub Actions成功。
- 統合：#220 sole writerが最新RC HEADとPR競合を再照合し、58フラグ登録・正規Placeを新最終Stageへ向け、nonforce expected-SHA CAS。main・Publish・実機受入は別ゲート。原作者ACKは不要。
- 引継ぎ：毎回正式HEAD・PR・CIとSource SHA・rollbackを再確認し、失敗した時は該当候補を修復してから進める。単なるCI greenをStudio/FUN合格にしない。
