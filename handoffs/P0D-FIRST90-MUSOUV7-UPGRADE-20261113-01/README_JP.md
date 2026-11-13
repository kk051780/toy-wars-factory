# P0D B42 + Musou V7：実ダメージ表示・撃破演出まで一体型ゲームへ統合した非公開候補

2026-11-13 JST。前回のB42+V6成功版（commit \`63442fb415d361855d72f5a15171f7cdd4a2486f\`）を**不変の比較基準**として保存し、差分をこの隔離パックに追加した。

## 実装された変化
- 元ゲーム B42 の卵奪取（1卵・5卵）、初回90秒サーバー認証ガイド/卵Waypoint、無料孵化/装備・XP/Power/魔獣進化と同一の\`Game.server.luau\`と\`HUD.client.luau\`を保持。
- 先行V6の9体（8兵＋精鋭）可動3Dモデルと赤い攻撃予兆を維持し、元作者 #288 のV7 **実HP減少量の頭上ポップアップ／KOの0.72秒表示**を\`MusouHorde.luau\`1本差し替えで反映。
- 追加されたのは既存9体それぞれに固定の再利用式BillboardGui。HP=0になった時点で二重撃破・二重XPは禁止、8秒の復活時に古い表示を消す（元作者の実装）。
- B42のうち41/42 Luauは**完全バイト同一**。Game/Remote/score/HP/XP/Store/メイン世界・HUDは増やさず、危険な別ゲーム全置換はしない。

## 受入方法
\`python3 -B handoffs/P0D-FIRST90-MUSOUV7-UPGRADE-20261113-01/tools/assemble.py --assemble\`で B42元作者 → V6前作 → V7 の各固定ソースを再現し、独立distの42本にsource-lockを作る。隔離Actionsは全42本をLuau compile、V7の真正79 nativeモック、First90 48/Waypoint39の純ルール、Rojo 42本XML内容一致まで実行。非公開.rbx​lx はStudio用であり本番公開や公式RC更新は絶対に行わない。

**重要：** #250の正式PRODUCT_SELECTや#220の公式RC書込みは未実施。H1の人間Studio2client/Android、初回90秒、実FPS・描画負荷、客観的な面白さは未検証で、最後の公式S1 75/100、FUN_NO_GOは変えない。#248世界の未承認ルート等は今回追加しない。

NEXT_OWNER：#219企画責任者・#250製品判断・#220唯一RC担当。試遊時には初めての卵ルート理解、斬った相手の実HP減少表示、精鋭赤ゾーン、撃破後の消滅、スマホ可読性、勝敗・再戦意思を観察する。
