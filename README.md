# Backend Perf Lab — Index & Cache Experiment

Flask + SQLite 기반 동아리 웹앱에서 **인덱스/캐시 적용에 따른 응답시간**을 비교하는 실험용 저장소입니다.
조건 4종(C0~C3)과 데이터 규모(1k/5k/10k)별로 **반복 측정 → 집계 → 그래프 출력**까지 자동화되어 있습니다.

* **C0**: Baseline (인덱스×, 캐시×)
* **C1**: Index Only
* **C2**: Cache Only (TTL 기본 60s)
* **C3**: Index + Cache

---

## 1) 요구사항

* Python 3.10+ (권장 3.11)
* OS: Windows / macOS / Linux
* 네트워크 접속 가능한 웹브라우저(결과 확인용)

---

## 2) 프로젝트 구조

```
backend-perf-lab/
├─ app.py                # Flask 서버(인덱스/캐시 토글)
├─ generate_data.py      # SQLite 데이터 생성 스크립트
├─ measure.py            # 응답시간 측정(클라이언트)
├─ analyze_with_plots.py # 집계 + matplotlib 그래프
├─ requirements.txt
└─ data/
    ├─ db_1k.sqlite3
    ├─ db_5k.sqlite3
    └─ db_10k.sqlite3
```

> 처음엔 `data/`가 비어 있어도 됩니다. 아래 4)에서 DB를 생성합니다.

---

## 3) 설치 (가상환경 권장)

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux (Bash)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

> ❗ 에러: `ModuleNotFoundError: No module named 'flask'` → 가상환경 활성화 후 `pip install -r requirements.txt` 재실행

---

## 4) 데이터 생성 (SQLite)

아래 명령으로 1k/5k/10k 레코드 DB를 생성합니다.

```bash
# 공통(운영체제 무관)
python generate_data.py data/db_1k.sqlite3   1000
python generate_data.py data/db_5k.sqlite3   5000
python generate_data.py data/db_10k.sqlite3 10000
```

---

## 5) 서버 실행 (조건 토글)

서버는 환경변수로 동작 조건을 제어합니다.

* `DB_PATH` : 데이터베이스 파일 경로 (예: `data/db_1k.sqlite3`)
* `USE_INDEX` : 0/1
* `USE_CACHE` : 0/1
* `CACHE_TTL` : 캐시 TTL(초), 기본 60

### Windows PowerShell

```powershell
# C0: Baseline
$env:DB_PATH="data/db_1k.sqlite3"; $env:USE_INDEX="0"; $env:USE_CACHE="0"; $env:CACHE_TTL="60"; python app.py
# C1: Index Only
$env:DB_PATH="data/db_1k.sqlite3"; $env:USE_INDEX="1"; $env:USE_CACHE="0"; $env:CACHE_TTL="60"; python app.py
# C2: Cache Only
$env:DB_PATH="data/db_1k.sqlite3"; $env:USE_INDEX="0"; $env:USE_CACHE="1"; $env:CACHE_TTL="60"; python app.py
# C3: Index + Cache
$env:DB_PATH="data/db_1k.sqlite3"; $env:USE_INDEX="1"; $env:USE_CACHE="1"; $env:CACHE_TTL="60"; python app.py
```

### macOS / Linux (Bash)

```bash
# C0
DB_PATH=data/db_1k.sqlite3 USE_INDEX=0 USE_CACHE=0 CACHE_TTL=60 python app.py
# C1
DB_PATH=data/db_1k.sqlite3 USE_INDEX=1 USE_CACHE=0 CACHE_TTL=60 python app.py
# C2
DB_PATH=data/db_1k.sqlite3 USE_INDEX=0 USE_CACHE=1 CACHE_TTL=60 python app.py
# C3
DB_PATH=data/db_1k.sqlite3 USE_INDEX=1 USE_CACHE=1 CACHE_TTL=60 python app.py
```

#### 서버 헬스체크

* 브라우저에서 `http://127.0.0.1:5000/health` 열어 JSON 확인
* 인덱스 사용 검증: `http://127.0.0.1:5000/api/plan?user=100&start=2025-09-01&end=2025-09-30`

> ❗ Flask 3.x에서는 `before_first_request` 훅이 제거되었습니다. 본 저장소의 `app.py`는 해당 사항을 반영해 초기화 코드를 수정해 두었습니다.

---

## 6) 측정 (results.csv 누적 기록)

서버가 떠 있는 터미널을 유지한 채, **다른 터미널**에서 아래를 실행합니다.

```bash
# 예시: 30회 반복 측정, note는 조건/규모 표기 용도
python measure.py --n 30 --mode initial --csv results.csv --note C0_1k
python measure.py --n 30 --mode repeat  --csv results.csv --note C0_1k
```

조건(C1/C2/C3)과 규모(5k/10k)로 DB_PATH와 서버 조건을 바꿔가며 동일하게 측정하세요.
`--note`는 `C1_5k`, `C2_10k`처럼 구분 이름만 바꿔 기록하면 됩니다.

