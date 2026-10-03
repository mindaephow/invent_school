# 새 조립도의 뼈대를 만든다 (오토건 스크립트를 보고 베끼던 일을 대신한다).
#   python new_assembly.py <이름> "<차시 제목>" [권]      예: python new_assembly.py airplane 조종형비행기 1
#   환경변수 IVS_MCP_URL = 발명학교 MCP 주소(키 포함)가 있으면 교재관리에서 그 차시의 부품 목록(LIST)을 읽어 온다.
#   없으면 --list '{"2단블록":9,"3단블록":8}' 처럼 직접 준다.  --dir 폴더 로 다른 곳에 만들 수 있다(시험용).
# 만드는 파일(이미 있으면 덮어쓰지 않는다):
#   <이름>.py          스크립트 뼈대: 조립도 이름·LIST 주석·1단계 틀·마무리 호출 (오토건 autogun.py 와 같은 구조)
#   <이름>_list.json   교재 LIST (build.py 가 개수 대조에 쓴다)
#   <이름>_def.json    조립도 메모(listNote 등)
#   <이름>_rules.json  눈으로 확인한 단계 기록 {"count": [], "view": [], "camera": []}
# 그다음: 스크립트에 1단계부터 순서대로 적고(오토건 autogun.py 참고) python build.py <이름> 으로 검사한다.
import sys, os, json, re, urllib.request

def mcp_sql(url, sql):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "run_sql", "arguments": {"sql": sql}}}, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"})
    raw = urllib.request.urlopen(req, timeout=120).read().decode("utf-8")
    line = [l[6:] for l in raw.splitlines() if l.startswith("data: ")][0]
    r = json.loads(line).get("result", {})
    text = "\n".join(c.get("text", "") for c in r.get("content", []))
    if r.get("isError"):
        raise RuntimeError(text)
    return json.loads(text[text.index("["):])

def fetch_list(url, volume, title):
    t = title.replace("'", "''").replace(" ", "")
    sql = ("select pc.data->>'name' as name, (p->>'qty')::int as qty "
           "from ivs_textbooks t, jsonb_array_elements(t.data->'chapters') c, jsonb_array_elements(c->'parts') p "
           "left join ivs_part_catalog pc on pc.id::text = p->>'partId' "
           f"where t.data->>'volume' = '{int(volume)}' and replace(c->>'title', ' ', '') = '{t}'")
    rows = mcp_sql(url, sql)
    out = {}
    for r in rows:
        out[r["name"] or "(DB에 없는 부품)"] = out.get(r["name"] or "(DB에 없는 부품)", 0) + int(r["qty"] or 0)
    return out

SKELETON = '''# 큐보 {volume}권 {title}(교재 ?~?쪽) — 조립 프로그램(asmlib)으로 만든다.  ← 쪽 번호를 채운다 (교재 PDF 쪽 번호 = 교재 쪽 번호)
# 순서대로 만든다: 1단계 → 확인 → 2단계 → 확인 …  (뒤에서부터 만들거나 중간부터 시작하지 않는다)
# 각 단계: 교재 그림을 왼쪽→오른쪽, 위→아래로 읽고(부품·초록 원·화살표), get_step_context 로 직전 상태(쓴 부품·남은 부품·빈 구멍)를 본 뒤 적는다.
# 교재 LIST(부품 목록, {count}개 종류):
{list_comment}
import json, sys
import numpy as np
from asmlib import *

A = Asm("cubo-{volume}-{id}", "{title}", "교재 ?~?쪽 · {title} (1~?단계)", camera={{"target": [60, 20, 0], "radius": 380, "theta": 0.9, "phi": 1.0}},
        listNote="만드는 중 — 단계가 끝나기 전까지 LIST 개수는 안 맞는 것이 정상")
RELOCK = "--relock" in sys.argv   # 잠금 기록을 새로 만들 때(수정 지시는 이번 빌드에서 무시한다)
if not RELOCK: A.load_fixes("{name}_fixes.json")   # 관리자 수정 지시(앞 단계 수정 → 뒤 단계가 따라온다). 파일이 없으면 아무 일도 안 한다
A.load_links("{name}_links.json", relock=RELOCK)   # 좌표로 쓴 결합·절대 좌표로 놓은 판을 이름으로 잠가 두는 기록
UP = (0, 1, 0)

# ── 1 ── (교재 1: 첫 부품은 pt/place 로 직접 놓고, 나머지는 이름으로 결합한다)
# 예)  s1 = A.step("[교재 1] ...")
#      base = s1.place("315프레임", orient("315프레임", {{"홀면 +y": "위"}}), (75, 2.5, 0))
#      blk  = s1.attach("3단블록", orient("3단블록", {{"돌기면 +z": "아래", "홀면 +y": "+Z"}}), {{"돌기면 +z 1": ("315프레임 1번", "홀면 +y 열14·줄1"), "돌기면 +z 3": ("315프레임 1번", "홀면 +y 열15·줄1")}}, hover=45)
# 구멍·돌기는 이름(면 +축, 열·줄)으로 말한다(안내서 3-1절). 번호를 모르면 get_part_faces / get_step_context 로 본다.

A.save_links()                                    # 이번 빌드의 잠금 기록 저장(수정 지시가 있는 빌드는 갱신하지 않는다)
A.check_fixes()                                   # 적용되지 않은 수정 지시가 있으면 경고(번호가 밀렸거나 오타)
A.report = lambda: [print("경고:", w) for w in A.warn]
if __name__ == "__main__":
    steps = export_steps(A)
    json.dump({{"steps": steps}}, open("{name}_asm.json", "w", encoding="utf-8"), ensure_ascii=False)
    open("{name}_entry.js", "w", encoding="utf-8").write(js_entry(A))
    print(len(steps), "단계,", len(A.parts), "부품", "경고", len(A.warn))
'''

