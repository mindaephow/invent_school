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

    class _SkipSame(io.StringIO):
        """<이름>_asm.json 은 빌드·점검 도구가 실행될 때마다 다시 쓰는데, 내용이 같아도 수정 시각이 바뀌면 Claude 앱이 돌리는 git status 가 그 파일을 다시 해시하며(메모리 매핑) 몇 초 잠가 다음 쓰기가 OSError 22 로 실패했다(2026-11-14 시험으로 확인). 닫을 때 기존 내용과 같으면 디스크에 쓰지 않는다."""
        def __init__(self, path, enc):
            super().__init__(); self._path = path; self._enc = enc or "utf-8"; self._done = False
        def close(self):
            if not self._done:
                self._done = True; new = self.getvalue()
                try: old = _open(self._path, "r", encoding=self._enc).read() if os.path.exists(self._path) else None
                except Exception: old = None
                if old != new:
                    with _open(self._path, "w", encoding=self._enc) as _fh: _fh.write(new)
            super().close()

    def _lock_log(_msg):
        try: _open(os.path.join(TOOLS, ".open_retry.log"), "a", encoding="utf-8").write(_msg.rstrip("\n") + "\n")
        except Exception: pass
        try: import rule_status as _rs; _rs.sync_writelock()
        except Exception: pass

    def _op(file, *a, **k):
        _p = resolve(file); _mode = str(a[0] if a else k.get("mode", "r"))
        if not any(c in _mode for c in "wax+"): return _open(_p, *a, **k)
        if _mode in ("w", "wt") and isinstance(_p, str) and _p.endswith("_asm.json"): return _SkipSame(_p, k.get("encoding"))
        import time as _t, errno as _e   # 쓰기로 열 때 윈도우가 다른 프로세스의 일시 잠금으로 EINVAL(22)·EACCES·EBUSY 를 내면 잠깐 기다렸다 다시 연다(빌드의 kidknight_asm.json 간헐 OSError 22, 2026-11-14). 끝까지 안 되면 그대로 올리고 기록을 남긴다
        _T = (_e.EINVAL, _e.EACCES, _e.EBUSY); _a0 = None; _t0 = _t.time(); _hd = lambda: __import__("time").strftime("%H:%M:%S")
        for _i in range(12):
            try:
                _f = _open(_p, *a, **k)
            except OSError as _x:
                if _x.errno not in _T: raise
                if _i == 0:   # 처음 실패한 순간: 파일 상태·잡은 프로세스(Restart Manager)·전체 프로세스 스냅샷 A 를 남긴다 — 매핑은 핸들이 없어 RM 에 안 보이므로 스냅샷 차이(lock_diag)로 범인을 좁힌다
                    _st = ""
                    try: _s = os.stat(_p); _st = " 파일 %dB 수정 %s 접근 %s" % (_s.st_size, _t.strftime("%H:%M:%S", _t.localtime(_s.st_mtime)), _t.strftime("%H:%M:%S", _t.localtime(_s.st_atime)))
                    except Exception: pass
                    try: import who_holds as _wh; _rm = _wh.holders([os.path.abspath(_p)])
                    except Exception as _we: _rm = "조회 실패 %s" % _we
                    _lock_log("%s [시작] %s errno=%s pid=%d%s | Restart Manager 잡은 프로세스: %s" % (_hd(), _p, _x.errno, os.getpid(), _st, _rm))
                    try: import lock_diag as _ld; _a0 = _ld.snap()
                    except Exception as _se: _lock_log("%s   스냅샷 A 실패: %s" % (_hd(), _se))
                else:
                    try: import who_holds as _wh; _rm2 = _wh.holders([os.path.abspath(_p)])
                    except Exception: _rm2 = "?"
                    _lock_log("%s   재시도 %d errno=%s RM=%s" % (_hd(), _i + 1, _x.errno, _rm2))
                if _i == 11:
                    _lock_log("%s [끝내 실패] %d번·%.1f초 %s" % (_hd(), _i + 1, _t.time() - _t0, _p)); raise
                _t.sleep(0.5); continue
            if _i > 0:   # 재시도 끝에 열림: 해소된 순간 스냅샷 B 와 A 의 차이를 적는다(읽은 바이트·CPU 가 늘어난 프로세스, 새로 생기거나 사라진 프로세스)
                _lock_log("%s [해소] %d번째 시도에 열림, 막힌 시간 %.1f초" % (_hd(), _i + 1, _t.time() - _t0))
                try:
                    import lock_diag as _ld
                    if _a0: _b = _ld.snap(); [_lock_log("      " + _l) for _l in _ld.diff(_a0, _b, me=os.getpid())]
                except Exception as _se: _lock_log("%s   스냅샷 B 실패: %s" % (_hd(), _se))
            return _f
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
