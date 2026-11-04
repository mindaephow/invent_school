# 부품 연결점 라이브러리 — 조립 프로그램(asmlib.py)과 로컬 검사(check_local.js)가 같이 쓴다.
# 부품의 크기·돌기·구멍은 부품 DB 의 상세내역(ivs_part_catalog 의 data.detail)이 원본이다(사용자 지시 2026-11-04).
# build_all() 이 DB 상세내역을 읽어 conn.json·dims.json 을 만든다. 부품 값을 이 파일에 따로 적지 않는다(프레임 규칙·OTHER 삭제).
import json, re, os, urllib.request

_DIR = {"+x": [1, 0, 0], "-x": [-1, 0, 0], "+y": [0, 1, 0], "-y": [0, -1, 0], "+z": [0, 0, 1], "-z": [0, 0, -1]}

def load_details():
    """DB 상세내역을 읽는다 → {부품이름: detail}. 같은 이름이 여러 행이면 상세내역이 있는 행을 쓴다. 읽지 못하면 {}."""
    env = {}
    try:
        for ln in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env.local"), encoding="utf-8"):
            if "=" in ln and not ln.lstrip().startswith("#"):
                k, v = ln.split("=", 1); env[k.strip()] = v.strip().strip('"').strip("'")
        url = (env.get("SUPABASE_URL") or env.get("NEXT_PUBLIC_SUPABASE_URL")).rstrip("/"); key = env["SUPABASE_SERVICE_ROLE_KEY"]
        q = url + "/rest/v1/ivs_part_catalog?select=name:data->>name,detail:data->detail&data->>subject=eq.robot&limit=1000"
        rows = json.loads(urllib.request.urlopen(urllib.request.Request(q, headers={"apikey": key, "Authorization": "Bearer " + key}), timeout=30).read().decode("utf-8"))
    except Exception as e:
        print("⚠ 부품 DB 상세내역을 읽지 못했다:", e); return {}
    out = {}
    for r in rows:
        if r.get("detail") and r["name"] not in out: out[r["name"]] = r["detail"]
    return out

def from_detail(d):
    """상세내역 → {size, pegs, holes}. 지름→r, 방향 문자열→벡터."""
    sz = d.get("크기_mm") or {}
    size = [sz.get("가로(x)"), sz.get("높이(y)"), sz.get("세로(z)")]
    pegs = [{"id": p["번호"], "pos": p["위치"], "dir": _DIR[p["방향"]], "len": p["길이"], "r": p["지름"] / 2} for p in (d.get("돌기") or {}).get("목록", [])]
    holes = [{"id": h["번호"], "pos": h["위치"], "dir": _DIR[h["방향"]], "len": h["길이"], "r": h["지름"] / 2, "through": bool(h.get("관통"))} for h in (d.get("구멍") or {}).get("목록", [])]
    return {"size": size, "pegs": pegs, "holes": holes}

_CACHE = {}

def get(name):
    """부품 하나의 {size, pegs, holes} — build_all() 이 만든 conn.json·dims.json 에서 읽는다(원본은 DB 상세내역)."""
    if not _CACHE:
        here = os.path.dirname(os.path.abspath(__file__))
        conn = json.load(open(os.path.join(here, "conn.json"), encoding="utf-8")); dims = json.load(open(os.path.join(here, "dims.json"), encoding="utf-8"))
        for n in conn: _CACHE[n] = {"pegs": conn[n]["pegs"], "holes": conn[n]["holes"], "size": dims[n]}
    return _CACHE[name]

def build_all(details=None):
    """DB 상세내역(크기·돌기·구멍)이 있는 모든 부품 → (conn, dims). 상세내역이 없는 부품은 만들지 않는다."""
    details = load_details() if details is None else details
    conn, dims = {}, {}
    for n, d in details.items():
        sz = d.get("크기_mm") or {}
        if not all(isinstance(sz.get(k), (int, float)) for k in ("가로(x)", "높이(y)", "세로(z)")): continue
        c = from_detail(d)
        conn[n] = {"pegs": c["pegs"], "holes": c["holes"]}; dims[n] = c["size"]
    return conn, dims

def build_heads(details=None):
    """대가리(머리) 두께·지름이 상세내역에 있는 부품 → {부품이름: {"두께": mm, "지름": mm}} (heads.json). asmlib 가 머리가 밖으로 남는 두께로 쓴다."""
    details = load_details() if details is None else details
    out = {}
    for n, d in details.items():
        hb = d.get("대가리_몸통") or {}
        if isinstance(hb.get("대가리 두께_mm"), (int, float)): out[n] = {"두께": hb["대가리 두께_mm"], "지름": hb.get("대가리 지름_mm")}
    return out

if __name__ == "__main__":
    json.dump(build_heads(), open("heads.json", "w", encoding="utf-8"), ensure_ascii=False)
    conn, dims = build_all()
    if not conn: raise SystemExit("상세내역을 읽지 못해 conn.json 을 만들지 않았다")
    json.dump(conn, open("conn.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(dims, open("dims.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(len(conn), "parts")
