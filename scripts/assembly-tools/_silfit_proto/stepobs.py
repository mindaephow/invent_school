# 번호 하나의 관찰·증거를 한 번에 남긴다(스티어카 11번~): 스크린샷 8장 id + 결합 크롭 상자 + 문구 JSON → observe add ×N → record_check → build → rulecheck → verify_step
#   python _silfit_proto/stepobs.py spec.json
#   spec = {"n":11, "shots":{"zoom":"id","front":..,"back":..,"left":..,"right":..,"top":..,"bottom":..,"step":"id"},
#           "joins":[{"name":"지점","book":[y0,y1,x0,x1],"scr_from":"zoom","scr":[y0,y1,x0,x1],"text":"한 줄"}],
#           "six":"한 줄", "group":{"book":[..],"scr":[..],"scr_from":"step","name":"..","text":".."}|null, "next":{"book_file":"12.jpg","book":[..],"scr_from":"step","scr":[..],"name":"..","text":".."}|null,
#           "compare":"비교 한 줄"}
import sys, os, json, subprocess, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(HERE)
sp = json.load(open(sys.argv[1], encoding="utf-8")); N = sp["n"]
T = "C:/Users/user/.claude/projects/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/tool-results/mcp-Claude_Browser-blob-"
O = "C:/Users/user/AppData/Local/Temp/bbx%d/" % N; os.makedirs(O, exist_ok=True)
im = {k: cv2.imread(T + v + ".jpg") for k, v in sp["shots"].items()}
assert all(v is not None for v in im.values()), [k for k, v in im.items() if v is None]
sc = {k: v[70:555, 225:780] for k, v in im.items()}; book = cv2.imread("refs/steercar/%02d.jpg" % N)
crop = lambda a, b: a[b[0]:b[1], b[2]:b[3]]; w = lambda n, a: cv2.imwrite(O + n, a)
def obs(kind, name, bk, sc_, text):
    cmd = [sys.executable, "observe.py", "add", "steercar", str(N), kind, name, O + bk, O + sc_, "같다", text]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8")); print(r.stdout.strip().splitlines()[-2:] if r.stdout else r.stderr[-300:])
for i, j in enumerate(sp["joins"]):
    w("bj%d.png" % i, crop(book, j["book"])); w("sj%d.png" % i, crop(im[j["scr_from"]], j["scr"])); obs("결합", j["name"], "bj%d.png" % i, "sj%d.png" % i, j["text"])
font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 22); tiles = []
for nm, k in (("위", "top"), ("아래", "bottom"), ("앞(+Z)", "front"), ("뒤(−Z)", "back"), ("왼쪽(+X)", "left"), ("오른쪽(−X)", "right")):
    pil = Image.fromarray(cv2.cvtColor(sc[k], cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil); d.rectangle([0, 0, 150, 30], fill=(255, 255, 255)); d.text((4, 2), nm, font=font, fill=(200, 0, 0)); tiles.append(np.array(pil))
m = np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:])]); w("s6.png", cv2.cvtColor(m, cv2.COLOR_RGB2BGR)); w("b6.png", book); obs("6방향", "위·아래·앞·뒤·좌·우", "b6.png", "s6.png", sp["six"])
g = sp.get("group")
if g:
    w("bg.png", crop(book, g["book"])); w("sg.png", crop(im[g["scr_from"]], g["scr"])); obs("그룹비교", g["name"], "bg.png", "sg.png", g["text"])
nx = sp.get("next")
if nx:
    b2 = cv2.imread("refs/steercar/" + nx["book_file"]); w("bn.png", crop(b2, nx["book"])); w("sn.png", crop(im[nx["scr_from"]], nx["scr"])); obs("뒤번호", nx["name"], "bn.png", "sn.png", nx["text"])
print(subprocess.run([sys.executable, "observe.py", "check", "steercar", str(N)], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8")).stdout.strip().splitlines()[-3:])
shot = T + sp["shots"]["step"] + ".jpg"
run = lambda *a: subprocess.run([sys.executable, *a], capture_output=True, text=True, encoding="utf-8", env=dict(os.environ, PYTHONIOENCODING="utf-8")).stdout
print(run("record_check.py", "steercar", str(N), shot, sp["compare"]).strip()[-120:])
run("build.py", "steercar", "--write")
print([l for l in run("rulecheck.py", "steercar").splitlines() if ("%d번" % N) in l[:5] or "합계" in l])
print("\n".join(run("verify_step.py", "steercar", str(N)).splitlines()[-3:]))
