# generate_data.py
import sqlite3, random, string, os, sys
from datetime import datetime, timedelta
random.seed(42)

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS users(
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS attendance(
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  date TEXT NOT NULL,             -- YYYY-MM-DD
  status TEXT NOT NULL,           -- PRESENT/ABSENT/LATE
  FOREIGN KEY(user_id) REFERENCES users(id)
);
"""

STATUSES = ["PRESENT", "ABSENT", "LATE"]

def rand_name():
  return "User_" + "".join(random.choices(string.ascii_uppercase+string.digits,k=6))

def main(out_path: str, total_rows: int, user_cnt: int=300):
  os.makedirs(os.path.dirname(out_path), exist_ok=True)
  if os.path.exists(out_path):
    os.remove(out_path)
  conn = sqlite3.connect(out_path)
  c = conn.cursor()
  c.executescript(SCHEMA)
  # users
  users = [(i+1, rand_name()) for i in range(user_cnt)]
  c.executemany("INSERT INTO users(id,name) VALUES(?,?)", users)
  # attendance
  start = datetime.today().date() - timedelta(days=120)
  rows = []
  for i in range(total_rows):
    uid = random.randint(1, user_cnt)
    d = start + timedelta(days=random.randint(0, 120))
    st = random.choice(STATUSES)
    rows.append((uid, d.isoformat(), st))
    if len(rows) >= 5000:
      c.executemany("INSERT INTO attendance(user_id,date,status) VALUES(?,?,?)", rows)
      rows.clear()
  if rows:
    c.executemany("INSERT INTO attendance(user_id,date,status) VALUES(?,?,?)", rows)
  conn.commit()
  conn.close()
  print(f"OK: {out_path} with {total_rows} attendance rows and {user_cnt} users.")

if __name__=="__main__":
  # 사용법: python generate_data.py data/db_1k.sqlite3 1000
  if len(sys.argv) < 3:
    print("Usage: python generate_data.py <out_db_path> <rows> [user_cnt]")
    sys.exit(1)
  out = sys.argv[1]; rows = int(sys.argv[2])
  ucnt = int(sys.argv[3]) if len(sys.argv)>=4 else 300
  main(out, rows, ucnt)