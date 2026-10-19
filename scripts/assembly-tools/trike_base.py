# 3륜바이크 1~10단계(저장소 데이터)를 마지막 모양(이동 적용)으로 읽어 asmlib Part 로 만든다.
import json, subprocess, numpy as np
from asmlib import *
def load_existing():
    """1~10단계 원본(y 올리기 전 좌표) — trike_base_1_10.json. design-assemblies.js 의 현재 값은 y 가 올라가 있어 쓰지 않는다."""
    import os
    return json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "trike_base_1_10.json"), encoding="utf-8"))
def final_parts(asm, upto=10):
    A = Asm("tmp", "t", "t"); out = []
    for k, st in enumerate(asm["steps"][:upto]):
        S = A.step(st["note"])
        for pt in st["parts"]:
            p, r = pt["p"], pt.get("r", [0, 0, 0])
            mv = pt.get("move")
            if mv and mv["at"] <= upto:
                p = mv.get("p") or [a + b for a, b in zip(p, mv["by"])]
                r = mv.get("r") or r
            out.append((k + 1, S.place(pt["n"], euler_to_R(r), p)))
    return A, out
if __name__ == "__main__":
    asm = load_existing(); A, parts = final_parts(asm)
    for k, pt in parts:
        print(k, pt.n, rnd(pt.p), R_to_euler(pt.R))
