#!/usr/bin/env python3
"""User-requested P0D concept matrix, not an official release completion score."""
import argparse
import collections
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WEIGHTS = {"IDEA": 20, "SOURCE": 40, "RC": 70, "STUDIO": 90, "FUN": 100}
LABELS = {"IDEA": "企画", "SOURCE": "独立ソース", "RC": "RCビルド", "STUDIO": "実機済", "FUN": "面白さ合格"}

def summarize(data):
    assert data["schema"] == "P0D_OWNER_PORTFOLIO_V1"
    assert data["progress_scoring"] == WEIGHTS
    rows = data["rows"]
    assert len(rows) >= 40
    assert len({r["id"] for r in rows}) == len(rows)
    for row in rows:
        assert row["stage"] in WEIGHTS, row["id"]
        assert row["release"] in ("S1", "S2+")
        assert row["name"] and row["group"] and row["note"]
        if row["stage"] in ("RC", "STUDIO", "FUN"):
            assert (row.get("rc_evidence") or "").startswith("https://github.com/"), row["id"]
        if row["stage"] in ("STUDIO", "FUN"):
            assert (row.get("studio_evidence") or "").startswith("https://"), row["id"]
        if row["stage"] == "FUN":
            assert row.get("fun_evidence"), row["id"]
    stages = collections.Counter(r["stage"] for r in rows)
    totals = {}
    for target in ("S1", "S2+"):
        group = [r for r in rows if r["release"] == target]
        reached = sum(WEIGHTS[r["stage"]] >= 70 for r in group)
        totals[target] = {"all": len(group), "rc": reached,
                          "rc_pct": round(100 * reached / len(group), 1),
                          "phase_pct": round(sum(WEIGHTS[r["stage"]] for r in group) / len(group), 1)}
    n = len(rows)
    rc = sum(WEIGHTS[r["stage"]] >= 70 for r in rows)
    return {
        "total": n, "rc": rc, "rc_pct": round(100 * rc / n, 1),
        "phase_pct": round(sum(WEIGHTS[r["stage"]] for r in rows) / n, 1),
        "stage_counts": {k: stages[k] for k in WEIGHTS},
        "targets": totals, "official_s1_last_reported": data["official_s1_previous_score"],
        "studio_rich51": "NOT_TESTED", "owner_fun": "NOT_TESTED"
    }

def report(data, summary):
    out = [
        "# P0D｜企画案と実装進捗の一覧",
        "",
        "企画の工程到達率と公式ゲーム完成率は別です。RCはGitHubでStudio用ファイルを生成した状態で、実機動作の確認ではありません。",
        "",
        f"**企画 {summary['total']} 件 / 現RC搭載 {summary['rc']} 件 / RC搭載率 {summary['rc_pct']}% / 工程平均 {summary['phase_pct']}%**",
        f"公式S1の前回監査 {summary['official_s1_last_reported']} / 100（この表では更新しない）。Studio2client・Android・人間FUNは現RCで未検証。",
        "",
        "工程%は企画20、独立ソース40、RCビルド70、実機試験90、面白さ評価合格100という便宜的指標で、工数見積ではありません。",
        "",
        "|分類|企画案|状態|工程%|現状|",
        "|---|---|---|---:|---|",
    ]
    for row in data["rows"]:
        source = (" [根拠](" + row["evidence"] + ")") if row.get("evidence") else ""
        note = row["note"].replace("|", "／")
        out.append("|" + "|".join([row["group"], row["name"], LABELS[row["stage"]],
                                  str(WEIGHTS[row["stage"]]), note + source]) + "|")
    out += ["", "## 対象別RC搭載率", "|区分|企画件数|RC搭載|RC搭載率|工程平均|",
            "|---|---:|---:|---:|---:|"]
    for target, v in summary["targets"].items():
        out.append(f"|{target}|{v['all']}|{v['rc']}|{v['rc_pct']}%|{v['phase_pct']}%|")
    out += ["", "各チャットの単独ソース納品をRC完成と数えず、新機能のRC採用でのみRC搭載数を増やします。",
            "新しいRC HEADのビルドが未PASSなら前回のCIを流用して新機能を達成扱いにしません。"]
    return "\n".join(out) + "\n"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    data = json.loads((HERE / "FEATURE_CATALOG.json").read_text(encoding="utf-8"))
    stats = summarize(data)
    md = report(data, stats)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(md, encoding="utf-8")
    else:
        print(md)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("P0D_FEATURE_CATALOG_PASS", stats["total"], stats["rc"], stats["rc_pct"])

if __name__ == "__main__":
    main()
