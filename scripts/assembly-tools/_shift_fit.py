# holefit(DoG) 점이 구멍 한가운데가 아니라 구멍의 흰 틈(아래쪽)에 찍혀 링 중심보다 아래·오른쪽에 있을 때, 링 중심과 맞는 평행이동(dx dy)으로 fits 의 점을 옮긴다(⚠ 링 기준 보정, 이름에 기록)
#   python _shift_fit.py <이름> <번호> <라벨> <dx> <dy>
import json, sys
sys.stdout.reconfigure(encoding="utf-8")
name, N, lab, dx, dy = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4]), float(sys.argv[5])
p = "refs/%s/fits/%02d_%s.json" % (name, N, lab); f = json.load(open(p, encoding="utf-8"))
f["pts"] = [[c, r, round(x + dx, 1), round(y + dy, 1)] for c, r, x, y in f["pts"]]
f["name"] = f.get("name", "") + " · 점을 링 중심에 맞춰 (%+g, %+g)px 평행이동(holefit 점이 구멍 흰 틈에 찍혀 중심보다 아래라서, ⚠ 링 기준 보정)" % (dx, dy)
json.dump(f, open(p, "w", encoding="utf-8"), ensure_ascii=False); print("옮김", dx, dy, len(f["pts"]))
