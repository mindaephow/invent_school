# 부품의 면·구멍·돌기 이름 — public/design-faces.js 와 같은 규칙(화면·MCP 와 이름이 어긋나지 않게 한다. 규칙을 바꾸면 양쪽을 같이 고치고 test_faces.js 로 대조한다).
#   · 면은 홀면(구멍이 있는 면) / 돌기면(돌기가 나온 면) 두 종류, 같은 종류가 둘이면 부품 축(+y, -y …)으로 구분한다. 앞면 = +y, 뒷면 = -y.
#   · 면 안의 번호: 수직인 축을 뺀 나머지 두 축을 x → y → z 순으로 놓고 첫째가 열, 둘째가 줄. 각 축의 − 끝부터 1, 2, 3….
#   · 이름 예: "홀면 +y 열5·줄1"(격자 면), "돌기면 +z 1"(한 줄 면). 같은 이름 부품은 조립도 전체에서 나온 순서로 "35프레임 1번".
import re

AX = ["x", "y", "z"]
TOL = 2.0   # mm — 같은 열·줄로 묶는 허용 오차(design-faces.js 의 TOL 과 같다)


def _dominant(d):
    k = 0
    for i in range(1, 3):
        if abs(d[i]) > abs(d[k]): k = i
    return AX[k], (1 if d[k] >= 0 else -1)


def _ranks(vals):
    s = sorted(vals); groups = []
    for v in s:
        if groups and abs(v - groups[-1][-1]) <= TOL: groups[-1].append(v)
        else: groups.append([v])
    centers = [sum(g) / len(g) for g in groups]
    def of(v):
        for i, c in enumerate(centers):
            if abs(c - v) <= TOL: return i + 1
        return 0
    return of, len(centers)


def faces_of(conn):
    """연결점 {pegs, holes} → 면 목록. 면: {key, kind, axis, sign, cols, rows, items:[{id, col, row, label, pos}]}"""
    raw = {}
    def put(kind, axis, sign, c):
        key = f"{kind}면 {'+' if sign > 0 else '-'}{axis}"
        raw.setdefault(key, {"key": key, "kind": kind, "axis": axis, "sign": sign, "items": []})["items"].append({"id": c["id"], "pos": c["pos"], "len": c.get("len", 0)})
    for c in conn.get("pegs", []):
        a, sg = _dominant(c["dir"]); put("돌기", a, sg, c)
    for c in conn.get("holes", []):
        a, sg = _dominant(c["dir"]); put("홀", a, -sg, c)           # 구멍의 dir 은 끼워 들어가는 방향 → 입구 면은 반대쪽
        if c.get("through"): put("홀", a, sg, c)                    # 관통 구멍은 반대 면에도 열려 있다
    out = []
    for f in raw.values():
        A, B = [a for a in AX if a != f["axis"]]
        ia, ib = AX.index(A), AX.index(B)
        ra, na = _ranks([it["pos"][ia] for it in f["items"]]); rb, nb = _ranks([it["pos"][ib] for it in f["items"]])
        for it in f["items"]:
            it["col"], it["row"] = ra(it["pos"][ia]), rb(it["pos"][ib])
            it["label"] = f"{it['col']}" if nb == 1 else f"열{it['col']}·줄{it['row']}"
        f["cols"], f["rows"] = na, nb
        f["colAxis"], f["rowAxis"] = A, B
        out.append(f)
    return out


_NAME = re.compile(r"^(홀면|돌기면)\s*\(?\s*([+\-−])\s*([xyz])\s*\)?\s*(.*)$")


def parse_item_name(name):
    """'홀면 +y 열5·줄1' → ('홀', '+y' 의 (sign, axis), '열5·줄1'). 마이너스는 -, − 둘 다 받는다. 이름이 아니면 None."""
    m = _NAME.match(str(name).strip())
    if not m: return None
    kind = "홀" if m.group(1) == "홀면" else "돌기"
    sign = 1 if m.group(2) == "+" else -1
    label = m.group(4).strip().replace(" ", "").replace("열", "열").replace("줄", "줄")
    label = re.sub(r"^열(\d+)[·,]?줄(\d+)$", r"열\1·줄\2", label)
    return kind, sign, m.group(3), label


