# 파일을 지금 누가 열고 있는지(프로세스 이름·PID) 윈도우 Restart Manager 로 알려 준다 — 빌드의 kidknight_asm.json OSError 22(일시 잠금) 조사용(2026-11-14).
#   python who_holds.py <파일 경로> [...]
import sys, ctypes
from ctypes import wintypes as W
sys.stdout.reconfigure(encoding="utf-8")
class UP(ctypes.Structure): _fields_ = [("dwProcessId", W.DWORD), ("ProcessStartTime", W.FILETIME)]
class RPI(ctypes.Structure): _fields_ = [("Process", UP), ("strAppName", W.WCHAR * 256), ("strServiceShortName", W.WCHAR * 64), ("ApplicationType", ctypes.c_int), ("AppStatus", W.ULONG), ("TSSessionId", W.DWORD), ("bRestartable", W.BOOL)]
def holders(paths):
    rm = ctypes.WinDLL("rstrtmgr"); h = W.DWORD(); key = (W.WCHAR * 33)()
    if rm.RmStartSession(ctypes.byref(h), 0, key): return None
    try:
        arr = (W.LPCWSTR * len(paths))(*paths)
        if rm.RmRegisterResources(h, len(paths), arr, 0, None, 0, None): return None
        need = W.UINT(); have = W.UINT(10); reasons = W.DWORD(); buf = (RPI * 10)()
        r = rm.RmGetList(h, ctypes.byref(need), ctypes.byref(have), buf, ctypes.byref(reasons))
        if r not in (0, 234): return None
        return [(buf[i].Process.dwProcessId, buf[i].strAppName) for i in range(have.value)]
    finally: rm.RmEndSession(h)
if __name__ == "__main__":
    import os
    for p in sys.argv[1:]:
        r = holders([os.path.abspath(p)])
        print(p, "→", "조회 실패" if r is None else (r or "잡고 있는 프로세스 없음"))
