#!/usr/bin/env python3
"""제출 직전 점검. 표준 라이브러리만 쓴다.

사용: python3 check_submit.py [필수 제출물 ...] [--test-cmd "명령"] [--doc 제출설명.md]
종료 코드: 0 문제 없음 / 1 고칠 것 있음 / 2 아무 테스트도 실행되지 않음(통과로 읽지 말 것)
[권장]으로 표시한 항목은 종료 코드에 영향을 주지 않는다.
"""
import argparse
import os
import re
import subprocess
import sys

HEADINGS = ["선택한 판단과 근거", "검증 결과", "남은 한계"]
SECRET = re.compile(r"(sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{30,}|"
                    r"(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{8,}['\"])", re.I)
JUNK = [".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".cache", ".DS_Store"]


def sh(args):
    r = subprocess.run(args, capture_output=True, text=True)
    return r.returncode, (r.stdout + r.stderr).strip()


def tracked_files():
    code, out = sh(["git", "ls-files"])
    return out.splitlines() if code == 0 else []


def count_tests(output):
    m = re.search(r"(\d+) passed", output)
    if m:
        return int(m.group(1)), "failed" in output or "error" in output.lower()
    m = re.search(r"Ran (\d+) tests?", output)
    if m:
        return int(m.group(1)), "FAILED" in output
    return 0, True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("required", nargs="*", help="README가 요구한 제출물 경로")
    ap.add_argument("--test-cmd", default=None)
    ap.add_argument("--doc", default=None, help="제출 설명 문서(기본: SUBMIT.md, 없으면 세 요소가 담긴 .md를 찾음)")
    a = ap.parse_args()
    problems, warnings, nothing_checked = [], [], False

    for p in a.required:
        if not os.path.exists(p):
            problems.append(f"필수 제출물 없음: {p}")

    files = tracked_files()
    test_cmd = a.test_cmd
    if not test_cmd:
        allf = set(files) | set(os.listdir("."))
        if any(re.search(r"(^|/)(test_[^/]*|[^/]*_test)\.py$", f) for f in allf) or os.path.isdir("tests"):
            has_pytest = subprocess.run([sys.executable, "-c", "import pytest"], capture_output=True).returncode == 0
            test_cmd = "python3 -m pytest -q" if has_pytest else "python3 -m unittest discover -s tests" if os.path.isdir("tests") else "python3 -m unittest discover"
        elif os.path.exists("package.json") and '"test"' in open("package.json").read():
            test_cmd = "npm test --silent"
        elif os.path.exists("go.mod"):
            test_cmd = "go test ./..."
    if not test_cmd:
        nothing_checked = True
        print("[2] 테스트 파일을 찾지 못함 — 검증한 것이 없다")
    else:
        args = test_cmd.split()
        if args[0] == "python3":
            args[0] = sys.executable  # 지금 이 파이썬으로 실행(패키지 유무 판단과 일치)
        code, out = sh(args)
        n, failed = count_tests(out)
        print(f"테스트: `{test_cmd}` → {n}개 실행, {'실패 있음' if failed or code else '통과'}")
        if n == 0:
            nothing_checked = True
            print("[2] 실행된 테스트가 0개 — 통과로 읽지 말 것")
        elif failed or code:
            problems.append("테스트 실패:\n" + out[-1500:])

    doc = a.doc or ("SUBMIT.md" if os.path.exists("SUBMIT.md") else None)
    if not doc:
        for f in files:
            if f.endswith(".md") and all(h in open(f, encoding="utf-8", errors="ignore").read() for h in HEADINGS[1:]):
                doc = f
                break
    if doc and os.path.exists(doc):
        text = open(doc, encoding="utf-8").read()
        for h in HEADINGS:
            if h not in text:
                problems.append(f"{doc}에 '{h}' 내용이 없음(공식 안내의 세 요소)")
        if not re.search(r"\b[0-9a-f]{7,40}\b", text):
            warnings.append(f"{doc}에 커밋 해시(증거 좌표)가 없음")
        if "NOT_RUN" in text:
            warnings.append(f"{doc}에 NOT_RUN 항목이 남아 있음(실행하거나 한계로 옮길 것)")
    else:
        problems.append("제출 설명 문서를 찾지 못함(판단과 근거·검증 결과·남은 한계) — 과제가 정한 이름이면 --doc으로 지정")

    code, status = sh(["git", "status", "--short"])
    if code == 0 and status:
        problems.append("커밋 안 된 변경:\n" + status)
    code, tags = sh(["git", "tag", "-l", "submittable*"])
    if code == 0 and not tags:
        warnings.append("submittable 태그 없음(되돌아갈 지점)")

    for f in files:
        if any(part in JUNK for part in f.split("/")):
            problems.append(f"커밋된 잡동사니: {f}")
            continue
        try:
            if os.path.getsize(f) > 5 << 20:
                problems.append(f"5MB 넘는 파일: {f}")
                continue
            with open(f, encoding="utf-8", errors="ignore") as fh:
                for i, ln in enumerate(fh, 1):
                    if SECRET.search(ln):
                        problems.append(f"비밀값으로 보임: {f}:{i}")
                        break
        except OSError:
            pass

    print()
    for w in warnings:
        print(f"[권장] {w}")
    for p in problems:
        print(f"[1] {p}")
    if nothing_checked:
        return 2
    if problems:
        return 1
    print("[0] 문제 없음")
    return 0


if __name__ == "__main__":
    sys.exit(main())
