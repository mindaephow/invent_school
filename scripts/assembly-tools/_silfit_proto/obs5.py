import sys, cv2, numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.stdout.reconfigure(encoding="utf-8")
T = "C:/Users/user/.claude/projects/C--Users-user-Downloads/d23b294b-4abb-4fbf-963d-542f38772228/tool-results/mcp-Claude_Browser-blob-"
B = "C:/Users/user/AppData/Local/Temp/bb/"
rd = lambda p: cv2.imdecode(np.fromfile(p, np.uint8), cv2.IMREAD_COLOR)
wr = lambda p, im: cv2.imencode(".png", im)[1].tofile(p)
book = rd(B + "book5.png")
S = {"zoom": "1793439612545-uf5j4l.jpg", "front": "1793439612546-hosuvn.jpg", "back": "1793439612546-3730ap.jpg", "left": "1793439612546-cl7w5g.jpg",
     "right": "1793439628240-hix05e.jpg", "top": "1793439628241-o41b4m.jpg", "bottom": "1793439628241-89rf99.jpg", "step": "1793439628241-54o9fr.jpg"}
full = {k: rd(T + v) for k, v in S.items()}
sc = {k: v[70:555, 225:780] for k, v in full.items()}
wr(B + "book_p1.png", book[10:500, 380:925]); wr(B + "screen_p1.png", full["zoom"][70:430, 420:780])
wr(B + "book_p2.png", book[140:700, 300:700]); wr(B + "screen_p2.png", full["zoom"][230:555, 230:560])
font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 22)
names = [("위", "top"), ("아래", "bottom"), ("앞(+Z)", "front"), ("뒤(−Z)", "back"), ("왼쪽(+X)", "left"), ("오른쪽(−X)", "right")]
tiles = []
for nm, k in names:
    pil = Image.fromarray(cv2.cvtColor(sc[k], cv2.COLOR_BGR2RGB)); d = ImageDraw.Draw(pil); d.rectangle([0, 0, 150, 30], fill=(255, 255, 255)); d.text((4, 2), nm, font=font, fill=(200, 0, 0)); tiles.append(np.array(pil))
m = np.vstack([np.hstack(tiles[:3]), np.hstack(tiles[3:])]); wr(B + "screen_p3.png", cv2.cvtColor(m, cv2.COLOR_RGB2BGR)); wr(B + "book_p3.png", book)
print("ok")
