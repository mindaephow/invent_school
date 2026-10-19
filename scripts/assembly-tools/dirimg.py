# 완성품 방향선 그림 만들기(00_개선규칙 9번, 02_이미지_자르기 3-2 — 2026-10-15): 완성 사진(00.jpg)에 6×6 모눈(A~F·1~6)과 앞·뒤·위·왼쪽·오른쪽 화살표를 얹어 refs/<이름>/00_1.jpg 로 저장하고 index.json 에 넣는다.
#   python dirimg.py <이름> --원점 x y --앞 x y --뒤 x y --위 x y --왼쪽 x y --오른쪽 x y [--메모 "추가 안내"]
#   좌표는 모두 원본 00.jpg 의 픽셀(화살표 끝점). 방향은 눈으로 읽으므로 사용자에게 보여 주고 확인받는다(앞·뒤·위는 완성 3D 화면의 기준 부품 위치로도 확인).
#   읽는 법: 앞 = 눈·센서·머리가 향한 쪽 / 위 = 몸이 바닥에서 올라간 쪽 / 왼쪽 = 로봇이 앞을 보고 섰을 때 왼손 쪽(카메라를 마주 보는 로봇이면 화면 오른쪽).
#   축 표시: 앞 +Z · 뒤 −Z · 위 +Y · 왼쪽 +X · 오른쪽 −X (완성품 기준).
import sys, os, json, math
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = [r"C:\Windows\Fonts\malgunbd.ttf", r"C:\Windows\Fonts\Hancom Gothic Bold.ttf", r"C:\Windows\Fonts\HANBatangB.ttf", os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\Fonts\Hancom Gothic Bold.ttf")]
def font(size):
    for p in FONTS:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, size)
            except Exception: pass
    sys.exit("❌ 한글 글꼴을 찾지 못했다 — dirimg.py 의 FONTS 에 글꼴 경로를 추가한다")
# (이름, 축 표시, 색, 점선 여부)
KINDS = {"앞": ("앞", "+Z", (225, 45, 45), False), "뒤": ("뒤", "-Z", (40, 100, 235), False), "위": ("위", "+Y", (30, 155, 70), False),
         "왼쪽": ("왼쪽", "+X", (235, 135, 0), False), "오른쪽": ("오른쪽", "-X", (135, 70, 225), True)}   # 글꼴에 진짜 마이너스(−)가 없어 하이픈(-)을 쓴다
def parse(argv):
    a = {"이름": argv[1]}; i = 2
    while i < len(argv):
        k = argv[i].lstrip("-")
        if k == "메모": a["메모"] = argv[i + 1]; i += 2
        elif k in ("원점", "앞", "뒤", "위", "왼쪽", "오른쪽"): a[k] = (float(argv[i + 1]), float(argv[i + 2])); i += 3
        else: sys.exit("❌ 알 수 없는 옵션: " + argv[i])
    miss = [k for k in ("원점", "앞", "뒤", "위", "왼쪽", "오른쪽") if k not in a]
    if miss: sys.exit("❌ 빠진 옵션: " + ", ".join("--" + m for m in miss) + "\n" + __doc__)
    return a
def arrow(d, p0, p1, color, w, dashed):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]; L = math.hypot(dx, dy) or 1.0; ux, uy = dx / L, dy / L
    head = 34; bx, by = p1[0] - ux * head, p1[1] - uy * head
    if dashed:
        n = int((L - head) // 26)
        for s in range(0, n, 2): d.line([(p0[0] + ux * s * 26, p0[1] + uy * s * 26), (p0[0] + ux * min(s * 26 + 26, L - head), p0[1] + uy * min(s * 26 + 26, L - head))], fill=color, width=w)
    else: d.line([p0, (bx, by)], fill=color, width=w)
    px, py = -uy, ux
    d.polygon([p1, (bx + px * 16, by + py * 16), (bx - px * 16, by - py * 16)], fill=color)
def main():
    a = parse(sys.argv); name = a["이름"]; D = os.path.join(HERE, "refs", name)
    src = os.path.join(D, "00.jpg")
    if not os.path.exists(src): sys.exit("❌ 완성 사진이 없다: " + src)
    im = Image.open(src).convert("RGB"); W, H = im.size
    ov = Image.new("RGBA", im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    fs = font(max(11, W // 70))
    for r in range(6):   # 6×6 모눈(열 A~F, 행 1~6): 눈금 그림에서 위치를 말하는 기준
        for c in range(6):
            x0, y0 = c * W / 6, r * H / 6
            d.rectangle([x0, y0, x0 + W / 6, y0 + H / 6], outline=(60, 120, 235, 150), width=1)
            d.text((x0 + W / 12, y0 + H / 12), "%s%d" % ("ABCDEF"[c], r + 1), fill=(60, 120, 235, 200), font=fs, anchor="mm")
    im = Image.alpha_composite(im.convert("RGBA"), ov); d = ImageDraw.Draw(im)
    O = a["원점"]; lf = font(max(26, W // 22)); sf = font(max(22, W // 26))
    for key, (nm, ax, col, dash) in KINDS.items():
        E = a[key]; arrow(d, O, E, col, max(6, W // 130), dash)
        dx, dy = E[0] - O[0], E[1] - O[1]; L = math.hypot(dx, dy) or 1.0; tx, ty = E[0] + dx / L * 46, E[1] + dy / L * 46
        tx = min(max(tx, 60), W - 60); ty = min(max(ty, 50), H - 100)
        d.text((tx, ty - 14), nm, fill=col, font=lf, anchor="mm", stroke_width=4, stroke_fill=(255, 255, 255))
        d.text((tx, ty + 24), ax, fill=col, font=lf, anchor="mm", stroke_width=4, stroke_fill=(255, 255, 255))
    note = "완성품 기준:\n앞 = +Z · 위 = +Y\n왼쪽 = +X" + (("\n" + a["메모"]) if a.get("메모") else "")
    d.multiline_text((14, H - 14), note, fill=(20, 20, 20), font=sf, anchor="ld", align="left", stroke_width=3, stroke_fill=(255, 255, 255))   # 왼쪽 아래(보통 빈 곳)
    out = os.path.join(D, "00_1.jpg"); im.convert("RGB").save(out, quality=92)
    ip = os.path.join(D, "index.json"); idx = json.load(open(ip, encoding="utf-8"))
    row = {"step": 0, "idx": 1, "file": "00_1.jpg", "note": "완성품 방향선 — 완성 사진과 한 세트. 앞 +Z · 뒤 -Z · 위 +Y · 왼쪽 +X · 오른쪽 -X (방향은 눈으로 읽음, 사용자 확인 필요)"}
    idx = [r for r in idx if not (int(r.get("step", -1)) == 0 and int(r.get("idx", -1)) == 1)] + [row]
    idx.sort(key=lambda r: (int(r["step"]), int(r["idx"])))
    json.dump(idx, open(ip, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("저장:", out, "| index.json 에 step 0 idx 1 추가"); print("→ 사용자에게 보여 주고 확인받는다. 그다음 02 3-2 ④ 로 DB 에 올린다(__ivsRefsUpload).")
main()
