# 한 일 기록·검색 — 했던 점검·수정을 다시 하지 않게 한다(사용자 지시 2026-11-07: "했던 일을 기록해두고 반복하지 않게끔 하는 도구").
#   python worklog.py add  <조립도이름> "<한 일>" ["<결과>"]     일을 끝낼 때마다 한 줄 남긴다(무엇을 돌려 무엇이 나왔나)
#   python worklog.py find <조립도이름> <키워드…>               무거운 점검·조사를 시작하기 전에 먼저 찾는다 — 있으면 그 결과를 쓰고 다시 돌리지 않는다
#   python worklog.py show <조립도이름> [N]                      최근 N개(기본 15)
#   python worklog.py all  <키워드…>                             모든 조립도에서 찾는다
# 기록 위치: 그 조립도 폴더의 작업기록.jsonl (손으로 고치지 않는다). 컨텍스트가 압축돼도 파일에 남으므로 새 세션도 읽을 수 있다.
import asmpath  # 조립도 파일 자리 연결
import sys, os, json, glob, time
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))

def log_path(name):
    try: d = os.path.dirname(asmpath.resolve(name + "_asm.json"))
    except Exception: d = HERE
    return os.path.join(d, "작업기록.jsonl")

def read(path):
    out = []
    if os.path.exists(path):
        for ln in open(path, encoding="utf-8"):
            ln = ln.strip()
            if ln:
                try: out.append(json.loads(ln))
                except Exception: pass
    return out

def show(rows, n=None):
    for r in (rows[-n:] if n else rows): print("%s  %s%s" % (r.get("t", ""), r.get("do", ""), ("  → " + r["res"]) if r.get("res") else ""))
    if not rows: print("(기록 없음)")

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    cmd = a[0]
    if cmd == "add" and len(a) >= 3:
        row = {"t": time.strftime("%Y-%m-%d %H:%M"), "do": a[2], "res": a[3] if len(a) > 3 else ""}
        with open(log_path(a[1]), "a", encoding="utf-8") as f: f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print("기록함:", a[2])
    elif cmd == "find" and len(a) >= 3:
        kw = a[2:]; rows = [r for r in read(log_path(a[1])) if all(k in (r.get("do", "") + " " + r.get("res", "")) for k in kw)]
        show(rows)
    elif cmd == "show" and len(a) >= 2:
        show(read(log_path(a[1])), int(a[2]) if len(a) > 2 else 15)
    elif cmd == "all" and len(a) >= 2:
        kw = a[1:]
        for p in sorted(glob.glob(os.path.join(HERE, "큐보", "조립도", "*", "*", "작업기록.jsonl"))):
            rows = [r for r in read(p) if all(k in (r.get("do", "") + " " + r.get("res", "")) for k in kw)]
            if rows: print("[%s]" % os.path.basename(os.path.dirname(p))); show(rows)
    else: sys.exit(__doc__)
