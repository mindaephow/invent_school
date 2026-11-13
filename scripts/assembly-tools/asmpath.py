# 조립도 파일 자리 (2026-11-06).
#   조립도 하나의 파일(<이름>.py, <이름>_asm.json, <이름>_read.json, <이름>_entry.js …)은 전부
#   큐보/조립도/<N>권/<이름>/ 폴더에 있다. 도구는 예전처럼 scripts/assembly-tools 에서 돌고 파일을 <이름>_asm.json 처럼
#   이름만으로 열면, 이 모듈이 그 조립도 폴더로 이어 준다(읽기·쓰기·존재 확인·삭제·이름 바꾸기·복사·runpy).
#   새 도구는 첫 줄에 `import asmpath` 를 넣고, 폴더 경로가 직접 필요하면 asmpath.ap(이름, "_asm.json") 을 쓴다.
#   조립도 목록(폴더 이름)은 asmpath.names() — 예전의 glob("*.py") 를 대신한다.
import os, re, sys, io, builtins, shutil

TOOLS = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.join(TOOLS, "큐보", "조립도")


def _scan():
    d = {}
    if os.path.isdir(BASE):
        for v in sorted(os.listdir(BASE)):
            vp = os.path.join(BASE, v)
            if os.path.isdir(vp):
                for n in sorted(os.listdir(vp)):
                    if os.path.isdir(os.path.join(vp, n)):
                        d[n] = os.path.join(vp, n)
    return d


DIRS = _scan()


def _compile():
    if not DIRS:
        return None
    alt = "|".join(re.escape(n) for n in sorted(DIRS, key=len, reverse=True))
    return re.compile(r"^(%s)(\.py|_.+)$" % alt)


_RE = _compile()


def refresh():
    """새 조립도 폴더를 만든 직후 부른다."""
    global DIRS, _RE
    DIRS = _scan(); _RE = _compile()
    for p in DIRS.values():
        if p not in sys.path:
            sys.path.append(p)


def names():
    return sorted(DIRS)


def adir(name):
    return DIRS[name]


def ap(name, rest):
    """조립도 파일의 실제 경로. ap('trailer', '_asm.json'), ap('trailer', '.py')"""
    return os.path.join(DIRS[name], name + rest)


def list_counts(name):
    """교재 LIST 수량(`_list.json`)에 관리자가 확정한 수량(`_entry.js` 의 qtyOverride)을 덮어 쓴 것 — 부품 합계 대조는 모두 이 값을 쓴다(사용자 2026-11-13, 배틀로봇 15프레임 6·35프레임 3·리벳 16)."""
    import json, re
    f = ap(name, "_list.json")
    lst = json.load(open(f, encoding="utf-8")) if os.path.exists(f) else {}
    e = ap(name, "_entry.js")
    m = re.search(r"qtyOverride: (\{[^}]*\})", open(e, encoding="utf-8").read()) if os.path.exists(e) else None
    if m: lst.update(json.loads(m.group(1)))
    return lst


def resolve(p):
    if _RE is None or not isinstance(p, (str, os.PathLike)):
        return p
    s = os.fspath(p)
    if not isinstance(s, str) or not s:
        return p
    d, b = os.path.split(s)
    if d and os.path.normcase(os.path.abspath(d)) != os.path.normcase(TOOLS):
        return p
    m = _RE.match(b)
    if not m:
        return p
    return os.path.join(DIRS[m.group(1)], b)


# ── 파일 접근 이어 주기 ─────────────────────────────────────────────
if not getattr(builtins, "_asmpath_installed", False):
    builtins._asmpath_installed = True
    _open = builtins.open
    _io_open_code = getattr(io, "open_code", None)
    _stat = os.stat

    def _op(file, *a, **k):
        return _open(resolve(file), *a, **k)
    builtins.open = _op
    io.open = _op
    if _io_open_code:
        io.open_code = lambda path: _io_open_code(resolve(path))
    os.stat = lambda path, *a, **k: _stat(resolve(path), *a, **k)
    for _fn in ("exists", "isfile", "getmtime", "getsize", "getctime", "lexists"):   # Windows 3.12 는 exists·isfile 이 os.stat 을 안 거친다
        _f = getattr(os.path, _fn, None)
        if _f:
            setattr(os.path, _fn, (lambda f: (lambda path, *a, **k: f(resolve(path), *a, **k)))(_f))
    for _fn in ("remove", "unlink"):
        _f = getattr(os, _fn)
        setattr(os, _fn, (lambda f: (lambda path, *a, **k: f(resolve(path), *a, **k)))(_f))
    for _fn in ("replace", "rename"):
        _f = getattr(os, _fn)
        setattr(os, _fn, (lambda f: (lambda s, d, *a, **k: f(resolve(s), resolve(d), *a, **k)))(_f))
    for _fn in ("copy", "copy2", "copyfile", "move", "copyfileobj"):
        if _fn == "copyfileobj":
            continue
        _f = getattr(shutil, _fn)
        setattr(shutil, _fn, (lambda f: (lambda s, d, *a, **k: f(resolve(s), resolve(d), *a, **k)))(_f))
    # 조립도 폴더를 import 경로에 넣는다(import soccer, importlib.import_module(name))
    for _p in DIRS.values():
        if _p not in sys.path:
            sys.path.append(_p)
    # 조립도 스크립트를 직접 돌리면 작업 폴더를 도구 폴더로
    try:
        _m = os.path.abspath(sys.argv[0]) if sys.argv and sys.argv[0] else ""
        if _m.startswith(BASE):
            os.chdir(TOOLS)
    except Exception:
        pass
