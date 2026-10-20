# 번호를 끝낼 때 "6방향 확인"과 "다음 번호 같은 부분 비교"를 했는지 기록한다 (사용자 지시 2026-10-20: 앞으로 조립도를 하면서 계속 조사 — 완료 뒤 앞·뒤·좌·우·위·아래에서 보기와 다음 단계에서 같은 부분 비교는 꼭 한다)
#   python track.py <이름> <번호> --views 앞,뒤,좌,우,위,아래 --next "54번 책: 메인보드·LED 위치" [--note "..."]
#   python track.py --report            → 조립도별 6방향·다음 번호 비교 기록률 (feature_score.py 가 같이 보여 준다)
# 기록 파일: usage_log.json  {"<이름>": {"<번호>": {"views": [...], "next": "...", "note": "...", "at": "날짜"}}}
import sys, os, json, datetime
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__)); F = os.path.join(HERE, "usage_log.json")
SIX = ["앞", "뒤", "좌", "우", "위", "아래"]
def load(): return json.load(open(F, encoding="utf-8")) if os.path.exists(F) else {}
def main():
    a = sys.argv[1:]
    if not a: sys.exit(__doc__)
    d = load()
    if a[0] == "--report":
        for nm, v in sorted(d.items()):
            full = sum(1 for e in v.values() if all(s in e.get("views", []) for s in SIX)); nx = sum(1 for e in v.values() if e.get("next"))
            print("%s: 기록 %d번 — 6방향 모두 %d번, 다음 번호 비교 %d번" % (nm, len(v), full, nx))
        return
    name, n = a[0], str(int(a[1])); opt = {}; i = 2
    while i < len(a) - 1 and a[i].startswith("--"): opt[a[i][2:]] = a[i + 1]; i += 2
    e = d.setdefault(name, {}).setdefault(n, {})
    if "views" in opt: e["views"] = sorted(set(e.get("views", [])) | set(x.strip() for x in opt["views"].split(",") if x.strip()), key=lambda s: SIX.index(s) if s in SIX else 9)
    if "next" in opt: e["next"] = opt["next"]
    if "note" in opt: e["note"] = opt["note"]
    e["at"] = datetime.date.today().isoformat()
    missing = [s for s in SIX if s not in e.get("views", [])]
    json.dump(d, open(F, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("%s %s번 기록: 본 방향 %s%s / 다음 번호 비교 %s" % (name, n, ",".join(e.get("views", [])) or "없음", (" — 빠진 방향 " + ",".join(missing)) if missing else " (6방향 완료)", e.get("next") or "아직 안 함 ⚠"))
main()
