#!/usr/bin/env python3
"""경과 시간과 단계 순서. 표준 라이브러리만 쓴다. 시간 배분은 정하지 않는다.

사용: python3 checkpoint.py start [--minutes 제한분]   # 시작 시각 기록(.kit_start)
      python3 checkpoint.py                           # 경과·남은 시간, 단계 순서
      python3 checkpoint.py stage <번호>              # 지금 단계 기록(1~8)
"""
import argparse
import json
import os
import sys
import time

FILE = ".kit_start"
STAGES = ["읽기: 유형·제출물·해석 갈리는 지점", "묻기: 담당자 질문(사소한 것부터 하나씩)", "합의: PLAN + 첫 커밋",
          "설계: 내 구조안 → design-review", "짓기: 단위 루프, 제출 가능 상태 먼저 확보(tag)",
          "검증: 경계·재확인·리뷰", "줄이기: scope-check → 기능 동결", "쓰기: 제출 설명 → check_submit → 화면 확인 → 제출"]


def load():
    if not os.path.exists(FILE):
        print(f"시작 기록 없음 → python3 {sys.argv[0]} start [--minutes 제한분]")
        sys.exit(1)
    return json.load(open(FILE))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="status", choices=["start", "status", "stage"])
    ap.add_argument("n", nargs="?", type=int)
    ap.add_argument("--minutes", type=int, default=None)
    a = ap.parse_args()
    if a.cmd == "start":
        if os.path.exists(FILE):
            print(f"이미 시작 기록이 있음 (다시 시작하려면 {FILE} 삭제)")
            return 1
        json.dump({"start": time.time(), "minutes": a.minutes, "stage": 1}, open(FILE, "w"))
        print(f"시작 기록: {time.strftime('%H:%M:%S')}" + (f" / 제한 {a.minutes}분" if a.minutes else ""))
        return 0
    d = load()
    if a.cmd == "stage":
        if not a.n or not 1 <= a.n <= len(STAGES):
            print(f"단계 번호는 1~{len(STAGES)}")
            return 1
        d["stage"] = a.n
        json.dump(d, open(FILE, "w"))
    t = (time.time() - d["start"]) / 60
    line = f"경과 {t:.0f}분"
    if d.get("minutes"):
        left = d["minutes"] - t
        line += f" / 남은 시간 {left:.0f}분 (종료 {time.strftime('%H:%M', time.localtime(d['start'] + d['minutes'] * 60))})"
    print(line)
    cur = d.get("stage", 1)
    for i, s in enumerate(STAGES, 1):
        print(f"{'▶' if i == cur else ' '} {i}. {s}")
    if d.get("minutes") and d["minutes"] - t <= max(10, d["minutes"] * 0.1):
        print("※ 마감 임박: 새 작업 중단, 제출 가능 상태 확인·저장·커밋·제출")
    return 0


if __name__ == "__main__":
    sys.exit(main())
