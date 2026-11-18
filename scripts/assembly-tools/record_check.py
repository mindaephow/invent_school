# 번호 하나의 "화면 ↔ 책 그림 나란히 비교"를 했다는 증거를 남긴다(관리자 지시 2026-10-11).
#   python record_check.py <이름> <번호> <화면캡처.png> "<비교 결과 한 줄 — 센 개수·맞은 곳·다른 곳을 구체적으로>"
# 하는 일: 화면 캡처와 책 그림(refs/<이름>/NN.jpg)을 나란히 붙인 refs/<이름>/cmp/NN.jpg 를 만들고, 그 번호의 지금 내용 지문·비교 결과·시각을 <이름>_evidence.json 에 적는다.
# build.py 의 번호별 점검은 이 증거(지문이 지금 내용과 같은 것)가 있어야 그 번호의 눈으로 하는 확인 3개(화면 확대·칸 수 대조·카메라 대조)를 통과시킨다.
# 번호 내용이 바뀌면 지문이 달라져 증거가 무효가 되므로 다시 비교해야 한다. 사용자는 나중에 cmp 이미지를 열어 검토한다.
import asmpath  # 조립도 파일 자리(큐보/조립도/<권>/<이름>/) 연결
import sys, os, json, time
try:
    from PIL import Image
except ImportError:   # Pillow 가 없는 PC(2026-10-13): OpenCV 로 같은 동작(캡처 크기 확인·책 그림과 나란히 붙이기)을 한다 — 검사 기준은 그대로
    import cv2, numpy as np
    class _Im:
        def __init__(self, a): self.a = a; self.height, self.width = a.shape[:2]; self.size = (self.width, self.height)
        def convert(self, _): return self
        def resize(self, wh): return _Im(cv2.resize(self.a, tuple(int(v) for v in wh), interpolation=cv2.INTER_AREA))
        def paste(self, other, xy): x, y = xy; self.a[y:y + other.height, x:x + other.width] = other.a
        def save(self, path): cv2.imwrite(path, self.a)
    class Image:
        @staticmethod
        def open(path): return _Im(cv2.imdecode(np.fromfile(path, np.uint8), cv2.IMREAD_COLOR))
        @staticmethod
        def new(mode, size, color): return _Im(np.full((size[1], size[0], 3), 255, np.uint8))
sys.stdout.reconfigure(encoding="utf-8")
import stepfp

