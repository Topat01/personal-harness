#!/usr/bin/env python3
"""데이터 첫 파악(CSV·TSV·JSON·JSONL·XLSX·로그). 표준 라이브러리만 쓴다. 결론을 내지 않고 사실만 보여 준다.

사용: python3 eda.py data/* [--top 5]
출력: 파일별 행 수, 완전 중복 행, 컬럼별 결측·고유값·상위 값·표기 흔들림·형식 모양·숫자 범위·시간 범위,
      그리고 담당자에게 물어볼 만한 "질문 거리"(해석은 사람이 한다).
"""
import argparse
import csv
import json
import re
import sys
from collections import Counter
from datetime import datetime

MISSING = {"", "null", "none", "n/a", "na", "nan", "-"}
TIME_FORMATS = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M", "%Y-%m-%d %H:%M",
                "%Y-%m-%d", "%Y/%m/%d", "%Y/%m/%d %H:%M", "%Y/%m/%d %H:%M:%S"]


def shape(v):
    """값의 모양: 숫자→9, 영문→a, 나머지 그대로. 형식이 섞였는지 보는 용도."""
    s = re.sub(r"[0-9]", "9", v)
    s = re.sub(r"[A-Za-z]", "a", s)
    return re.sub(r"(.)\1{2,}", r"\1\1+", s)


def norm(v):
    """대소문자·공백·구분자·앞의 v를 무시한 값. 같은 것을 다르게 적었는지 보는 용도."""
    s = v.strip().lower().replace("_", "").replace("-", "").replace("/", "").replace(" ", "")
    return re.sub(r"^v(?=\d)", "", s)


def parse_time(v):
    t = v.strip()
    if t.endswith("Z"):
        t = t[:-1]
    for f in TIME_FORMATS:
        try:
            return datetime.strptime(t, f)
        except ValueError:
            pass
    return None


def as_number(v):
    try:
        return float(v.replace(",", ""))
    except ValueError:
        return None


def load_table(path):
    """CSV·TSV·JSON(객체 배열)·JSONL·XLSX(openpyxl 있을 때)를 (header, body)로 읽는다. 표가 아니면 None."""
    low = path.lower()
    if low.endswith((".csv", ".tsv")):
        with open(path, newline="", encoding="utf-8-sig") as f:
            sample = f.read(4096)
            f.seek(0)
            delim = "\t" if low.endswith(".tsv") or sample.count("\t") > sample.count(",") else ","
            rows = list(csv.reader(f, delimiter=delim))
        return (rows[0], rows[1:]) if rows else ([], [])
    if low.endswith((".json", ".jsonl", ".ndjson")):
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
        try:
            data = json.loads(text)
        except ValueError:
            data = [json.loads(ln) for ln in text.splitlines() if ln.strip()]
        if isinstance(data, dict):
            lists = [v for v in data.values() if isinstance(v, list) and v and isinstance(v[0], dict)]
            if not lists:
                print(f"## {path}\n- JSON 객체, 최상위 키: {list(data)[:20]}\n")
                return None
            data = lists[0]
        if not (isinstance(data, list) and data and isinstance(data[0], dict)):
            print(f"## {path}\n- JSON이지만 객체 배열이 아님(유형 {type(data).__name__})\n")
            return None
        keys = []
        for d in data:
            for k in d:
                if k not in keys:
                    keys.append(k)
        cell = lambda v: "" if v is None else (json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else str(v))
        return keys, [[cell(d.get(k)) for k in keys] for d in data]
    if low.endswith(".xlsx"):
        try:
            import openpyxl
        except ImportError:
            print(f"## {path}\n- XLSX인데 openpyxl이 없음 → CSV로 내보낼 수 있는지, 설치해도 되는지 확인\n")
            return None
        ws = openpyxl.load_workbook(path, read_only=True, data_only=True).active
        rows = [["" if c is None else str(c) for c in r] for r in ws.iter_rows(values_only=True)]
        return (rows[0], rows[1:]) if rows else ([], [])
    return None


