# 쓰기 열기가 일시 잠금(OSError 22 등)으로 실패했을 때 "누가 파일을 잡았나"를 좁히는 진단(2026-11-14, 빌드의 kidknight_asm.json 간헐 OSError 22).
#   매핑은 핸들이 없어 Restart Manager 에 안 잡히므로, 실패 순간과 해소 순간에 전체 프로세스 스냅샷을 찍어 차이를 본다.
#   snap() → {pid: {...}}   diff(a, b, 초) → 사람이 읽는 한 줄들(그 사이 읽은 바이트·CPU 가 가장 늘어난 프로세스, 새로 생기거나 사라진 프로세스)
import subprocess, json, time

_PS = (r"Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{ pid=$_.ProcessId; ppid=$_.ParentProcessId; name=$_.Name; "
       r"rd=[int64]$_.ReadTransferCount; rdops=[int64]$_.ReadOperationCount; wr=[int64]$_.WriteTransferCount; "
       r"cpu=[int64]($_.KernelModeTime + $_.UserModeTime); cmd=(($_.CommandLine -replace '\s+',' ') + '') } } | ConvertTo-Json -Compress")

def snap():
    t = time.time()
    r = subprocess.run(["powershell", "-NoProfile", "-Command", _PS], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=25)
    rows = json.loads(r.stdout) if r.stdout.strip() else []
    if isinstance(rows, dict): rows = [rows]
    return {"t": t, "p": {int(x["pid"]): x for x in rows}}

def _short(x): return "%s(%s) %s" % (x["name"], x["pid"], (x.get("cmd") or "")[:70])

def diff(a, b, me=None):
    dt = max(b["t"] - a["t"], 0.001); out = []
    pa, pb = a["p"], b["p"]
    rows = []
    for pid, x in pb.items():
        if pid == me or pid not in pa: continue
        y = pa[pid]
        rows.append((x["rd"] - y["rd"], x["rdops"] - y["rdops"], (x["cpu"] - y["cpu"]) / 1e7, x["wr"] - y["wr"], x))   # cpu: 100ns 단위 → 초
    top_rd = sorted(rows, key=lambda r: -r[0])[:5]; top_cpu = sorted(rows, key=lambda r: -r[2])[:5]
    out.append("간격 %.1f초 — 읽은 바이트 많이 늘어난 프로세스: %s" % (dt, " ; ".join("%s +%dB/%d회" % (_short(r[4]), r[0], r[1]) for r in top_rd if r[0] > 0) or "없음"))
    out.append("CPU 많이 쓴 프로세스: %s" % (" ; ".join("%s +%.2fs" % (_short(r[4]), r[2]) for r in top_cpu if r[2] > 0.01) or "없음"))
    new = [x for pid, x in pb.items() if pid not in pa and pid != me]; gone = [x for pid, x in pa.items() if pid not in pb and pid != me]
    out.append("새로 생긴 프로세스: %s" % (" ; ".join(_short(x) for x in new) or "없음"))
    out.append("사라진 프로세스: %s" % (" ; ".join(_short(x) for x in gone) or "없음"))
    return out
