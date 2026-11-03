#!/usr/bin/env bash
# 작업 폴더 루트에서 실행: bash <kit>/setup.sh
# 이미 있는 파일은 덮어쓰지 않는다(과제가 같은 이름을 요구하면 과제 쪽을 우선).
set -euo pipefail
KIT="$(cd "$(dirname "$0")" && pwd -P)"
HERE="$(pwd -P)"
HOME_REAL="$(cd "$HOME" 2>/dev/null && pwd -P || echo "$HOME")"
copy() { if [ -e "$2" ]; then echo "건너뜀(이미 있음): $2"; else cp -R "$1" "$2"; echo "복사: $2"; fi; }
tmp="$(mktemp)"; sed -e "s|~/kit|$KIT|g" -e "s|<kit>|$KIT|g" "$KIT/AGENTS.md" > "$tmp"
if [ -e AGENTS.md ] && grep -qF "# 작업 지침 (코딩 에이전트용)" AGENTS.md; then
  echo "건너뜀(이미 적용됨): AGENTS.md"
elif [ -e AGENTS.md ]; then
  printf '\n\n' >> AGENTS.md; cat "$tmp" >> AGENTS.md; echo "덧붙임: AGENTS.md (기존 내용 뒤)"
else
  cp "$tmp" AGENTS.md; echo "복사: AGENTS.md"
fi
rm -f "$tmp"
copy "$KIT/templates/NOTES.md" NOTES.md
mkdir -p .agents/skills
for d in "$KIT"/.agents/skills/*; do copy "$d" ".agents/skills/$(basename "$d")"; done
# 스킬 안의 도구 경로를 실제 하네스 경로로
find .agents/skills -name 'SKILL.md' -exec sed -i.bak -e "s|~/kit|$KIT|g" -e "s|<kit>|$KIT|g" {} \; -exec rm -f {}.bak \;
[ -d .git ] || git init -q
ign() { grep -qxF "$1" .gitignore 2>/dev/null || echo "$1" >> .gitignore; }
for p in .venv/ __pycache__/ .pytest_cache/ .cache/; do ign "$p"; done
# 하네스를 작업 폴더 안에 clone했다면 하네스 폴더는 커밋하지 않는다(중첩 저장소 방지)
case "$KIT/" in "$HERE"/*) ign "${KIT#$HERE/}/" ;; esac
# 작업 폴더가 홈 디렉터리면 환경 파일·설정 폴더는 커밋하지 않는다
if [ "$HERE" = "$HOME_REAL" ]; then
  for p in .bash_logout .bashrc .profile .bash_history .sudo_as_admin_successful .viminfo .lesshst .python_history .wget-hsts .gitconfig .config/ .local/ .npm/ .codex/ .ssh/ .cache/; do ign "$p"; done
fi
SRC="$(git -C "$KIT" remote get-url origin 2>/dev/null || echo "$KIT")@$(git -C "$KIT" rev-parse --short HEAD 2>/dev/null || echo unknown)"
echo
echo "다음 순서:"
echo "  python3 $KIT/tools/preflight.py && python3 $KIT/tools/scan.py"
echo "  git status --short     # 과제와 무관한 파일이 보이면 .gitignore에 추가"
echo "  git add AGENTS.md NOTES.md .agents .gitignore && git commit -m \"chore: 공개 하네스 적용 ($SRC)\""
echo "  (README.md 등 과제 파일이 아직 커밋 안 됐으면 받은 그대로 먼저 커밋)"
echo "  codex 첫 요청: kickoff 스킬 실행해"
