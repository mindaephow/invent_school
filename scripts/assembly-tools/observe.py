# 관찰 증거 — "조립되는 곳을 모두 눈으로 보고 책과 비교했다"를 파일로 남기고, 없으면 번호를 못 끝내게 막는다(사용자 지시 2026-10-27, 배틀바이크 17번).
#   왜 만들었나: verify_step ✅ 7항목(격자·카메라·돌기↔구멍…)은 위치만 재서 방향(뒤집힘·대칭)을 못 가린다. 그래서 ✅ 만 보고 끝난 줄 알았고 관찰은 증거를 요구하는 곳이 없어 빠졌다.
#   python observe.py add <이름> <번호> <종류> "<지점>" <책크롭.png> <화면크롭.png> 같다|다르다 "<한 줄>"
#       종류: 결합(결합 지점마다 1장) · 그룹비교(같은 조립이 둘 이상일 때 두 벌의 같은 부분을 나란히) · 뒤번호(합치는 번호를 뒤 번호/완성 모습과 대조) · 6방향(위·아래·앞·뒤·좌·우를 크게 본 것)
#       책크롭 = 원본 PDF 300dpi 확대 크롭(SKILL.md ★ 절 5번), 화면크롭 = 책과 같은 시점에서 가까이 찍은 3D 화면. 두 그림을 나란히 붙여 refs/<이름>/obs/NN_k.png 로 저장하고 index.json 에 idx 10+ 로 적는다(DB 에 올린다).
#       판정이 "다르다" 이면 기록은 남지만 check 가 막는다 — 방향·대칭을 다시 정해 고친 뒤 다시 add 한다(같은 지점·종류는 덮어쓴다).
#   python observe.py check <이름> <번호>    → 빠진 것을 보여 준다. record_check.py 가 이것을 통과해야 비교 증거를 기록한다.
#   필요한 것: 결합 ≥ 2곳 · 6방향 ≥ 1장 · (같은 조립이 둘 이상이거나 앞 번호 부품을 옮기는 번호면) 그룹비교 ≥ 1 · (앞 번호 부품을 옮기는 번호면) 뒤번호 ≥ 1 · 모든 판정 "같다".
import sys, os, json, time
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
KINDS = ("결합", "그룹비교", "뒤번호", "6방향")

def _load(name):
    p = os.path.join(HERE, name + "_obs.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

def _imread(path):
    a = np.fromfile(path, np.uint8); im = cv2.imdecode(a, cv2.IMREAD_COLOR)
    if im is None: sys.exit("❌ 그림을 못 읽는다: " + path)
    return im

def _need(name, step):
    """이 번호가 요구하는 관찰 종류와 이유"""
    need = {"결합": 2, "6방향": 1}
    try:
        asm = json.load(open(os.path.join(HERE, name + "_asm.json"), encoding="utf-8"))["steps"][step - 1]
    except Exception:
        return need
    parts = asm.get("parts") or []
    names = [(p.get("n") or p.get("name") or "") for p in parts if isinstance(p, dict)]
    mm = asm.get("moveMade") or {}
    groups = {v.get("moveGroup") for v in mm.values() if isinstance(v, dict) and v.get("moveGroup")}
    if len(groups) >= 2 or any(names.count(n) >= 2 for n in set(names) if n in ("35프레임", "39프레임", "515프레임", "315프레임", "3단블록", "2단블록", "DC모터", "리벳") and names.count(n) >= 4):
        need["그룹비교"] = 1
    if mm: need["뒤번호"] = 1
    return need

def check(name, step):
    ob = _load(name).get(str(step), [])
    need = _need(name, step); miss = []
    for k, n in need.items():
        have = [o for o in ob if o["kind"] == k]
        if len(have) < n: miss.append("%s 관찰 %d곳 필요(지금 %d곳)" % (k, n, len(have)))
    for o in ob:
        if o["verdict"] != "같다": miss.append("판정 '다르다' — %s %s: %s" % (o["kind"], o["point"], o["note"]))
    return miss

def add(name, step, kind, point, bookp, screenp, verdict, note):
    if kind not in KINDS: sys.exit("❌ 종류는 %s 중 하나" % "·".join(KINDS))
    if verdict not in ("같다", "다르다"): sys.exit("❌ 판정은 같다/다르다")
    if len(note.strip()) < 20: sys.exit("❌ 한 줄은 20자 이상 — 책과 화면에서 무엇을 어떻게 비교했는지(어느 면·리벳·돌기가 어느 쪽인지)를 쓴다")
    b = _imread(bookp); s = _imread(screenp); h = 520
    b = cv2.resize(b, (int(b.shape[1] * h / b.shape[0]), h)); s = cv2.resize(s, (int(s.shape[1] * h / s.shape[0]), h))
    for im, t in ((b, "책"), (s, "화면")): cv2.putText(im, t, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
    side = np.full((h, b.shape[1] + s.shape[1] + 8, 3), 255, np.uint8); side[:, :b.shape[1]] = b; side[:, b.shape[1] + 8:] = s
    data = _load(name); ob = [o for o in data.get(str(step), []) if not (o["kind"] == kind and o["point"] == point)]
    k = len(ob) + 1
    od = os.path.join(HERE, "refs", name, "obs"); os.makedirs(od, exist_ok=True)
    out = os.path.join(od, "%02d_%d.png" % (step, k)); cv2.imencode(".png", side)[1].tofile(out)
    ob.append({"kind": kind, "point": point, "verdict": verdict, "note": note.strip(), "img": "obs/%02d_%d.png" % (step, k), "time": time.strftime("%Y-%m-%d %H:%M:%S")})
    data[str(step)] = ob; json.dump(data, open(os.path.join(HERE, name + "_obs.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ip = os.path.join(HERE, "refs", name, "index.json"); idx = json.load(open(ip, encoding="utf-8"))
    idx = [r for r in idx if not (r["step"] == step and r["idx"] == 10 + k)]
    idx.append({"step": step, "idx": 10 + k, "file": "obs/%02d_%d.png" % (step, k), "note": "관찰(%s) %s — 왼쪽 책 · 오른쪽 화면 — 판정: %s. %s" % (kind, point, verdict, note.strip())})
    idx.sort(key=lambda r: (r["step"], r["idx"])); json.dump(idx, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("✅ 관찰 기록: %s [%s] %s → %s (%s)" % (step, kind, point, verdict, out)); print("   DB 에 올린다: refs/%s/obs/%02d_%d.png (index idx %d)" % (name, step, k, 10 + k))

def main():
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "check":
        miss = check(a[1], int(a[2]))
        if miss: print("❌ 관찰 증거가 모자란다:"); [print("   -", m) for m in miss]; sys.exit(1)
        print("✅ 관찰 증거 충분(%s번)" % a[2]); return
    if len(a) == 9 and a[0] == "add": add(a[1], int(a[2]), a[3], a[4], a[5], a[6], a[7], a[8]); return
    sys.exit(__doc__)

if __name__ == "__main__": main()
