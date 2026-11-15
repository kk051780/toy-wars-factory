# P0D-031 / FB: 拾って使える「飛行羽」— Private gameplay source

## Playable behavior (implemented, not just design)

- World `TRAP_RAIDERS_S1` の実 `GrassArena` に4つの光る飛行羽を配置。近づいて `拾う`（PCキー/モバイルProximityPrompt）。
- 装備欄に「飛行羽｜8秒飛行」が入り、PCクリック／スマホの標準Toolボタンで実際に上昇・移動・滑空。翼の軌跡VFX、8秒で消滅。
- 14秒後に元の場所に再出現。重複所持禁止。死亡・退室・アリーナ外・高高度では終了。
- 7職・Game/HUD・卵・戦績・HP・Store・元Remoteに干渉しない。画面常駐案内は増やさない。
- **Studioでのみ自動有効**。非Studioでの利用は非公開プライベートサーバーかつScript Attribute `EnablePrivatePreview=true` が必要。公開サーバーでは無効。

## Integration

作業用に複製した、既存 `default.project.json` / `SOURCE_LOCK.json` / `src/server/Game.server.luau` を持つRojo `dist` にのみ:

```bash
python3 apply_private_stage.py --dist PATH_TO_PRIVATE_COPIED_DIST
python3 -m unittest discover -s . -p 'test_flight_item.py' -v
```

既存全Luauのロック完全一致を最初に検証し、元ゲームの全Script bytesを保持して1本追加。未知のRC源/失敗したロックなら書込み前に中断。Source LockとRojo treeに候補を追加した後は**真正RC #220 のwriterが既存Native Luau/Rojo/同HEAD CIを実行し最終採用**。RC本線・mainへ勝手に書き込まない。

## Known gate

- Python regression / static source only。Roblox native Luau parse、Rojo build、Studio/Android操作、実際の飛行の操作感・衝突・FPSは **NOT_TESTED**。静的PASSをエンジン合格と混同しない。
- `P0D-031` カタログ旧Release `S2+` はOWNER最新の「空を飛べない」実機FB対応の優先候補。勝手に企画台帳を改竄せず、#219/#470 で対応。
- **Disable/rollback:** stage前のdistに戻す、または対象 Script を除去しSOURCE_LOCK/Project mappingを戻す。非Studioはprivate flag OFF。
