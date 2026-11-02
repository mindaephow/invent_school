# 결합 경우 카탈로그 — 사용자가 ✓(완료) 한 번호들의 "완성된 결합 모습"에서 결합 경우를 전부 뽑아 표로 만든다(기본은 모든 번호, ONLY_DONE=1 이면 ✓ 번호만; 사용자 지시 2026-11-03:
# "전체 결합 모습을 보면 결합 경우들이 나온다 — 그걸 보면 규칙이 다 정리된다. 아직도 틀리는 건 주먹구구라는 것").
#   python coupling_catalog.py [조립도이름 …]     (이름을 안 주면 ✓ 번호가 있는 조립도 전부)  → coupling_catalog.json·coupling_catalog.md
# 하는 일
#   1) 조립도 스크립트를 probe 로 실행(파일은 안 쓴다) → 번호 k 시점의 자세(옮겨진 묶음 반영)로 보이는 부품(숨김 제외)을 놓는다.
#   2) ✓ 번호의 새 부품마다 돌기↔구멍 맞물림(asmlib._mate)을 전부 찾아 "결합 경우"(돌기 부품.돌기 id → 구멍 부품)로 센다 — 구멍 축 위 중심 어긋남·축 어긋남도 모은다.
#   3) 볼트·너트·리벳은 지나는 판 묶음을 재서 머리·끝·너트 머리의 위치를 센 값으로 모은다(stepchecks.bolt_nut_fit 과 같은 기준).
#   4) 경우마다 가장 흔한 값(최빈값)과 벗어난 번호를 적는다 — 벗어난 번호가 틀린 결합 후보다.
import sys, os, json, runpy, collections, glob
import numpy as np
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE); sys.path.insert(0, HERE)
import userdone, obb, stepchecks
from asmlib import euler_to_R, _mate

FRAMEISH = lambda n: "프레임" in n or "블록" in n or n == "서보혼"

def pose_at(A, q, k):
    key = "%d:%d" % (q.step.index, q.step.parts.index(q))
    for j in range(k, 0, -1):
        e = (A.steps[j - 1].kw.get("moveMade") or {}).get(key)
        if e: return np.array(e["p"], float), np.array(euler_to_R(e["r"]), float)
    mv = q.extra.get("move")   # 옛 방식(extra["move"]): 빌드 전 probe 에서는 moveMade 가 없어도 그 번호부터 옮긴 자리·자세로 놓여야 한다
    if mv and mv.get("at", 10 ** 6) <= k: return np.array(mv["p"], float), np.array(euler_to_R(mv["r"]), float)
    return stepchecks._pose(q, k)

class V: pass

def view(A, k):
    hide = A.steps[k - 1].kw.get("hideMade") or {}
    out = []
    for k2, st in enumerate(A.steps, 1):
        if k2 > k or str(k2) in hide: continue
        for q in st.parts:
            _key = "%d:%d" % (q.step.index, q.step.parts.index(q)); _sl = st.kw.get("slot", 1)   # 부품이 지금 있는 창고: 만든 번호의 창고, 옮겨졌으면(moveMade) 옮긴 번호의 창고
            for _j in range(k, 0, -1):
                if (A.steps[_j - 1].kw.get("moveMade") or {}).get(_key): _sl = A.steps[_j - 1].kw.get("slot", 1); break
            if _sl != A.steps[k - 1].kw.get("slot", 1): continue   # 다른 창고에 있는 부품은 이 번호 화면에 같이 안 놓인다
            if "%d:%d" % (k2, st.parts.index(q)) in hide: continue   # hideMade 의 "번호:부품순서" 칸 — 부품 하나만 숨김
            p, R = pose_at(A, q, k); o = V(); o.p, o.R, o.n, o.conn, o.src, o.new = p, R, q.n, q.conn, q, (k2 == k); out.append(o)
    return out

