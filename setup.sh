#!/usr/bin/env bash
# 작업 폴더 루트에서 실행: bash <kit>/setup.sh
# 이미 있는 파일은 덮어쓰지 않는다(과제가 같은 이름을 요구하면 과제 쪽을 우선).
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd)"
copy() { if [ -e "$2" ]; then echo "건너뜀(이미 있음): $2"; else cp -R "$1" "$2"; echo "복사: $2"; fi; }
tmp="$(mktemp)"; sed "s|~/kit|$KIT|g" "$KIT/AGENTS.md" > "$tmp"
if [ -e AGENTS.md ]; then
  printf '\n\n' >> AGENTS.md; cat "$tmp" >> AGENTS.md; echo "덧붙임: AGENTS.md (기존 내용 뒤)"
else
  cp "$tmp" AGENTS.md; echo "복사: AGENTS.md"
fi
rm -f "$tmp"
for f in PLAN.md DECISIONS.md HANDOFF.md; do copy "$KIT/templates/$f" "$f"; done
mkdir -p .agents/skills
for d in "$KIT"/.agents/skills/*; do copy "$d" ".agents/skills/$(basename "$d")"; done
[ -d .git ] || git init -q
for p in .venv/ __pycache__/ .pytest_cache/ .cache/ .kit_start; do grep -qxF "$p" .gitignore 2>/dev/null || echo "$p" >> .gitignore; done
SRC="$(git -C "$KIT" remote get-url origin 2>/dev/null || echo "$KIT")@$(git -C "$KIT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo
echo "다음 순서:"
echo "  python3 $KIT/tools/checkpoint.py start --minutes <제한분>   # 시작 시각 기록"
echo "  python3 $KIT/tools/preflight.py && python3 $KIT/tools/scan.py"
echo "  git add -A && git commit -m \"chore: 공개 하네스 적용 ($SRC) — 작업 지침·템플릿·스킬\""
echo "  제출 직전: cp $KIT/templates/SUBMIT.md SUBMIT.md (과제가 정한 이름이 있으면 그 이름)"
