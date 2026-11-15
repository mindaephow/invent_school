# 끝까지 가 지킴이의 "사용자가 멈추라고 했나" 판정 시험(finish_guard.user_said_stop) — 훅을 실제로 돌리지 않고 함수만 본다.   python test_finish_guard.py
import json, os, tempfile
NL = chr(10)
src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "finish_guard.py"), encoding="utf-8").read().rsplit(NL + "main()", 1)[0]   # 맨 끝 main() 호출(훅 실행)은 빼고 불러온다
G = {"__file__": os.path.join(os.path.dirname(os.path.abspath(__file__)), "finish_guard.py")}; exec(compile(src, "finish_guard.py", "exec"), G)
U = lambda t: {"type": "user", "message": {"role": "user", "content": t}}
TR = {"type": "user", "message": {"role": "user", "content": [{"type": "tool_result", "content": "중단"}]}}
HOOK = U("Stop hook feedback:" + NL + "❌ kidknight 규칙 점검에 ❌ 3번이 남았다 — 멈추라고(중단·그만) 했으면 …")
A = {"type": "assistant", "message": {"role": "assistant", "content": [{"type": "text", "text": "그만"}]}}
def said(*rows):
    f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8"); f.write(NL.join(json.dumps(r, ensure_ascii=False) for r in rows)); f.close()
    try: return G["user_said_stop"](f.name)
    finally: os.remove(f.name)
assert said(U("9번까지 진행해"), A, TR, U("멈춰")) == "멈춰"
assert said(U("멈춰"), TR, HOOK, A) == "멈춰"                      # 멈추라고 한 뒤의 도구 결과·훅 안내는 사용자 말이 아니다
assert said(U("잠깐만, 그만하고 기다려")) is not None and said(U("stop")) == "stop"
assert said(U("멈춰"), U("계속해")) is None                        # 마지막 말이 기준
assert said(U("멈추지 말고 끝까지 해")) is None and said(U("왜 멈췄어?")) is None and said(U("중단 없이 진행")) is None
assert said(U("9번 카메라가 이상해 보이는데 그 부분은 그만 보고 다음 번호로 넘어가서 10번부터 12번까지 끝까지 진행해 줘")) is None   # 긴 지시 속 낱말은 멈춤이 아니다
assert said(A, TR) is None and G["user_said_stop"]("없는 파일.jsonl") is None
print("OK 사용자 멈춤 지시 판정")