def main():
    a = sys.argv[1:]
    out_dir = os.path.dirname(os.path.abspath(__file__))
    if "--dir" in a:
        i = a.index("--dir"); out_dir = a[i + 1]; del a[i:i + 2]
    listing = None
    if "--list" in a:
        i = a.index("--list"); listing = json.loads(a[i + 1]); del a[i:i + 2]
    if len(a) < 2:
        print(__doc__); sys.exit(1)
    name, title = a[0], a[1]
    volume = int(a[2]) if len(a) > 2 else 1
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", name):
        print("이름은 영문자로 시작하는 영문·숫자·밑줄만 쓸 수 있어요(예: airplane)."); sys.exit(1)
    if listing is None:
        url = os.environ.get("IVS_MCP_URL")
        if not url:
            print("교재 LIST 를 읽으려면 환경변수 IVS_MCP_URL 이 필요해요. 없으면 --list '{\"2단블록\":9}' 로 직접 주세요."); sys.exit(1)
        listing = fetch_list(url, volume, title)
        if not listing:
            print(f"교재관리에서 큐보 {volume}권 '{title}' 차시의 부품 목록을 못 찾았어요(차시 제목이 정확한지 check_chapter_parts 로 확인)."); sys.exit(1)
    missing_db = [n for n in listing if n.startswith("(DB에")]
    conn_f = os.path.join(out_dir, "conn.json")
    known = set(json.load(open(conn_f, encoding="utf-8"))) if os.path.exists(conn_f) else set()
    # 프레임(N프레임)은 규칙으로 만들어지므로 partlib 에 따로 없어도 된다
    need_partlib = [n for n in listing if not re.fullmatch(r"\d\d+프레임", n) and known and n not in known and not n.startswith("(DB에")]
    lc = "\n".join("#   " + n + " " + str(q) for n, q in listing.items())
    files = {
        f"{name}.py": SKELETON.format(volume=volume, title=title, id=name, name=name, count=len(listing), list_comment=lc),
        f"{name}_list.json": json.dumps(listing, ensure_ascii=False),
        f"{name}_def.json": json.dumps({"listNote": "만드는 중 — 단계가 끝나기 전까지 LIST 개수는 안 맞는 것이 정상"}, ensure_ascii=False),
        f"{name}_rules.json": json.dumps({"count": [], "view": [], "camera": []}),
    }
    os.makedirs(out_dir, exist_ok=True)
    for fn, content in files.items():
        path = os.path.join(out_dir, fn)
        if os.path.exists(path):
            print(f"이미 있어서 건너뜀: {fn}")
        else:
            open(path, "w", encoding="utf-8").write(content)
            print(f"만듦: {fn}")
    print(f"\n교재 LIST {len(listing)}종 · 총 {sum(listing.values())}개")
    if missing_db:
        print("⚠ DB 에 없는 부품이 있어요 — 교재 그림을 보고 직접 등록한 뒤 진행(안내서 '첫 30분').")
    if need_partlib:
        print("⚠ conn.json(partlib)에 연결점이 없는 부품: " + ", ".join(need_partlib) + "  → partlib.py 의 OTHER 에 get_part_connectors 결과를 옮긴다.")
    print(f"\n다음: {name}.py 에 1단계부터 순서대로 적고  python build.py {name}  으로 검사한다.")

if __name__ == "__main__":
    main()
