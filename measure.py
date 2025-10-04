# measure.py
import argparse, csv, statistics, time, requests
from datetime import date, timedelta

def ms():
  return time.perf_counter()*1000.0

def run(url, user, start, end, n, mode, out_csv, note):
  times = []
  # warm-up: 캐시 측정(repeat)에서는 1회 선호출로 채움
  if mode == "repeat":
    requests.get(url, params={"user":user,"start":start,"end":end}).json()

  with open(out_csv, "a", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    # 헤더가 없다면 수동 관리(처음에만 추가 권장)
    # w.writerow(["ts","mode","user","start","end","iter","elapsed_ms","note"])
    for i in range(1, n+1):
      t0 = ms()
      r = requests.get(url, params={"user":user,"start":start,"end":end})
      t1 = ms()
      elapsed = t1 - t0
      times.append(elapsed)
      w.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), mode, user, start, end, i, f"{elapsed:.3f}", note])

  avg = sum(times)/len(times)
  std = statistics.pstdev(times) if len(times)>1 else 0.0
  med = statistics.median(times)
  print(f"[{mode}] n={n} avg={avg:.3f} ms, std={std:.3f}, median={med:.3f}")
  return avg, std, med

if __name__=="__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--base", default="http://127.0.0.1:5000")
  ap.add_argument("--user", type=int, default=100)          # 존재하는 user_id 대략값
  ap.add_argument("--days", type=int, default=30)           # 최근 N일
  ap.add_argument("--n", type=int, default=30)
  ap.add_argument("--mode", choices=["initial","repeat"], default="initial")
  ap.add_argument("--csv", default="results.csv")
  ap.add_argument("--note", default="C0_1k")                # 조건/규모 표기
  args = ap.parse_args()

  end = date.today()
  start = end - timedelta(days=args.days)
  url = args.base + "/api/attendance"

  run(url, args.user, start.isoformat(), end.isoformat(), args.n, args.mode, args.csv, args.note)