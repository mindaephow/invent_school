# 단계 내용 지문(build.py 의 ✓ 단계 보호와 record_check.py 의 비교 증거가 같은 함수를 쓴다).
# 자동으로 다시 계산되는 "━ 작업 점검 ━" 체크 블록(☑/☐)은 뺀다 — 점검 결과가 바뀌어도 내용이 바뀐 것으로 잡히지 않게.
import hashlib, json

def fp(st):
    st = dict(st); st["note"] = str(st.get("note", "")).split("\n━ 작업 점검 ━")[0]
    return hashlib.sha1(json.dumps(st, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()[:12]
