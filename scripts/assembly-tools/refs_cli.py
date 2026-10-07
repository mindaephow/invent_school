# refs-grid MCP 를 못 쓰는 세션(프로젝트 폴더가 아닌 곳에서 시작했거나 MCP 가 안 붙은 세션)에서 같은 일을 명령줄로 한다.
#   python refs_cli.py view   <이름> <단계> [x0 y0 x1 y1] [배율]          눈금 그림(refs_view)
#   python refs_cli.py show   <이름> <단계> <칸> <줄> x1 y1 x2 y2 x3 y3 x4 y4   모서리 4곳으로 격자만 그려서 번호를 본다(맞추기 전 눈 확인용). 출력: 그림 경로
#   python refs_cli.py fit    '<JSON>'   refs_fit 과 같은 입력(+ "label"). 결과를 refs/<이름>/fits/NN_<label>.json 에 저장하고 그림 경로·오차를 출력
#   python refs_cli.py render '<JSON>'   refs_render 와 같은 입력(plates 의 label 로 fits 를 읽는다). NN_1·NN_2 를 만들고 index.json 을 갱신
#   (JSON 은 PowerShell/Git Bash 따옴표 문제를 피하려면 파일로 주고 @파일경로 로 쓴다: python refs_cli.py fit @fit1.json)
import sys, os, json
import cv2, numpy as np
sys.stdout.reconfigure(encoding="utf-8")
import refs_auto as R

def jarg(s):
    return json.load(open(s[1:], encoding="utf-8")) if s.startswith("@") else json.loads(s)

def fitfile(name, step, label):
    return os.path.join(R.refs_dir(name), "fits", "%02d_%s.json" % (step, label))

def main():
    c = sys.argv[1]
    if c == "view":
        name, step = sys.argv[2], int(sys.argv[3]); rest = sys.argv[4:]
        a = {"name": name, "step": step}
        if len(rest) >= 4: a["bbox"] = [float(v) for v in rest[:4]]
        if len(rest) >= 5: a["scale"] = float(rest[4])
        print(json.dumps(R.cmd_view(a), ensure_ascii=False))
    elif c == "show":
        name, step, cols, rows = sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]); v = [float(x) for x in sys.argv[6:14]]
        corners = [[v[0], v[1]], [v[2], v[3]], [v[4], v[5]], [v[6], v[7]]]
        im = R.load_orig(name, step).copy()
        src = np.array([[0, 0], [cols - 1, 0], [cols - 1, rows - 1], [0, rows - 1]], np.float32); H = cv2.getPerspectiveTransform(src, np.array(corners, np.float32))
        P = R.project(H, cols, rows)
        for (cc, rr), p in zip(R.lattice(cols, rows).astype(int), P):
            cv2.circle(im, (int(p[0]), int(p[1])), 3, (0, 0, 255), -1)
            if rr == 0: cv2.putText(im, str(cc + 1), (int(p[0]) - 6, int(p[1]) - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 0, 0), 1)
            if cc == 0: cv2.putText(im, "r%d" % (rr + 1), (int(p[0]) + 6, int(p[1]) + 4), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 140, 0), 1)
        print(R.save_png(im, "show_%02d" % step))
    elif c == "fit":
        a = jarg(sys.argv[2]); label = a.pop("label"); r = R.cmd_fit(a)
        if r.get("ok") is False: print(json.dumps({k: v for k, v in r.items() if k != "pts"}, ensure_ascii=False)); sys.exit(1)
        os.makedirs(os.path.dirname(fitfile(a["name"], a["step"], label)), exist_ok=True)
        json.dump({"cols": a["cols"], "rows": a["rows"], "pts": r["pts"], "corners": r["corners"]}, open(fitfile(a["name"], a["step"], label), "w"))
        print(json.dumps({k: v for k, v in r.items() if k != "pts"}, ensure_ascii=False))
    elif c == "render":
        a = jarg(sys.argv[2]); plates = []
        for p in a["plates"]:
            j = json.load(open(fitfile(a["name"], a["step"], p["label"]), encoding="utf-8")); plates.append({"name": p.get("name") or p["label"], "cols": j["cols"], "rows": j["rows"], "pts": j["pts"], "ref": bool(p.get("ref"))})
        a["plates"] = plates; print(json.dumps(R.cmd_render(a), ensure_ascii=False))
    else:
        print(__doc__)

if __name__ == "__main__": main()
