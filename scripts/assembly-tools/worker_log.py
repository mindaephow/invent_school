# 작업자 지시문 기록 — 안전장치("safeguards flagged this message (reasoning_extraction)")로 죽는 지시문을 성공한 것과 비교한다(사용자 지시 2026-11-25).
#   python worker_log.py add --agent cubo-worker --model sonnet --결과 ok|safeguard|other --요청id <id> --지시문파일 <경로> [--메모 "..."]
#   python worker_log.py show        표(번호·모델·글자수·결과·요청id) + 성공/실패 지시문의 길이·공통 문구 차이
# 기록 위치: 큐보/규칙/worker_log.jsonl (한 줄 = 한 번 부름, 지시문 전문 포함). 손으로 고치지 않는다.
import sys, os, json, time, argparse
sys.stdout.reconfigure(encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "큐보", "규칙", "worker_log.jsonl")

def load():
    if not os.path.exists(LOG): return []
    return [json.loads(l) for l in open(LOG, encoding="utf-8") if l.strip()]

def add(a):
    text = open(a.지시문파일, encoding="utf-8").read()
    d = {"ts": time.strftime("%Y-%m-%d %H:%M:%S"), "agent": a.agent, "model": a.model, "result": a.결과,
         "request_id": a.요청id or "", "chars": len(text), "lines": text.count("\n") + 1,
         "brief_file": os.path.abspath(a.지시문파일), "memo": a.메모 or "", "brief": text}
    os.makedirs(os.path.dirname(LOG), exist_ok=True)
    with open(LOG, "a", encoding="utf-8") as f: f.write(json.dumps(d, ensure_ascii=False) + "\n")
    print(f"기록 #{len(load())}: {a.agent}/{a.model} {a.결과} {d['chars']}자 {d['lines']}줄")

def phrases(text):   # 비교 단위 = 공백 정리한 줄
    return {" ".join(l.split()) for l in text.splitlines() if len(l.strip()) >= 4}

def show(_):
    rows = load()
    if not rows: print("기록 없음:", LOG); return
    print(f"{'#':>3}  {'시각':19}  {'모델':8} {'글자':>6} {'줄':>4}  {'결과':9} 요청id / 메모")
    for i, r in enumerate(rows, 1):
        print(f"{i:>3}  {r['ts']:19}  {r['model']:8} {r['chars']:>6} {r['lines']:>4}  {r['result']:9} {r['request_id'] or '-'}"
              + (f"  ({r['memo']})" if r['memo'] else ""))
    groups = {k: [r for r in rows if r["result"] == k] for k in ("ok", "safeguard", "other")}
    print("\n[길이] " + " / ".join(f"{k} {len(v)}건 평균 {sum(r['chars'] for r in v)//len(v)}자"
                                    for k, v in groups.items() if v))
    bad, good = groups["safeguard"], groups["ok"] or groups["other"]
    if not bad or not good:
        print("[문구 차이] safeguard 와 비교 대상(ok, 없으면 other)이 둘 다 있어야 비교합니다."); return
    bad_p = set.intersection(*(phrases(r["brief"]) for r in bad))
    good_p = set.union(*(phrases(r["brief"]) for r in good))
    only_bad = sorted(bad_p - good_p, key=len, reverse=True)
    label = "ok" if groups["ok"] else "other"
    print(f"[문구 차이] 모든 safeguard 지시문에 있고 {label} 에는 없는 줄 {len(only_bad)}개 (긴 순, 최대 15):")
    for p in only_bad[:15]: print("   -", p[:110])
    print(f"[공통] 양쪽 모두에 있는 줄 {len(bad_p & good_p)}개")

p = argparse.ArgumentParser(); s = p.add_subparsers(dest="cmd", required=True)
pa = s.add_parser("add")
pa.add_argument("--agent", required=True); pa.add_argument("--model", required=True)
pa.add_argument("--결과", required=True, choices=["ok", "safeguard", "other"])
pa.add_argument("--요청id", default=""); pa.add_argument("--지시문파일", required=True); pa.add_argument("--메모", default="")
s.add_parser("show")
a = p.parse_args()
{"add": add, "show": show}[a.cmd](a)
