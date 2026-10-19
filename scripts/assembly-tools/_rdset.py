# 읽기 표 한 번호를 채운다: python _rdset.py <번호> <json파일>   (json = {"면":…,"링":…,"부품":…,"대조":…,"방향":…,"부품방향":…,"판단과정":…})
import sys, json
sys.stdout.reconfigure(encoding="utf-8")
f = "autotarget_read.json"; r = json.load(open(f, encoding="utf-8")); r.setdefault(sys.argv[1], {}).update(json.load(open(sys.argv[2], encoding="utf-8")))
json.dump(r, open(f, "w", encoding="utf-8"), ensure_ascii=False, indent=1); print("읽기 표", sys.argv[1], "저장")
