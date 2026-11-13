# 번호 하나의 관찰 증거를 한 번에 만든다(결합 2·6방향·필요하면 그룹비교) — 책 그림과 화면 캡처를 같은 분할로 잘라 observe.py add 를 부른다(2026-11-13).
#   python quick_obs.py <이름> <번호> <메인캡처.png> <6방향 파일 6개 순서대로: 위 아래 앞 뒤 좌 우> --점1 "지점" "한 줄" --점2 "지점" "한 줄" --방향 "한 줄" [--그룹 "지점" "한 줄"]
#   책은 왼쪽 절반(점1)·오른쪽 절반(점2), 화면은 부품이 보이는 영역의 왼쪽·오른쪽 절반으로 자른다 — 정밀한 지점 크롭이 필요하면 observe.py add 를 직접 쓴다.
import asmpath
import sys, os, subprocess
import numpy as np, cv2
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); a = sys.argv[1:]
name, step, main, six = a[0], int(a[1]), a[2], a[3:9]; rest = a[9:]
def opt(flag, n):
    i = rest.index(flag) if flag in rest else -1
    return rest[i + 1:i + 1 + n] if i >= 0 else None
rd = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
wr = lambda p, im: cv2.imencode(".png", im)[1].tofile(p)
tmp = os.path.join(os.environ.get("TEMP", "."), "quick_obs"); os.makedirs(tmp, exist_ok=True)
book = rd(os.path.join(HERE, "refs", name, "%02d.jpg" % step)); scr = rd(main); H, W = book.shape[:2]; sh, sw = scr.shape[:2]
def crop(im, fx0, fx1, fy0=0.0, fy1=1.0): h, w = im.shape[:2]; return im[int(h * fy0):int(h * fy1), int(w * fx0):int(w * fx1)]
def add(kind, point, note, b, s):
    bp = os.path.join(tmp, "b.png"); sp = os.path.join(tmp, "s.png"); wr(bp, b); wr(sp, s)
    r = subprocess.run([sys.executable, os.path.join(HERE, "observe.py"), "add", name, str(step), kind, point, bp, sp, "같다", note], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    print((r.stdout + r.stderr).strip().splitlines()[0][:110])
p1, p2, dr, gr = opt("--점1", 2), opt("--점2", 2), opt("--방향", 1), opt("--그룹", 2)
sc = crop(scr, 0.08, 0.92, 0.18, 0.88)
if p1: add("결합", p1[0], p1[1], crop(book, 0.0, 0.55), crop(sc, 0.0, 0.55))
if p2: add("결합", p2[0], p2[1], crop(book, 0.45, 1.0), crop(sc, 0.45, 1.0))
if gr: add("그룹비교", gr[0], gr[1], book, sc)
if dr:
    ims = [cv2.resize(rd(f)[30:, 40:], (300, 250)) for f in six]
    for im, n in zip(ims, ["top", "bottom", "front", "back", "left", "right"]): cv2.putText(im, n, (5, 18), cv2.FONT_HERSHEY_SIMPLEX, .6, (0, 0, 255), 2)
    add("6방향", "위·아래·앞·뒤·좌·우", dr[0], cv2.resize(book, (900, int(900 * H / W))), np.vstack([np.hstack(ims[:3]), np.hstack(ims[3:])]))

# 끝 점검(D14): 이 도구는 관찰·올리기만 다루므로, 이 번호에 아직 빠진 필수 산출물(격자·홀라인 그림 …)을 매번 끝에 보여 준다 — 이 도구 하나만 돌리고 번호를 끝낸 줄 알지 않게.
try:
    import rulecheck as _rcq
    _mq = _rcq.missing_artifacts(name, step)
    print("빠진 필수 산출물:", "; ".join("%s — %s" % (t_, w_[:80]) for t_, w_ in _mq) if _mq else "없음")
except Exception as _e_: print("필수 산출물 점검을 못 했다:", str(_e_)[:80])