def feats(o, kind):
    return [{"id": c["id"], "pos": o.p + o.R @ np.array(c["pos"], float), "dir": o.R @ np.array(c["dir"], float), "len": c.get("len", 0) or 0, "r": c.get("r", 0), "through": c.get("through", False)} for c in o.conn[kind]]

def scan(A, k, dims, rows, fast):
    vs = view(A, k)
    pf = {id(o): feats(o, "pegs") for o in vs}; hf = {id(o): feats(o, "holes") for o in vs}
    for P in [o for o in vs if o.new and not o.src.extra.get("copyOf")]:
        for a in vs:
            if a is P: continue
            for peg_o, hole_o in ((P, a), (a, P)):          # P 의 돌기→a 의 구멍, a 의 돌기→P 의 구멍
                for pg in pf[id(peg_o)]:
                    for ho in hf[id(hole_o)]:
                        if _mate(pg, ho):
                            rel = pg["pos"] - ho["pos"]; along = float(np.dot(rel, ho["dir"])); lat = float(np.linalg.norm(rel - along * ho["dir"]))
                            rows.append({"asm": A.id, "step": k, "peg": "%s.%s" % (peg_o.n, pg["id"]), "hole": hole_o.n, "along": round(along, 1), "lat": round(lat, 2)})
    # 볼트·너트 판 묶음
    pool = []   # (부품, 중심, 자세, 반치수) — 브라켓은 L자라 상자 대신 구멍 하나마다 두께 5mm 날개 조각으로 넣는다(프레임과 같은 규격)
    for o in vs:
        if o.n not in dims: continue
        if "브라켓" in o.n or "서보혼" in o.n:
            for c_ in o.conn["holes"]:
                ax_ = int(np.argmax(np.abs(c_["dir"]))); d_ = np.array([6.0, 6.0, 6.0]); d_[ax_] = 2.5
                pool.append((o, o.p + o.R @ np.array(c_["pos"], float), o.R, d_))
        elif FRAMEISH(o.n) or "기어" in o.n: pool.append((o, o.p, o.R, np.array(dims[o.n], float) / 2.0))   # 기어(두께 8·9)도 볼트가 지나는 판 — 실측 큰기어 9
    for b in [o for o in vs if o.new and o.n in ("8볼트", "12볼트") and o.conn["pegs"]]:
        c = b.conn["pegs"][0]; ld = np.array(c["dir"], float); dw = b.R @ ld; ax = int(np.argmax(np.abs(ld)))
        base = b.p + b.R @ (np.array(c["pos"], float) - ld * c["len"] / 2); tip = base + dw * c["len"]
        head = float(np.dot(np.array(c["pos"], float) - ld * c["len"] / 2, ld) + np.array(dims[b.n], float)[ax] / 2)
        fr = []; gear = False
        for q, p, R, d in pool:
            if any(obb.contains(base - dw * head + dw * s, p, R, d, 0.01) for s in np.arange(0.25, c["len"] + head, 0.5)):
                sp = obb.span(obb.corners(p, R, d), dw); fr.append((float(sp[0]), float(sp[1]))); gear = gear or "기어" in q.n
        if not fr: continue
        top = min(f[0] for f in fr); bot = max(f[1] for f in fr); hd = float(np.dot(base - dw * head, dw)); tp = float(np.dot(tip, dw))
        has_nut = any(o.new and o.n == "너트" for o in vs)
        fast.append({"asm": A.id, "step": k, "kind": b.n, "nut": has_nut, "gear": gear, "stack": round(bot - top, 1), "head_off": round(hd - top, 1), "tip_off": round(tp - bot, 1)})
    for n in [o for o in vs if o.new and o.n == "너트" and o.conn["pegs"]]:
        c = n.conn["pegs"][0]; ld = np.array(c["dir"], float); dn = n.R @ ld
        nb = n.p + n.R @ (np.array(c["pos"], float) - ld * c["len"] / 2); fr = []
        for q, p, R, d in pool:
            if any(obb.contains(nb + dn * s, p, R, d, 0.01) for s in np.arange(0.25, c["len"], 0.5)):
                sp = obb.span(obb.corners(p, R, d), dn); fr.append(float(sp[0]))
        if fr: fast.append({"asm": A.id, "step": k, "kind": "너트", "nut_off": round(float(np.dot(nb, dn)) - (min(fr) + 1.0), 1)})