def resolve_item(conn, name):
    """이름 → (연결점 id, 종류('돌기'|'홀'), 면 부호, 면 축). 이름이 아니면 None. 없는 이름이면 KeyError 로 가능한 이름을 알려 준다."""
    p = parse_item_name(name)
    if p is None: return None
    kind, sign, axis, label = p
    faces = faces_of(conn)
    for f in faces:
        if f["kind"] == kind and f["axis"] == axis and f["sign"] == sign:
            for it in f["items"]:
                if it["label"] == label: return it["id"], kind, sign, axis
            raise KeyError(f"{name}: 이 면에 '{label}' 이(가) 없다. 가능한 번호: " + ", ".join(i["label"] for i in f["items"]))
    raise KeyError(f"{name}: 이런 면이 없다. 가능한 면: " + ", ".join(f["key"] for f in faces))


def name_of(conn, kind_id, ident, sign=None):
    """연결점 id → 이름(첫 번째 면 기준). kind_id: '돌기' | '홀'. sign 을 주면 그 부호의 면으로."""
    for f in faces_of(conn):
        if f["kind"] != kind_id: continue
        if sign is not None and f["sign"] != sign: continue
        for it in f["items"]:
            if it["id"] == ident: return f"{f['kind']}면 {'+' if f['sign'] > 0 else '-'}{f['axis']} {it['label']}"
    return ident


def number_parts(parts):
    """부품 목록(순서대로, .n 이름을 가진 것) → {부품 객체 id: 번호}. 같은 이름의 n번째. (design-faces.js numberParts 와 같다)"""
    seq, out = {}, {}
    for p in parts:
        seq[p.n] = seq.get(p.n, 0) + 1; out[id(p)] = seq[p.n]
    return out


# ───────── 면 방향으로 자세 정하기 ─────────
# "돌기면 +z 는 아래, 홀면 +y 는 +Z 쪽" 처럼 부품의 면이 월드 어느 쪽을 보게 할지 말하면 회전 행렬을 계산한다(오일러 각도를 손으로 짐작하지 않는다).
#   방향 말: 위·아래(= +Y·-Y), +X -X +Z -Z (바닥 방향선 이름), 또는 [x, y, z] 벡터. 왼쪽·오른쪽 같은 카메라 기준 말은 쓰지 않는다.
import numpy as np

_DIRS = {"위": (0, 1, 0), "아래": (0, -1, 0), "+Y": (0, 1, 0), "-Y": (0, -1, 0), "+X": (1, 0, 0), "-X": (-1, 0, 0), "+Z": (0, 0, 1), "-Z": (0, 0, -1)}
_FACE = re.compile(r"^(홀면|돌기면)\s*\(?\s*([+\-−])\s*([xyz])\s*\)?$")


def _world_dir(d):
    if isinstance(d, str):
        k = d.strip().replace("−", "-").upper().replace("面", "")
        k = {"위": "위", "아래": "아래"}.get(d.strip(), k)
        if k not in _DIRS: raise KeyError(f"방향 '{d}' 을(를) 모른다. 쓸 수 있는 말: 위, 아래, +X, -X, +Z, -Z (+Y/-Y) 또는 [x, y, z]")
        v = np.array(_DIRS[k], float)
    else:
        v = np.array(d, float); v /= np.linalg.norm(v)
    return v


_AXIS = re.compile(r"^축\s*([+\-−])\s*([xyz])$")

def _face_normal(conn, spec):
    """면 이름('돌기면 +z') 또는 부품 축('축 +x' — 프레임의 길이 방향처럼 면으로 말할 수 없는 방향)의 로컬 방향 벡터."""
    ma = _AXIS.match(str(spec).strip())
    if ma:
        n = np.zeros(3); n[AX.index(ma.group(2))] = 1 if ma.group(1) == "+" else -1
        return n
    m = _FACE.match(str(spec).strip())
    if not m: raise KeyError(f"면 이름이 아니다: {spec!r} (예: '돌기면 +z', '홀면 +y', 부품 축은 '축 +x')")
    kind = "홀" if m.group(1) == "홀면" else "돌기"
    sign = 1 if m.group(2) == "+" else -1
    axis = m.group(3)
    keys = {(f["kind"], f["axis"], f["sign"]) for f in faces_of(conn)}
    if (kind, axis, sign) not in keys:
        raise KeyError(f"{spec}: 이 부품에는 그런 면이 없다. 있는 면: " + ", ".join(f["key"] for f in faces_of(conn)))
    n = np.zeros(3); n[AX.index(axis)] = sign
    return n