def resign(argv):
    """python record_check.py --재서명 <이름> <번호> [이전 _asm.json] [--검사만]
    코드·플래그·설명만 바뀌고 그 번호 화면의 조립(부품 위치·회전·안내점·띄움)이 그대로일 때, 화면을 다시 찍지 않고 증거 지문만 새로 서명한다.
    비교 기준 = 증거에 저장된 조립 값(geo). 옛 증거(geo 없음)는 증거를 남겼던 때의 _asm.json 을 준다(생략하면 git HEAD) — 그 파일의 지문이 증거와 같아야 기준으로 받는다.
    허용 오차(stepfp.GEO_TOL_MM·GEO_TOL_DEG)를 넘거나 부품 수·안내점 수가 다르면 서명하지 않는다 — 그때는 화면과 책을 다시 비교해 증거를 새로 남긴다."""
    dry = "--검사만" in argv; argv = [a for a in argv if a != "--검사만"]
    if len(argv) not in (2, 3) or not argv[1].isdigit(): sys.exit(resign.__doc__)
    name, step = argv[0], int(argv[1]); here = os.path.dirname(os.path.abspath(__file__))
    asm = json.load(open(os.path.join(here, name + "_asm.json"), encoding="utf-8"))["steps"]
    ef = os.path.join(here, name + "_evidence.json"); evd = json.load(open(ef, encoding="utf-8")) if os.path.exists(ef) else {}
    ev = evd.get(str(step))
    if not ev or step < 1 or step > len(asm): sys.exit("❌ %d번에는 비교 증거가 없다 — 재서명이 아니라 증거를 새로 남긴다" % step)
    st = asm[step - 1]
    if stepfp.same(ev, st, asm): print("✅ %d번 증거는 지금 내용과 이미 같다 — 재서명할 것이 없다" % step); return
    if ev.get("geo"): base, src = ev["geo"], "증거에 저장된 조립 값"
    else:
        if len(argv) == 3: old = json.load(open(argv[2], encoding="utf-8")); src = "이전 파일 " + os.path.basename(argv[2])
        else:
            import subprocess
            rel = os.path.relpath(str(asmpath.resolve(name + "_asm.json")), here).replace(os.sep, "/")
            r = subprocess.run(["git", "-C", here, "show", "HEAD:./" + rel], capture_output=True)
            if r.returncode != 0: sys.exit("❌ 이전 _asm.json 을 git HEAD 에서 못 읽었다 — 증거를 남겼던 때의 _asm.json 경로를 준다")
            old = json.loads(r.stdout.decode("utf-8")); src = "git HEAD 의 _asm.json"
        old = old["steps"] if isinstance(old, dict) else old
        if step > len(old) or not stepfp.same(ev, old[step - 1], old): sys.exit("❌ %s 의 %d번은 증거를 남겼던 내용이 아니다(지문이 증거와 다르다) — 기준으로 쓸 수 없다. 증거를 남겼던 때의 파일을 주거나 증거를 새로 남긴다" % (src, step))
        base = stepfp.geo(old[step - 1], stepfp.anchor(old), step, old)
    now = stepfp.geo(st, stepfp.anchor(asm), step, asm)
    ok, mp, mr, bad = stepfp.geo_diff(base, now)
    print("%d번 조립 비교(기준: %s) — 항목 %d개, 가장 큰 위치 차 %.3f mm · 회전 차 %.3f° (허용 %.1f mm · %.1f°)" % (step, src, len(now), mp, mr, stepfp.GEO_TOL_MM, stepfp.GEO_TOL_DEG))
    if not ok:
        for b in bad[:20]: print("   ✗", b)
        sys.exit("❌ 조립이 달라졌다(%d곳) — 재서명하지 않는다. 화면과 책을 다시 비교해 증거를 새로 남긴다" % len(bad))
    if dry: print("✅ 조립이 같다 — --검사만 이라 서명하지 않았다"); return
    log = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "기준": src, "이전지문": ev.get("fp"), "항목": len(now), "위치차_mm": mp, "회전차_deg": mr, "허용": [stepfp.GEO_TOL_MM, stepfp.GEO_TOL_DEG]}
    ev["fp"] = stepfp.fp(st); ev["shape"] = stepfp.shape_fp(st, stepfp.anchor(asm), step, asm); ev["geo"] = base   # 기준 값은 처음 눈으로 확인한 때의 것을 그대로 둔다 — 재서명을 거듭해도 오차가 쌓이지 않는다
    ev.setdefault("재서명", []).append(log)
    json.dump(evd, open(ef, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("✅ %d번 증거 재서명(조립 동일 확인) — 지문 %s → %s, 비교 결과는 증거의 '재서명' 에 남겼다" % (step, log["이전지문"], ev["fp"]))

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--재서명": return resign(sys.argv[2:])
    # --감독(사용자 승인 2026-11-18 "감독관이 봤을 때 괜찮으면 증거 같은 것 없이 넘어가자"): 감독 모드의 감독이 책과 화면을 직접 나란히 보고 판정한 것을 증거로 남긴다.
    #   관찰 기록(observe) 요구만 빼고 나머지(필수 산출물·45분 안 캡처·숫자 든 비교·비교 그림·지문 — 조립이 바뀌면 무효)는 같다. 감독(supervise.py approve)만 쓴다(큐보/규칙/감독.md).
    by_sup = len(sys.argv) > 1 and sys.argv[1] == "--감독"
    if by_sup: sys.argv = sys.argv[:1] + sys.argv[2:]
    if len(sys.argv) != 5: sys.exit(__doc__)
    name, step, shot, note = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4].strip()
    here = os.path.dirname(os.path.abspath(__file__))
    if not by_sup and (step >= 16 or os.environ.get("OBS_REQUIRED") == "1"):   # 관찰 증거(observe.py) — 결합 지점·그룹·뒤 번호를 눈으로 본 기록이 없으면 비교 증거를 안 받는다(2026-10-27 배틀바이크 17번). 기존 번호(1~15)는 그대로.
        import observe
        _miss = observe.check(name, step)
        if _miss: sys.exit("❌ 관찰 증거가 모자라 비교 증거를 기록하지 않는다 — `python observe.py add …` 로 책 확대와 화면을 나란히 본 기록을 먼저 남긴다(큐보 부품결합규칙.md H 절):\n   - " + "\n   - ".join(_miss))
    try:   # 필수 산출물(격자·홀라인 그림·카메라·읽기 표 …)이 빠졌으면 비교 증거를 받지 않는다 — 정의는 rulecheck.py 한 곳(D14). 그림DB 는 증거 뒤에 올리는 관찰 그림 때문에 제외한다.
        import rulecheck as _rcr, asmpath as _ap
        if _rcr.load(_ap.ap(name, "_rules.json"), {}).get("holeline_img"):
            _pm = [(t_, w_) for t_, w_ in _rcr.missing_artifacts(name, step) if not t_.startswith("그림DB")]
            if _pm: sys.exit(chr(10).join(["❌ 필수 산출물이 빠져 비교 증거를 기록하지 않는다(D14) — 먼저 만든다:"] + ["   - %s: %s" % (t_, w_) for t_, w_ in _pm]))
    except SystemExit: raise
    except Exception as _e_: print("필수 산출물 점검을 못 했다:", str(_e_)[:100])
    if not os.path.isfile(shot): sys.exit("❌ 화면 캡처 파일이 없다: " + shot)
    if time.time() - os.path.getmtime(shot) > 45 * 60: sys.exit("❌ 화면 캡처가 45분보다 오래됐다 — 지금 화면을 새로 찍어 쓴다")
    im = Image.open(shot).convert("RGB")
    if im.width < 500 or im.height < 350: sys.exit("❌ 화면 캡처가 너무 작다(%dx%d) — 조립 보기 화면 전체를 찍는다" % im.size)
    if len(note) < 30 or not any(ch.isdigit() for ch in note): sys.exit("❌ 비교 결과는 30자 이상이고 센 개수(숫자)가 들어가야 한다 — 무엇을 몇 개 세어 책과 맞았고 어디가 달랐는지 적는다")
    book = os.path.join(here, "refs", name, "%02d.jpg" % step)
    if not os.path.isfile(book): sys.exit("❌ 책 그림이 없다: " + book)
    asm = json.load(open(os.path.join(here, name + "_asm.json"), encoding="utf-8"))["steps"]
    if step < 1 or step > len(asm) or not (asm[step - 1].get("parts") or asm[step - 1].get("moveMade") or asm[step - 1].get("madeNoPart")): sys.exit("❌ 부품이 있거나 앞 번호 부품을 옮기는(합치는) 번호가 아니다(부품 없는 번호는 kw madeNoPart 로 표시 — 어보이더 28·30번)")
    fp = stepfp.fp(asm[step - 1])
    b = Image.open(book).convert("RGB"); h = 760
    a = b.resize((int(b.width * h / b.height), h)); c = im.resize((int(im.width * h / im.height), h))
    side = Image.new("RGB", (a.width + c.width + 6, h), "white"); side.paste(a, (0, 0)); side.paste(c, (a.width + 6, 0))
    out_dir = os.path.join(here, "refs", name, "cmp"); os.makedirs(out_dir, exist_ok=True)
    from PIL import ImageFile as _IF; _IF.MAXBLOCK = 1 << 26   # optimize=True 가 복잡한 그림에서 "broken data stream" 으로 실패하는 것을 막는다
    out = os.path.join(out_dir, "%02d.jpg" % step); side.save(out, "JPEG", quality=90, subsampling=0, optimize=True)   # 비교 그림도 JPEG(용량, 사용자 지시 2026-11-14)
    ef = os.path.join(here, name + "_evidence.json")
    ev = json.load(open(ef, encoding="utf-8")) if os.path.exists(ef) else {}
    ev[str(step)] = {"fp": fp, "shape": stepfp.shape_fp(asm[step - 1], stepfp.anchor(asm), step, asm), "note": note, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "cmp": "refs/%s/cmp/%02d.jpg" % (name, step), "geo": stepfp.geo(asm[step - 1], stepfp.anchor(asm), step, asm), **({"by": "감독"} if by_sup else {})}   # by: 감독 판정 증거(감독.md) · geo: 이 번호 화면의 조립 값 — 나중에 코드만 바뀌면 --재서명 이 이 값과 숫자로 비교한다
    json.dump(ev, open(ef, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("✅ %d번 비교 증거 기록: %s" % (step, out)); print("   지문", fp, "| 결과:", note)
    # 왼쪽 점검 칩 자동 연동(사용자 지시 2026-11-10 — "번호마다 이미지 작업을 하고도 칩이 한 번도 자동으로 안 채워졌다"): 증거를 남기는 순간 verify_step 을 돌려 칩 기록(<이름>_verify.json·DB)을 채운다
    import subprocess
    _v = subprocess.run([sys.executable, os.path.join(here, "verify_step.py"), name, str(step)], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    # 책 링 ↔ 칸·줄 대조(cellmap.py, 사용자 지시 2026-11-10): 격자는 카메라만 풀려고 만드는 것이 아니라 링이 몇 칸·몇 줄 구멍인지 정하려는 것이다 — 증거를 남길 때마다 같이 만들어 읽기 표 '링'·모델 결합 구멍과 맞춰 본다
    _c = subprocess.run([sys.executable, os.path.join(here, "cellmap.py"), name, str(step)], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    print("── 책 링 ↔ 칸·줄(cellmap 자동) — 읽기 표 '링'과 모델 결합 구멍이 이 칸·줄과 같은지 확인 ──"); print("\n".join(l for l in (_c.stdout or _c.stderr).splitlines() if l.startswith("  링") or l.startswith("그림") or l.startswith("❌")))
    print("── 왼쪽 점검 칩(verify_step 자동) ──"); print("\n".join(l for l in _v.stdout.splitlines() if l.startswith("  ") or l.startswith("검증 결과")))
    print("   → 화면을 새로 불러와 칩(왼쪽)·하단 감시 칩이 초록인지 눈으로 읽은 뒤 다음 번호로 간다(규칙 가-0 다-3). ⚠·❌ 가 있으면 그 번호는 끝난 것이 아니다.")

if __name__ == "__main__": main()
