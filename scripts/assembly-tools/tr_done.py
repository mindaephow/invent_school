# 트레일러 번호 하나를 끝낼 때 반복하는 일을 묶는다(2026-10-23): overlay_check(NN_3) → _cellcmp(NN_6) → index.json 에 6번 줄 → 그림을 public/_refs_tmp/trailer 로 복사(화면 업로드용).
#   python tr_done.py <번호> [<_cellcmp 모델 부품 번호들 콤마>]   (_cellcmp 인자를 안 주면 6번 그림은 건너뛴다)
import sys, os, json, shutil, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
N = int(sys.argv[1]); cc = sys.argv[2] if len(sys.argv) > 2 else None
env = dict(os.environ, PYTHONIOENCODING="utf-8")
def run(*a): r = subprocess.run([sys.executable, *a], capture_output=True, text=True, encoding="utf-8", env=env); return (r.stdout + r.stderr).strip().splitlines()[-1:] 
print("overlay:", run("overlay_check.py", "trailer", str(N)))
p = "refs/trailer/index.json"; d = json.load(open(p, encoding="utf-8"))
if cc:
    print("cellcmp:", run("_cellcmp.py", "trailer", str(N), cc))
    d = [r for r in d if not (int(r["step"]) == N and r["idx"] == 6)]
    d.append({"step": N, "idx": 6, "file": "%02d_6.jpg" % N, "note": "⑥ 단계 %d — 책 링 ↔ 모델 구멍 번호 대조(_cellcmp.py): 파랑 = 칸-줄 번호, 빨강 M = 모델이 돌기를 꽂은 구멍." % N})
d.sort(key=lambda r: (int(r["step"]), int(r["idx"]))); json.dump(d, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
tmp = os.path.join(HERE, "..", "..", "public", "_refs_tmp", "trailer"); os.makedirs(tmp, exist_ok=True)
for f in os.listdir("refs/trailer"):
    if f.startswith("%02d_" % N) and f.endswith(".jpg") or f == "%02d.jpg" % N: shutil.copy(os.path.join("refs/trailer", f), tmp)
shutil.copy(p, tmp); print("복사 완료 → public/_refs_tmp/trailer (업로드 뒤 지운다)")