def _rot_between(a, b):
    """a 를 b 로 돌리는 최소 회전."""
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b))
    if np.linalg.norm(v) < 1e-9:
        if c > 0: return np.eye(3)
        axis = np.cross(a, [1, 0, 0]) if abs(a[0]) < 0.9 else np.cross(a, [0, 1, 0])
        axis /= np.linalg.norm(axis); return 2 * np.outer(axis, axis) - np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K * (1 / (1 + c))


def orient(conn, mapping):
    """mapping: {"돌기면 +z": "아래", "홀면 +y": "+Z"} → 회전 행렬 R (부품 로컬 → 월드).
    조건 2개면 자세가 하나로 정해진다(두 면 사이 각도와 두 방향 사이 각도가 다르면 모순 오류).
    조건 1개면 그 면만 맞추고 나머지는 '부품의 +x 가 바닥 +X 에 가장 가깝게' 정한다(비어 있는 회전이라 결과를 확인할 것)."""
    items = [(_face_normal(conn, k), _world_dir(v), k, v) for k, v in mapping.items()]
    if not items: raise ValueError("면 조건이 하나도 없다")
    if len(items) == 1:
        a, b, _, _ = items[0]
        R = _rot_between(a, b)
        # 남는 회전(b 축 둘레)은 부품 +x 를 바닥 +X 쪽에 두도록
        def perp(v): w = v - np.dot(v, b) * b; return w
        cur = perp(R @ np.array([1.0, 0, 0])); tgt = perp(np.array([1.0, 0, 0]))
        if np.linalg.norm(tgt) < 1e-6: tgt = perp(np.array([0, 0, 1.0]))
        if np.linalg.norm(cur) > 1e-6:
            cur /= np.linalg.norm(cur); tgt /= np.linalg.norm(tgt)
            ang = np.arctan2(float(np.dot(np.cross(cur, tgt), b)), float(np.dot(cur, tgt)))
            K = np.array([[0, -b[2], b[1]], [b[2], 0, -b[0]], [-b[1], b[0], 0]])
            R = (np.eye(3) + np.sin(ang) * K + (1 - np.cos(ang)) * K @ K) @ R
        return R
    if len(items) > 2: raise ValueError("면 조건은 최대 2개까지 쓴다(2개면 자세가 정해진다)")
    (a1, b1, k1, v1), (a2, b2, k2, v2) = items
    ang_a = float(np.degrees(np.arccos(np.clip(np.dot(a1, a2), -1, 1)))); ang_b = float(np.degrees(np.arccos(np.clip(np.dot(b1, b2), -1, 1))))
    if abs(ang_a - ang_b) > 1.0:
        raise ValueError(f"조건이 모순이다: '{k1}'과 '{k2}' 두 면 사이는 {ang_a:.0f}°인데 '{v1}'과 '{v2}' 두 방향 사이는 {ang_b:.0f}°")
    if abs(np.dot(a1, a2)) > 0.999: raise ValueError(f"'{k1}'과 '{k2}' 는 같은 축의 면이라 자세를 하나로 못 정한다 (다른 축의 면을 골라 주세요)")
    def frame(u, v):
        e1 = u / np.linalg.norm(u); e2 = v - np.dot(v, e1) * e1; e2 /= np.linalg.norm(e2); return np.column_stack([e1, e2, np.cross(e1, e2)])
    return frame(b1, b2) @ frame(a1, a2).T


def describe_orientation(conn, R):
    """회전 R 에서 각 면이 월드 어느 쪽을 보는지 — {면 key: '위'|'아래'|'+X'…} (검산용)"""
    out = {}
    for f in faces_of(conn):
        n = np.zeros(3); n[AX.index(f["axis"])] = f["sign"]; w = R @ n
        k = int(np.argmax(np.abs(w))); s = 1 if w[k] > 0 else -1
        out[f["key"]] = ("위" if s > 0 else "아래") if k == 1 else ("+" if s > 0 else "-") + "XYZ"[k]
    return out
