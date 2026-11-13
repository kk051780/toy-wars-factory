# #288 H1 独立監査：精鋭の復活直後に攻撃予兆が残る問題

**2026-11-13 JST** · QA-only / 実Studio未検証 / 既存ソース変更なし

## 固定した証拠

- 対象は [#288 の固定実装](https://github.com/kk051780/toy-wars-factory/tree/55ad13b45907a5a3e9deae7196a7c202a0672c0c/handoffs/P0D-MUSOU-CHAOS-H1-20261113-01)（38 Luau、native/Rojo PASS は#288自身の報告）。
- ソースパス：`handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/MusouHorde.luau`。
- Git blob SHA-1 `c1ef565f4e8b11a6e8ff7eac5ed55c8f268a4553`。
- `Horde:hit` 約139–146行：精鋭のHPが0になると `m.deadUntil=now+8` にし、見た目を地中へ移すが、`m.tellUntil`／`m.target`／`m.attackAt` を無効化しない。
- `Horde:tick` 159–165行：8秒後にHP／位置とUIを復活させるが、古い`m.tellUntil`／`m.target` が残る。
- 同193行以降：`if m.elite and m.tellUntil>0 and now>=m.tellUntil` が旧攻撃を解決する。旧対象が攻撃範囲内なら新たな1.5秒予告なしに `damage=11` の候補が返る。

## 再現可能な**ソース条件**（実機の再現結果ではない）

1. t=100.0 精鋭が標的Aをロックし、`tellUntil=101.5,target=A`。
2. t=100.5 味方が精鋭を撃破。HP=0、`deadUntil=108.5` になるが予兆と対象参照を残す。
3. t=108.5 精鋭が復活（HP回復、UIのみ初期化）。旧`tellUntil=101.5` は残存。
4. 次のサーバーtickで `now >= tellUntil` が即成立。Aが付近にいれば、再度の1.5秒予兆を出す前に攻撃候補が発生する。

**判断：SOURCE-LEVEL FAIL / FAIRNESS RISK。実Studioの命中・実FPSはUNKNOWN。**

## 作者に依頼する最小修正（提案・原作者ファイルは直接編集しない）

```diff
--- a/inputs/MusouHorde.luau
+++ b/inputs/MusouHorde.luau
@@ after m.deadUntil=now+8 in Horde:hit
+                        m.tellUntil=0
+                        m.target=nil
+                        m.attackAt=now+2.5
@@ after m.hp=m.maxHp in Horde:tick respawn
+                m.tellUntil=0
+                m.target=nil
+                m.attackAt=now+2.5
+                m.flashUntil=0
```

復活後、精鋭の視覚予兆が出る場合は正規の新しい`tellUntil=now+1.5`だけで発火させる。古い攻撃対象・他ラウンドの標的は再利用しない。死亡直後にもターゲット／予兆解除を行うことで、デバッグ時の攻撃レシートの誤解を避ける。

## 独立検収

- [ ] GitHub固定38 Luauソース再取得＋manifest GitBlob/SHA一致
- [ ] ソースレベル：死亡直後・復活時の双方で`tellUntil=0,target=nil`、回帰Mutationを拒否
- [ ] 真のLuau原本をnativeコンパイル／Horde状態遷移QA（Lua VMテストが可能なら）
- [ ] Studio 2client：予兆→精鋭撃破→8秒後復活→Aが至近距離に居ても予告なしダメージ0
- [ ] 新規予兆1.5秒が再度見える／回避すると被弾0／ヒットすると既存権威が11ダメージを1回だけ適用
- [ ] 連続撃破・再戦・離脱・再入室・切断時にも古い標的を持ち越さない
- [ ] 既存 CLASSIC/SCORE_5、卵HP・得点・保存・XP・魔獣所有・拘束/脱出はH0と同一で二重イベントなし
- [ ] Android横画面の可視性／同条件H0/H1「理不尽なダメージ」感想確認

**最終的な扱い：** #288の原作者が自分の隔離ブランチで修正→独立QA→#250 PRODUCT_SELECT→#220唯一のRC統合者が選定・実機検収。現時点では全ゲームの正式RC・Studio・本番公開へは組み込まない。#285パワー/#287進化の追加と混同しない。

## テスト

```bash
node handoffs/P0D-INDEPENDENT-HORDE-RESPAWN-QA-20261113-01/tools/audit_horde_respawn.mjs handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/MusouHorde.luau expect-unsafe
node handoffs/P0D-INDEPENDENT-HORDE-RESPAWN-QA-20261113-01/tests/test_horde_respawn.mjs handoffs/P0D-MUSOU-CHAOS-H1-20261113-01/inputs/MusouHorde.luau
```

Expected current source: `requiresFix:true` and Node test 17/17 asserting **bug detection**. **A green QA detection test is NOT a fixed game**. After the author patches source, on its SHA use `expect-fixed`, update pinned blob and all source tests, and then run Studio2client QA.

No main/merge/Roblox publish/paid/spend/PC Codex/P0 ABC/CAS/five automations changed.