def profile_text(path, top):
    """로그·텍스트: 줄 수, 시각 모양, 자주 나오는 단어(레벨 등), 앞 3줄."""
    with open(path, encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    print(f"## {path}\n- 줄: {len(lines)}")
    stamps = Counter(shape(m.group(0)) for ln in lines for m in [re.search(r"\d{4}[-/]\d\d[-/]\d\d[ T]?[\d:]*", ln)] if m)
    levels = Counter(w for ln in lines for w in re.findall(r"\b(ERROR|WARN(?:ING)?|INFO|DEBUG|FATAL|CRITICAL)\b", ln))
    print(f"- 시각 모양: {dict(stamps.most_common(3))}\n- 레벨: {dict(levels)}")
    for ln in lines[:3]:
        print(f"    {ln[:160]}")
    print()
    hints = []
    if len(stamps) > 1:
        hints.append(f"{path}: 시각 형식이 {len(stamps)}가지 — 같은 기준(시간대)인지")
    return hints


def profile(path, top):
    t = load_table(path)
    if t is None:
        return profile_text(path, top) if path.lower().endswith((".log", ".txt", ".out")) else []
    header, body = t
    if not header:
        print(f"## {path}\n빈 파일\n")
        return []
    print(f"## {path}")
    print(f"- 행: {len(body)} (헤더 제외), 컬럼: {len(header)}")
    bad_width = sum(1 for r in body if len(r) != len(header))
    dup = sum(c - 1 for c in Counter(tuple(r) for r in body).values() if c > 1)
    print(f"- 컬럼 수가 다른 행: {bad_width}, 완전히 같은 행(추가분): {dup}")
    hints = []
    if dup:
        hints.append(f"{path}: 완전히 같은 행 {dup}개 — 중복 내보내기인지, 실제 반복인지")
    print()
    print("| 컬럼 | 결측 | 고유값 | 상위 값 | 형식 모양 | 범위 |")
    print("|---|---|---|---|---|---|")
    for i, col in enumerate(header):
        vals = [r[i] if i < len(r) else "" for r in body]
        miss = [v for v in vals if v.strip().lower() in MISSING]
        present = [v for v in vals if v.strip().lower() not in MISSING]
        cnt = Counter(present)
        shapes = Counter(shape(v) for v in present)
        rng = ""
        nums = [as_number(v) for v in present]
        times = [parse_time(v) for v in present]
        if present and all(n is not None for n in nums):
            rng = f"{min(nums):g} ~ {max(nums):g}"
        elif present and sum(t is not None for t in times) >= 0.8 * len(present):
            ok = [t for t in times if t]
            rng = f"{min(ok)} ~ {max(ok)} (파싱 실패 {len(present) - len(ok)})"
            if len(present) - len(ok):
                hints.append(f"{col}: 시각으로 읽히지 않는 값 {len(present) - len(ok)}개 — 버릴지, 원본 확인할지")
            hints.append(f"{col}: 시간대 기준(UTC/KST)과 경계(시작·끝 포함 여부)")
        top_s = ", ".join(f"{k}({c})" for k, c in cnt.most_common(top))
        shape_s = ", ".join(f"{k}({c})" for k, c in shapes.most_common(3))
        miss_s = f"{len(miss)}" + (f" [{', '.join(sorted(set(m if m else '공란' for m in miss)))}]" if miss else "")
        print(f"| {col} | {miss_s} | {len(cnt)} | {top_s} | {shape_s} | {rng} |")
        if miss:
            hints.append(f"{col}: 비어 있는 {len(miss)}건의 의미 — 아직 진행 중인지, 기록 누락인지")
        ascii_only = all(v.isascii() for v in present)
        if ascii_only and len(shapes) > 1 and len(cnt) > 1:
            hints.append(f"{col}: 형식이 {len(shapes)}가지 섞임 ({shape_s})")
        groups = {}
        for v in cnt:
            groups.setdefault(norm(v), set()).add(v)
        variants = [sorted(g) for g in groups.values() if len(g) > 1]
        if variants and len(cnt) <= 200:
            ex = "; ".join("/".join(g) for g in variants[:3])
            print(f"|  ↳ 표기 흔들림 | | | {ex} | | |")
            hints.append(f"{col}: 같은 값을 다르게 적은 것으로 보임 ({ex}) — 같은 것으로 봐도 되는지")
        prefixes = Counter(m.group(0) for m in (re.match(r"^[A-Za-z]+-", v) for v in present) if m)
        if 0 < len(prefixes) <= 8:
            rare = [f"{k}({c}행)" for k, c in prefixes.items() if c < 0.2 * len(present)]
            if rare:
                hints.append(f"{col}: 드문 접두어 {', '.join(rare)} — 성격이 다른 행(테스트·실험 등)인지")
        zeros = sum(1 for n in nums if n == 0) if present and all(n is not None for n in nums) else 0
        if zeros:
            hints.append(f"{col}: 0인 값 {zeros}개 — 실제 0인지, 다른 상태(폐기·미측정)의 표시인지")
        if 1 < len(cnt) <= 6 and present and all(n is not None and n == int(n) and abs(n) <= 20 for n in nums):
            hints.append(f"{col}: 숫자 코드({', '.join(sorted(cnt))}) — 크고 작음의 의미")
        if 1 < len(cnt) <= 6 and not rng:
            hints.append(f"{col}: 범주 {sorted(cnt)} — 범주별로 다르게 다뤄야 하는지")
        if col.lower().endswith("id") and i == 0 and len(cnt) < len(present):
            hints.append(f"{col}: ID가 중복됨 ({len(present) - len(cnt)}개) — 같은 기록이 두 번 들어온 것인지")
    print()
    return hints


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()
    hints = []
    for p in a.files:
        if p.lower().endswith((".csv", ".tsv", ".json", ".jsonl", ".ndjson", ".xlsx", ".log", ".txt", ".out")):
            hints += profile(p, a.top)
        else:
            print(f"## {p}\n(표·로그가 아니라 건너뜀: 문서·이미지는 직접 열어 확인)\n")
    print("## 질문 거리 (사실에서 나온 후보 — 해석·질문 문장은 사람이 정한다)")
    for h in hints:
        print(f"- {h}")
    print("- 공통: 성공 기준(숫자·현재값·측정 방법), 결과를 누가 어디서 보는지, 이번에 하지 않아도 되는 것")


if __name__ == "__main__":
    sys.exit(main())