* 주요 옵션

  * `--base` : 서버 주소(기본 `http://127.0.0.1:5000`)
  * `--user` : 조회할 user_id (기본 100, DB에 존재하는 id 권장)
  * `--days` : 최근 N일(기본 30)
  * `--mode` : `initial`(초회) / `repeat`(재조회, 자동 워밍업 1회 포함)

---

## 7) 집계 & 그래프 생성

아래를 실행하면 **요약표 + 개선율 계산 + 그래프(PNG)**가 생성됩니다.

```bash
python analyze_with_plots.py
```

생성물:

* `plots/summary_by_size_cond_mode.csv`
* `plots/summary_with_improvement.csv`
* `plots/avg_{size}_{mode}.png` (오차막대=표준편차)
* `plots/improve_{size}_{mode}.png` (C0 대비 개선율 %)

> 개선율(%) = ((Baseline 평균 − 조건 평균) ÷ Baseline 평균) × 100

---

## 8) 추천 실행 루틴(권장 순서)

1. **1k DB**로 C0 → C1 → C2 → C3 순서 실행 및 측정(초회/재조회 각각 `--n 30`)
2. **5k, 10k DB**에서도 동일 루틴 반복
3. `analyze_with_plots.py` 실행 → `plots/` 내 CSV/PNG를 보고서에 삽입
4. 인덱스 사용 검증은 `/api/plan` 응답으로 확인

---

## 9) 자주 만나는 오류 & 해결

* **PowerShell에서 `DB_PATH=... python app.py`가 동작하지 않음**
  → Windows는 `$env:DB_PATH="..." ; python app.py` 형식 사용(위 5) 참고)

* **`ModuleNotFoundError: No module named 'flask'`**
  → 가상환경 활성화 후 `pip install -r requirements.txt`

* **`AttributeError: 'Flask' object has no attribute 'before_first_request'`**
  → Flask 3.x 변화. 저장소의 `app.py`는 수정 반영됨(이전 코드 사용 시 훅 제거/대체 필요)

* **포트 충돌 (`OSError: [Errno 98] Address already in use`)**
  → 기존 서버 종료 또는 `set FLASK_RUN_PORT=5001` 등 다른 포트 사용

* **results.csv 형식 오류**
  → `measure.py`가 생성하는 기본 스키마를 유지하세요
  → 컬럼: `ts,mode,user,start,end,iter,elapsed_ms,note`

---

## 10) 개인정보/윤리 유의사항

* 실험 데이터는 **가명/랜덤 생성**을 사용하세요.
* 캐시에는 **민감정보 저장 금지**, TTL/무효화 정책 준수.
* 결과 해석은 **평균 + 분포(표준편차/상자그림)**를 함께 보며 과장 금지.

---

## 11) 보고서 삽입 팁

* **표 1**: `plots/summary_with_improvement.csv`에서 10k(또는 학교 지시 규모) 행만 추출
* **그림 1~4**: `avg_{size}_{mode}.png`, `improve_{size}_{mode}.png` 삽입
* **캡션**: “오차막대는 표준편차”, “개선율은 C0 대비 평균 기준” 명시
* **핵심 문장**:

  * 인덱스는 **초회 조회**에 효과, 캐시는 **재조회**에서 탁월
  * 병행(C3)은 환경에 따라 캐시 단독과 유사할 수 있어 **접근 패턴 기반 선택** 권장

---

## 12) 확장 아이디어

* DB: SQLite → MySQL/PostgreSQL, ORM(SQLAlchemy) 적용
* 최적화: 페이지네이션, SELECT 칼럼 최소화, 비동기 I/O(FastAPI)
* 측정: `wrk`/`ab` 부하도구, 동시접속(`-c`) 실험, 히트율 분석

---

### 부록 A) 자동 실행 스크립트 예시

**Windows PowerShell — 1k 전체 루틴**

```powershell
$env:DB_PATH="data/db_1k.sqlite3"; $env:CACHE_TTL="60"

# C0
$env:USE_INDEX="0"; $env:USE_CACHE="0"; Start-Process powershell -ArgumentList "python app.py"
Start-Sleep -Seconds 2
python measure.py --n 30 --mode initial --note C0_1k
python measure.py --n 30 --mode repeat  --note C0_1k
Get-Process python | Where-Object {$_.MainWindowTitle -like "*app.py*"} | Stop-Process

# C1
$env:USE_INDEX="1"; $env:USE_CACHE="0"; Start-Process powershell -ArgumentList "python app.py"
Start-Sleep -Seconds 2
python measure.py --n 30 --mode initial --note C1_1k
python measure.py --n 30 --mode repeat  --note C1_1k
Get-Process python | Where-Object {$_.MainWindowTitle -like "*app.py*"} | Stop-Process

# (C2, C3도 동일 패턴)
```

**macOS/Linux — 1k 전체 루틴(개념 예시)**

```bash
export DB_PATH=data/db_1k.sqlite3 CACHE_TTL=60

USE_INDEX=0 USE_CACHE=0 python app.py &  # C0
PID=$!; sleep 2
python measure.py --n 30 --mode initial --note C0_1k
python measure.py --n 30 --mode repeat  --note C0_1k
kill $PID

# (C1/C2/C3 반복)
```

---
