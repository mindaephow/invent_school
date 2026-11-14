# 화면 하단 규칙 바가 읽는 상태 파일(public/_rule_status.json) — Claude 쪽 상시 감시(포니테일 사다리·상시검사)가 돌았음을 화면에 알린다(사용자 지시 2026-11-09).
#   rule_status.put("ponytail", {...}) 처럼 키 하나씩 덧쓴다. 실패해도 본 작업을 막지 않는다.
import json, os, time
FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "public", "_rule_status.json")

def put(key, value):
    try:
        d = json.load(open(FILE, encoding="utf-8")) if os.path.exists(FILE) else {}
        d[key] = dict(value, ts=int(time.time() * 1000))
        json.dump(d, open(FILE, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass

def sync_writelock():
    """빌드 쓰기 잠김 기록(.open_retry.log)을 칩이 읽는 상태로 옮긴다 — 기록이 비면 칩이 초록(사용자 지시 2026-11-15)."""
    lg = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".open_retry.log")
    try: ls = open(lg, encoding="utf-8").read().splitlines() if os.path.exists(lg) else []
    except Exception: return
    st = [l for l in ls if "[시작]" in l]
    put("writelock", {"n": len(st), "fail": sum(1 for l in ls if "[끝내 실패]" in l), "last": (st[-1][:160] if st else "")})
