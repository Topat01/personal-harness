#!/usr/bin/env python3
"""작업 폴더 첫 파악(과제 유형 판별용). 표준 라이브러리만 쓴다. 파일을 바꾸지 않는다.

사용: python3 scan.py [폴더]   (기본: 현재 폴더)
출력: README·과제 안내의 핵심 줄, 파일 구성, 기존 프로젝트 표지(실행·테스트 명령), git 이력, 데이터·문서 파일 목록.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter

SKIP = {".git", "node_modules", ".venv", "venv", "__pycache__", ".pytest_cache", ".agents", ".cache", "dist", "build"}
KEYS = re.compile(r"(제출|필수|요구|목표|산출|결과물|완료|조건|금지|포트|실행|테스트|평가|deliverable|must|required|should|submit|port|test)", re.I)
DATA_EXT = {".csv", ".tsv", ".json", ".jsonl", ".ndjson", ".xlsx", ".xls", ".parquet", ".db", ".sqlite", ".log", ".txt"}
DOC_EXT = {".md", ".pdf", ".docx", ".html"}
MARKERS = ["package.json", "pyproject.toml", "requirements.txt", "setup.py", "Makefile", "Dockerfile",
           "docker-compose.yml", ".env.example", "pytest.ini", "tsconfig.json", "go.mod", "Cargo.toml", "pom.xml"]


def is_harness(path):
    """이 하네스 폴더(이름이 무엇이든)는 과제 파일이 아니다."""
    return os.path.exists(os.path.join(path, "setup.sh")) and os.path.exists(os.path.join(path, "tools", "scan.py"))


def walk(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP and not x.startswith(".") and not is_harness(os.path.join(d, x)))
        for f in sorted(files):
            if f.startswith("."):
                continue  # 환경 파일(.bashrc 등) 제외
            yield os.path.relpath(os.path.join(d, f), root)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "."
    files = list(walk(root))
    readmes = [f for f in files if re.search(r"(^|/)(readme|과제|안내|task|problem|instructions?)[^/]*\.(md|txt)$", f, re.I)]
    print("== 과제 안내 핵심 줄 ==")
    for r in readmes[:5]:
        print(f"## {r}")
        with open(os.path.join(root, r), encoding="utf-8", errors="replace") as fh:
            for i, ln in enumerate(fh, 1):
                s = ln.rstrip()
                if s.startswith("#") or (s.strip() and KEYS.search(s)) or re.match(r"^\s*(\d+\.|[-*])\s", s):
                    print(f"{i:>4}: {s[:200]}")
    if not readmes:
        print("(README·과제 안내 파일을 찾지 못함)")

    print("\n== 파일 구성 ==")
    ext = Counter(os.path.splitext(f)[1].lower() or "(없음)" for f in files)
    print(f"파일 {len(files)}개: " + ", ".join(f"{k} {v}" for k, v in ext.most_common(12)))
    tops = Counter(f.split("/")[0] + ("/" if "/" in f else "") for f in files)
    print("최상위: " + ", ".join(f"{k}({v})" for k, v in sorted(tops.items())))

    print("\n== 기존 프로젝트 표지 ==")
    found = [m for m in MARKERS if os.path.exists(os.path.join(root, m))]
    print("표지 파일: " + (", ".join(found) or "없음 → 새로 만드는 과제일 가능성"))
    if "package.json" in found:
        try:
            pj = json.load(open(os.path.join(root, "package.json")))
            print(f"npm scripts: {pj.get('scripts', {})}")
            print(f"dependencies: {list((pj.get('dependencies') or {}).keys())[:15]}")
        except ValueError as e:
            print(f"package.json 읽기 실패: {e}")
    if "Makefile" in found:
        targets = re.findall(r"^([A-Za-z0-9_.-]+):", open(os.path.join(root, "Makefile")).read(), re.M)
        print(f"make 대상: {targets[:15]}")
    tests = [f for f in files if re.search(r"(^|/)(tests?/|test_[^/]*\.py$|[^/]*_test\.(py|go)$|[^/]*\.(test|spec)\.[jt]sx?$)", f)]
    print(f"테스트 파일: {len(tests)}개 {tests[:8]}")
    src = [f for f in files if os.path.splitext(f)[1] in {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb"} and f not in tests]
    print(f"소스 파일: {len(src)}개 {src[:10]}")
    if tests:
        print("→ 기존 테스트가 있으면 무엇보다 먼저 한 번 실행해 현재 상태를 기록한다")

    print("\n== git ==")
    r = subprocess.run(["git", "-C", root, "log", "--oneline", "-5"], capture_output=True, text=True)
    print(r.stdout.strip() or "(git 이력 없음)")

    print("\n== 데이터·문서 ==")
    data = [f for f in files if os.path.splitext(f)[1].lower() in DATA_EXT and not re.search(r"(^|/)(readme|requirements[^/]*|license)[^/]*$", f, re.I)]
    docs = [f for f in files if os.path.splitext(f)[1].lower() in DOC_EXT and f not in readmes]
    for f in data[:30]:
        print(f"데이터: {f} ({os.path.getsize(os.path.join(root, f)):,} B)")
    for f in docs[:30]:
        print(f"문서: {f}")
    if data:
        print(f"→ 다음: python3 {os.path.dirname(os.path.abspath(__file__))}/eda.py " + " ".join(data[:10]))
    print("\n다음: 유형(A 데이터→결과물 / B 기존 코드 수정 / C 서비스·도구 / D 문서 응답 / E 분석 보고)과 제출물 목록, 해석이 갈리는 지점 3개를 정리")


if __name__ == "__main__":
    main()
