# 사용자가 조립 보기 화면에서 직접 누른 "완료 ✓" 목록을 DB(ivs_assembly_status)에서 읽어 온다(읽기 전용).
# 이 목록이 번호별 검증의 유일한 근거다(관리자 지시 2026-10-11: 우회 옵션 삭제) — Claude 가 rules.json 에 "확인함"을 적어서 막힘을 푸는 길은 없다.
# DB 를 못 읽으면 빈 집합이 아니라 오류로 멈춘다(읽지 못했다고 통과시키지 않는다).
import json, os, urllib.request

def _env():
    here = os.path.dirname(os.path.abspath(__file__))
    path = os.path.normpath(os.path.join(here, "..", "..", ".env.local"))
    out = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        k, v = line.split("=", 1); out[k.strip()] = v.strip().strip('"').strip("'")
    return out

_cache = {}

def user_done(assembly_id):
    """사용자가 ✓ 완료로 표시한 단계 번호 집합. 같은 실행 안에서는 한 번만 읽는다."""
    if assembly_id in _cache: return _cache[assembly_id]
    env = _env()
    url = env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL"); key = env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key: raise SystemExit("❌ 사용자 완료 표시를 읽을 수 없다(.env.local 에 SUPABASE_URL·SUPABASE_SERVICE_ROLE_KEY 없음) — 읽지 못했으니 --write 를 하지 않는다.")
    req = urllib.request.Request(url.rstrip("/") + "/rest/v1/ivs_assembly_status?select=step,status&assembly_id=eq." + assembly_id, headers={"apikey": key, "Authorization": "Bearer " + key})
    try:
        rows = json.loads(urllib.request.urlopen(req, timeout=20).read().decode("utf-8"))
    except Exception as e:
        raise SystemExit("❌ 사용자 완료 표시를 DB 에서 읽지 못했다(%s) — 읽지 못했으니 --write 를 하지 않는다." % e)
    done = {int(r["step"]) for r in rows if r.get("status") == "done"}
    _cache[assembly_id] = done
    return done
