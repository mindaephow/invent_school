# 바이킹 번호 하나를 끝낼 때 반복되는 일을 묶은 도구(2026-10-20): 읽기 표 쓰기·번호 대조 그림(NN_6)·DB 올릴 파일 복사
#   python vk_tools.py read N 읽기표.json      — viking_read.json 의 N번 칸을 파일 내용으로 덮어쓴다
#   python vk_tools.py cmp N 링.json           — 책 링 ↔ 모델 구멍 번호 대조 그림 refs/viking/NN_6.jpg 를 만들고 index.json 에 적는다
#       링.json = {"title": "...", "note": "...", "rings": [["라벨", x, y, "설명"], ...]}
#   python vk_tools.py stage N                 — public/_refs_tmp/viking 에 그 번호 그림과 index.json 을 복사한다(올린 뒤 지운다)
import sys, os, json, shutil
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); R = os.path.join(HERE, "refs", "viking")
def jload(p): return json.load(open(p, encoding="utf-8"))
def jdump(o, p, **k): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, **k)
def cmd_read(N, f):
    p = os.path.join(HERE, "viking_read.json"); d = jload(p); d.setdefault(str(N), {}).update(jload(f)); jdump(d, p, indent=1); print("읽기 표", N, "갱신")
def cmd_cmp(N, f):
    a = jload(f); im = Image.open(os.path.join(R, "%02d.jpg" % N)).convert("RGB"); rings = a["rings"]
    ft = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 21); ft2 = ImageFont.truetype(r"C:\Windows\Fonts\malgunbd.ttf", 24)
    W, H = im.size; out = Image.new("RGB", (W, H + 40 + len(rings) * 30 + 20), "white"); out.paste(im, (0, 0)); d = ImageDraw.Draw(out)
    for nm, x, y, t in rings:
        d.ellipse([x - 22, y - 22, x + 22, y + 22], outline=(220, 40, 40), width=3); d.text((x, y - 28), nm, fill=(0, 70, 200), font=ft2, anchor="ms", stroke_width=3, stroke_fill=(255, 255, 255))
    d.text((14, 8), a["title"], fill=(0, 70, 200), font=ft, anchor="la", stroke_width=3, stroke_fill=(255, 255, 255))
    for i, (nm, x, y, t) in enumerate(rings): d.text((16, H + 14 + i * 30), "%s   %s" % (nm, t), fill=(30, 30, 30), font=ft, anchor="la")
    out.save(os.path.join(R, "%02d_6.jpg" % N), quality=90)
    ip = os.path.join(R, "index.json"); ix = [r for r in jload(ip) if not (r["step"] == N and r["idx"] == 6)]
    ix.append({"step": N, "idx": 6, "file": "%02d_6.jpg" % N, "note": a["note"]}); ix.sort(key=lambda r: (r["step"], r["idx"])); jdump(ix, ip, indent=1); print("대조 그림", N)
def cmd_stage(N):
    dst = os.path.join(HERE, "..", "..", "public", "_refs_tmp", "viking"); shutil.rmtree(dst, ignore_errors=True); os.makedirs(dst)
    shutil.copy(os.path.join(R, "index.json"), dst)
    for fn in sorted(os.listdir(R)):
        if fn.startswith("%02d" % N) and fn.endswith(".jpg"): shutil.copy(os.path.join(R, fn), dst); print("복사", fn)
if __name__ == "__main__":
    c = sys.argv[1]; N = int(sys.argv[2])
    if c == "read": cmd_read(N, sys.argv[3])
    elif c == "cmp": cmd_cmp(N, sys.argv[3])
    elif c == "stage": cmd_stage(N)
