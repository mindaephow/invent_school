# 부품 방향·제자리 검사(관리자 지시 2026-10-09 — "부품을 가져와 제자리에 놓는 게 가장 중요한 부분, 첫 단추").
# build.py 가 <이름>_rules.json 에 "placecheck": true 가 있을 때 부른다. 그룹으로 옮겨 붙이는 부품(move.at 가 같은 것)은 한 덩어리(강체)로 움직여야 한다:
#   부품 쌍마다 "옮기기 전 상대 자세"와 "옮긴 뒤 상대 자세"가 같아야 한다(거울 복사·부품별 따로 놓기로 모양이 깨지는 것을 잡는다 — 강아지로봇 36번에서 170mm 어긋났다).
#   예외: 부품 extra 에 "nonRigid": true (일부러 관절처럼 돌아가는 부품).
import numpy as np
from asmlib import euler_to_R

def _pose_before(pt, at):   # 이 이동 직전(at−1 단계 끝)의 자세: poseAt 가 있으면 그것, 아니면 더 앞의 move·lift 를 반영한 자세, 없으면 기본 자세
    pa = (pt.get("poseAt") or {}).get(str(at - 1))
    if pa: return np.array(pa["p"], float), np.array(euler_to_R(pa["r"]), float)
    p, R = np.array(pt["p"], float), np.array(euler_to_R(pt["r"]), float)
    mv = pt.get("move")
    if mv and mv["at"] < at: p, R = np.array(mv["p"], float), np.array(euler_to_R(mv["r"]), float)
    lf = pt.get("lift")
    if lf and lf.get("from", 0) <= at - 1 < lf.get("at", 0): p = p + np.array(lf.get("by", [0, 0, 0]), float)
    return p, R

def rigid_problems(asm, tol=1.0, exempt=()):
    groups = {}
    for si, st in enumerate(asm, 1):
        for pt in st.get("parts", []):
            mv = pt.get("move")
            if mv and not pt.get("nonRigid"):
                p0, r0 = _pose_before(pt, mv["at"])
                groups.setdefault(mv["at"], []).append((si, pt["n"], p0, r0, np.array(mv["p"], float), np.array(euler_to_R(mv["r"]), float)))
    out = []; summary = []
    for at, L in sorted(groups.items()):
        worst, w = 0.0, None
        for i in range(len(L)):
            for j in range(i + 1, len(L)):
                _, ni, pi, Ri, qi, Si = L[i]; _, nj, pj, Rj, qj, Sj = L[j]
                e = max(float(np.abs(Ri.T @ Rj - Si.T @ Sj).max()) * 30.0, float(np.abs(Ri.T @ (pj - pi) - Si.T @ (qj - qi)).max()))
                if e > worst: worst, w = e, (L[i][0], ni, L[j][0], nj)
        summary.append((at, len(L), worst))
        if worst > tol and at not in exempt: out.append("%d번에서 옮겨 붙이는 그룹(%d개 부품)이 한 덩어리로 움직이지 않는다 — 부품 사이 상대 자세가 최대 %.1fmm 어긋남 (%s %d번 ↔ %s %d번)" % (at, len(L), worst, w[1], w[0], w[3], w[2]))
    return out, summary
