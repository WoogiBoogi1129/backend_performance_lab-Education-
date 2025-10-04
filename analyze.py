# analyze.py
import pandas as pd

# results.csv 컬럼: ts,mode,user,start,end,iter,elapsed_ms,note
df = pd.read_csv("results.csv", header=None,
                 names=["ts","mode","user","start","end","iter","elapsed_ms","note"])
df["elapsed_ms"] = df["elapsed_ms"].astype(float)

# note를 "C0_1k" 처럼 사용 → 조건/규모 분리
df[["cond","size"]] = df["note"].str.split("_", n=1, expand=True)

# initial/repeat 별 평균/표준편차/중앙값
summary = (df.groupby(["size","cond","mode"])
             .agg(avg_ms=("elapsed_ms","mean"),
                  std_ms=("elapsed_ms","std"),
                  median_ms=("elapsed_ms","median"),
                  n=("elapsed_ms","count"))
             .reset_index())

print(summary)

# Baseline(C0, initial 기준) 대비 개선율 계산(같은 size, 같은 mode 비교)
base = summary.query("cond=='C0'")[["size","mode","avg_ms"]].rename(columns={"avg_ms":"base_ms"})
merged = summary.merge(base, on=["size","mode"])
merged["improve_pct"] = (merged["base_ms"] - merged["avg_ms"]) / merged["base_ms"] * 100.0

# 보기 편하게 피벗
pivot = merged.pivot_table(index=["size","mode"], columns="cond", values=["avg_ms","improve_pct"])
print("\n=== Summary (vs C0) ===")
print(pivot.round(2))