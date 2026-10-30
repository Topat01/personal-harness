#!/usr/bin/env python3
"""작업 환경 3분 점검. 표준 라이브러리만 쓴다(Python 3.8+).

사용: python3 preflight.py
무엇을 보나: Python 버전, 쓸 수 있는 패키지·명령, 시간 파싱 함정, git 설정, 쓰기 권한, 0.0.0.0 바인딩, 비밀값처럼 보이는 환경 변수 이름.
"""
import importlib.util
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from datetime import datetime

OK, WARN = "OK  ", "WARN"


def line(tag, name, detail=""):
    print(f"[{tag}] {name}" + (f": {detail}" if detail else ""))


def cmd_version(cmd):
    if not shutil.which(cmd):
        return None
    try:
        out = subprocess.run([cmd, "--version"], capture_output=True, text=True, timeout=10)
        return (out.stdout or out.stderr).strip().splitlines()[0]
    except Exception as e:  # 실행은 되지만 버전 출력이 없을 때
        return f"설치됨(버전 확인 실패: {e.__class__.__name__})"


def main():
    print("== 환경 점검 ==")
    v = sys.version_info
    line(OK if v >= (3, 9) else WARN, "python", sys.version.split()[0])

    print("\n== 패키지 ==")
    for mod in ["pandas", "numpy", "pytest", "matplotlib", "scipy", "sklearn"]:
        found = importlib.util.find_spec(mod) is not None
        line(OK if found else WARN, mod, "있음" if found else "없음 → 표준 라이브러리로 하거나 설치 전 사람에게 확인")

    print("\n== 명령 ==")
    for c in ["git", "node", "npm", "codex", "sqlite3", "make"]:
        ver = cmd_version(c)
        line(OK if ver else WARN, c, ver or "없음")

    print("\n== 시간 파싱 함정 ==")
    samples = ["2026-10-20T10:00:00Z", "2026-10-20T10:00:00+09:00", "2026-10-20 10:00:00", "2026/10/20 10:00"]
    for s in samples:
        try:
            d = datetime.fromisoformat(s)
            line(OK, f"fromisoformat('{s}')", "aware" if d.tzinfo else "naive(시간대 없음)")
        except ValueError:
            line(WARN, f"fromisoformat('{s}')", "실패 → strptime 형식 지정 또는 'Z'를 '+00:00'으로 바꿔 파싱")

    print("\n== git ==")
    if shutil.which("git"):
        for key in ["user.name", "user.email"]:
            r = subprocess.run(["git", "config", key], capture_output=True, text=True)
            val = r.stdout.strip()
            line(OK if val else WARN, key, val or "없음 → 커밋 전에 설정 필요")
        r = subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
        line(OK if r.returncode == 0 else WARN, "현재 폴더 git 저장소", "예" if r.returncode == 0 else "아님 → git init")

    print("\n== 쓰기·네트워크 ==")
    try:
        with tempfile.NamedTemporaryFile(dir=os.getcwd()):
            pass
        line(OK, "현재 폴더 쓰기")
    except OSError as e:
        line(WARN, "현재 폴더 쓰기", str(e))
    total, used, free = shutil.disk_usage(os.getcwd())
    line(OK if free > 1 << 30 else WARN, "디스크 여유", f"{free / (1 << 30):.1f} GB")
    try:
        s = socket.socket()
        s.bind(("0.0.0.0", 0))
        port = s.getsockname()[1]
        s.close()
        line(OK, "0.0.0.0 바인딩", f"가능(테스트 포트 {port})")
    except OSError as e:
        line(WARN, "0.0.0.0 바인딩", str(e))

    print("\n== 비밀값처럼 보이는 환경 변수 이름(값은 출력하지 않음) ==")
    names = [k for k in os.environ if any(t in k.upper() for t in ("KEY", "TOKEN", "SECRET", "PASSWORD"))]
    line(OK if not names else WARN, "개수", ", ".join(sorted(names)) if names else "없음")


if __name__ == "__main__":
    main()