def main():
    want = sys.argv[1:]
    names = want or sorted(os.path.basename(p)[:-3] for p in glob.glob("*.py") if not os.path.basename(p).startswith(("scratch", "new_assembly")) and any(l.startswith("A = Asm(") for l in open(p, encoding="utf-8")))
    dims = stepchecks._dims(); rows = []; fast = []; used = {}
    for nm in names:
        try:
            A = runpy.run_path(nm + ".py", run_name="probe")["A"]
            done = sorted(userdone.user_done(A.id)) if os.environ.get("ONLY_DONE") == "1" else list(range(1, len(A.steps) + 1))   # 사용자 ✓ 는 DB 에 거의 없어 기본은 모든 번호(가장 흔한 값이 기준, 벗어난 번호가 후보)
        except SystemExit as e: print("⚠", nm, "건너뜀:", e); continue
        except Exception as e: print("⚠", nm, "건너뜀(실행 오류):", repr(e)[:90]); continue
        used[nm] = done
        for k in done:
            if 1 <= k <= len(A.steps):
                try: scan(A, k, dims, rows, fast)
                except Exception as e: print("⚠", nm, k, "번 분석 오류:", repr(e)[:80])
        print(nm, "✓ 번호", len(done), "개 분석")
    json.dump({"rows": rows, "fast": fast, "used": used}, open("coupling_catalog.json", "w", encoding="utf-8"), ensure_ascii=False)
    # 경우별 집계
    by = collections.defaultdict(list)
    for r in rows: by[(r["peg"], r["hole"])].append(r)
    lines = ["# 결합 경우 카탈로그 (사용자 ✓ 번호 기준)", "", "| 돌기 → 구멍 | 횟수 | 구멍 축 위 중심 어긋남(mm) 최빈 | 범위 | 축 어긋남 최대 |", "|---|---|---|---|---|"]
    for key, v in sorted(by.items(), key=lambda kv: -len(kv[1])):
        al = [x["along"] for x in v]; mode = collections.Counter(al).most_common(1)[0][0]
        lines.append("| %s → %s | %d | %+.1f | %+.1f ~ %+.1f | %.2f |" % (key[0], key[1], len(v), mode, min(al), max(al), max(x["lat"] for x in v)))
    lines += ["", "## 볼트·너트 (판 묶음 기준, mm)", "", "| 종류 | 항목 | 횟수 | 최빈 | 범위 |", "|---|---|---|---|---|"]
    for kind in ("8볼트", "12볼트"):
        for fld in ("stack", "head_off", "tip_off"):
            vals = [f[fld] for f in fast if f.get("kind") == kind and fld in f and f.get("nut")]
            if vals: lines.append("| %s(너트 있음) | %s | %d | %+.1f | %+.1f ~ %+.1f |" % (kind, {"stack": "지나는 판 두께 합", "head_off": "머리 − 맨 위 면", "tip_off": "볼트 끝 − 마지막 면"}[fld], len(vals), collections.Counter(vals).most_common(1)[0][0], min(vals), max(vals)))
    nv = [f["nut_off"] for f in fast if "nut_off" in f]
    if nv: lines.append("| 너트 | 머리 − (면 + 1.0) | %d | %+.1f | %+.1f ~ %+.1f |" % (len(nv), collections.Counter(nv).most_common(1)[0][0], min(nv), max(nv)))
    open("coupling_catalog.md", "w", encoding="utf-8").write("\n".join(lines) + "\n"); print("\n".join(lines[:60]))

if __name__ == "__main__": main()
