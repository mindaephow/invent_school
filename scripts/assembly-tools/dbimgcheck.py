# 로컬 refs/<이름>/index.json 의 그림이 DB(ivs_assembly_refs)에 올라갔는지 비교한다(읽기 전용, 규칙 B5·I1).
#   python dbimgcheck.py <이름> [번호 ...]     번호를 주면 그 번호만, 없으면 전체
# 결과: 로컬에 있는데 DB 에 없는 그림(안 올림) / DB 에 있는데 로컬 index 에 없는 그림 / 설명(note)이 다른 그림.
# 안 올린 그림이 있으면 종료 코드 1 — 번호를 끝내기 전에 돌려서 0 이 되게 한다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, os, json, urllib.request
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from userdone import _env


def db_rows(assembly_id):
    env = _env()
    url = env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL"); key = env.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key: sys.exit("❌ .env.local 에 SUPABASE_URL·SUPABASE_SERVICE_ROLE_KEY 가 없다")
    req = urllib.request.Request(url.rstrip("/") + "/rest/v1/ivs_assembly_refs?select=step,idx,note&assembly_id=eq." + assembly_id, headers={"apikey": key, "Authorization": "Bearer " + key})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf-8"))
    except Exception as e:
        sys.exit("❌ DB 를 읽지 못했다(%s)" % e)


def main():
    if len(sys.argv) < 2: sys.exit(__doc__)
    name = sys.argv[1]; only = {int(v) for v in sys.argv[2:]}
    idx = json.load(open(os.path.join(HERE, "refs", name, "index.json"), encoding="utf-8"))
    import re   # 조립도 id 는 <이름>.py 의 Asm("cubo-3-hammerbattle", ...) 첫 인자
    m = re.search(r'''Asm\(\s*["']([^"']+)["']''', open(os.path.join(HERE, name + ".py"), encoding="utf-8").read())
    aid = m.group(1) if m else None
    if not aid: sys.exit("❌ %s.py 에서 Asm(\"조립도id\", ...) 를 찾지 못했다" % name)
    db = {(r["step"], r["idx"]): r["note"] for r in db_rows(aid)}
    loc = {(e["step"], e["idx"]): e for e in idx if not only or e["step"] in only}
    miss = sorted(k for k in loc if k not in db)
    extra = sorted(k for k in db if (not only or k[0] in only) and k not in loc)
    diff = sorted(k for k in loc if k in db and (db[k] or "").strip() != (loc[k].get("note") or "").strip())
    print("조립도 %s · 로컬 %d장 · DB %d장%s" % (aid, len(loc), sum(1 for k in db if not only or k[0] in only), (" · 번호 " + ",".join(map(str, sorted(only)))) if only else ""))
    print("❌ 안 올림(로컬에만 있음): %s" % (", ".join("%d_%d" % k for k in miss) or "없음"))
    print("⚠ DB 에만 있음(로컬 index 에 없음): %s" % (", ".join("%d_%d" % k for k in extra) or "없음"))
    print("⚠ 설명이 다름(올린 뒤 index 를 고쳤으면 다시 올린다): %s" % (", ".join("%d_%d" % k for k in diff) or "없음"))
    sys.exit(1 if miss else 0)


main()
