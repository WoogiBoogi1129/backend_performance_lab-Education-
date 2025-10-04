# app.py
import os, time, sqlite3
from datetime import date, timedelta
from flask import Flask, request, jsonify

DB_PATH = os.environ.get("DB_PATH") or "data/db_1k.sqlite3"
USE_INDEX = int(os.environ.get("USE_INDEX","0"))
USE_CACHE = int(os.environ.get("USE_CACHE","0"))
CACHE_TTL = int(os.environ.get("CACHE_TTL","60"))

INDEX_NAME = "idx_attendance_user_date"

app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False

_init_done = False  # 1회 실행 가드

# --- 간단 TTL 캐시 ---
_cache = {}  # key -> {"ts": float, "data": any}

def cache_get(key):
  if not USE_CACHE:
    return None
  v = _cache.get(key)
  if not v: return None
  if time.time() - v["ts"] <= CACHE_TTL:
    return v["data"]
  _cache.pop(key, None)
  return None

def cache_set(key, data):
  if not USE_CACHE: return
  _cache[key] = {"ts": time.time(), "data": data}

def open_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_index(conn):
    c = conn.cursor()
    if USE_INDEX:
        c.execute(f"CREATE INDEX IF NOT EXISTS {INDEX_NAME} ON attendance(user_id, date)")
    else:
        c.execute(f"DROP INDEX IF EXISTS {INDEX_NAME}")
    conn.commit()
    
@app.before_request
def _ensure_init_once():
    global _init_done
    if not _init_done:
        conn = open_conn()
        ensure_index(conn)
        conn.close()
        _init_done = True

def parse_params():
  user = request.args.get("user", type=int)
  start = request.args.get("start")
  end = request.args.get("end")
  if not start or not end:
    # 기본: 최근 30일
    end_d = date.today()
    start_d = end_d - timedelta(days=30)
    start = start_d.isoformat()
    end = end_d.isoformat()
  return user, start, end

@app.get("/api/attendance")
def api_attendance():
  user, start, end = parse_params()
  key = f"{user}:{start}:{end}"
  v = cache_get(key)
  if v is not None:
    return jsonify({"source":"cache","rows":v})

  q = "SELECT user_id, date, status FROM attendance WHERE user_id=? AND date BETWEEN ? AND ? ORDER BY date LIMIT 200"
  conn = open_conn(); cur = conn.cursor()
  cur.execute(q, (user, start, end))
  rows = [dict(r) for r in cur.fetchall()]
  conn.close()
  cache_set(key, rows)
  return jsonify({"source":"db","rows":rows})

@app.get("/api/plan")
def api_plan():
  user, start, end = parse_params()
  conn = open_conn(); cur = conn.cursor()
  cur.execute("EXPLAIN QUERY PLAN SELECT * FROM attendance WHERE user_id=? AND date BETWEEN ? AND ?",
              (user, start, end))
  plan = [tuple(r) for r in cur.fetchall()]
  conn.close()
  return jsonify({"plan": plan, "use_index": USE_INDEX})

@app.get("/health")
def health():
  return jsonify({"ok": True, "db": DB_PATH, "use_index": USE_INDEX, "use_cache": USE_CACHE, "ttl": CACHE_TTL})
  
if __name__ == "__main__":
  # flask --app app run --port 5000 --debug  로 실행해도 됨
  app.run(host="0.0.0.0", port=5000)