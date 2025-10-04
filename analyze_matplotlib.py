# analyze_with_plots.py
# 사용법: python analyze_with_plots.py
# 결과물: /mnt/data/plots/ 폴더(요약 CSV + 차트 PNG)

import os
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

csv_path = Path("results.csv")
if csv_path.exists():
    df = pd.read_csv(csv_path, header=None,
                     names=["ts","mode","user","start","end","iter","elapsed_ms","note"])
    df["elapsed_ms"] = df["elapsed_ms"].astype(float)
    data_origin = "results.csv"
else:
    # (데모) 합성 데이터 생성 — 실제 파일 있으면 이 블록은 실행되지 않음
    import numpy as np
    np.random.seed(0)
    rows = []
    for size in ["1k","5k","10k"]:
        base = {"1k":120.0,"5k":300.0,"10k":600.0}[size]
        for cond in ["C0","C1","C2","C3"]:
            for mode in ["initial","repeat"]:
                if cond=="C0":
                    mean = base if mode=="initial" else base*0.98
                elif cond=="C1":
                    mean = base*0.35 if size!="10k" else base*0.28
                elif cond=="C2":
                    mean = base*0.15 if mode=="repeat" else base*0.7
                else:
                    mean = base*0.10 if mode=="repeat" else base*0.30
                for i in range(30):
                    val = max(np.random.normal(loc=mean, scale=max(mean*0.05,1.0)), 1.0)
                    rows.append([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                 mode, 100, "2025-09-01", "2025-09-30", i+1, val, f"{cond}_{size}"])
    df = pd.DataFrame(rows, columns=["ts","mode","user","start","end","iter","elapsed_ms","note"])
    data_origin = "synthetic demo (no results.csv found)"

# note → cond/size 분리
df[["cond","size"]] = df["note"].str.split("_", n=1, expand=True)

# 집계표
summary = (
    df.groupby(["size","cond","mode"])
      .agg(avg_ms=("elapsed_ms","mean"),
           std_ms=("elapsed_ms","std"),
           median_ms=("elapsed_ms","median"),
           n=("elapsed_ms","count"))
      .reset_index()
)

# C0 대비 개선율
base = summary.query("cond=='C0'")[["size","mode","avg_ms"]].rename(columns={"avg_ms":"base_ms"})
merged = summary.merge(base, on=["size","mode"])
merged["improve_pct"] = (merged["base_ms"] - merged["avg_ms"]) / merged["base_ms"] * 100.0

# 출력 경로
outdir = Path("plots")
outdir.mkdir(parents=True, exist_ok=True)

summary.to_csv(outdir / "summary_by_size_cond_mode.csv", index=False)
merged.to_csv(outdir / "summary_with_improvement.csv", index=False)

# 조건 정렬
order = ["C0","C1","C2","C3"]

# 차트: 각 (size, mode) 별로 2개(평균/개선율), 한 그림에 하나의 플롯만(지침 준수)
for size in sorted(summary["size"].unique()):
    for mode in sorted(summary["mode"].unique()):
        block = summary[(summary["size"]==size) & (summary["mode"]==mode)].set_index("cond")
        block = block.loc[[c for c in order if c in block.index]].reset_index()

        # 평균 응답시간 + 오차막대(std)
        plt.figure()
        plt.title(f"Avg Response Time by Condition — size={size}, mode={mode}")
        plt.bar(block["cond"], block["avg_ms"], yerr=block["std_ms"])
        plt.xlabel("Condition")
        plt.ylabel("Average Response Time (ms)")
        plt.tight_layout()
        plt.savefig(outdir / f"avg_{size}_{mode}.png", dpi=150)
        plt.close()

        # 개선율(%)
        blk2 = merged[(merged["size"]==size) & (merged["mode"]==mode)].set_index("cond")
        blk2 = blk2.loc[[c for c in order if c in blk2.index]].reset_index()

        plt.figure()
        plt.title(f"Improvement vs C0 (%) — size={size}, mode={mode}")
        plt.bar(blk2["cond"], blk2["improve_pct"])
        plt.xlabel("Condition")
        plt.ylabel("Improvement (%)")
        plt.tight_layout()
        plt.savefig(outdir / f"improve_{size}_{mode}.png", dpi=150)
        plt.close()

print("Done. Data source:", data_origin)
print("Saved tables & charts under:", outdir.resolve())