# personal-harness

코딩 에이전트(Codex 등)와 함께 README 기반 업무 과제를 수행할 때 쓰는 개인 작업 지침·문서 템플릿·점검 도구.
**과제 해답이나 특정 과제용 코드는 들어 있지 않다.** 도구는 진단·검증용이며 표준 라이브러리만 쓴다(Python 3.8+).
과제 유형(데이터 처리, 기존 코드 수정, 서비스·도구 구현, 문서 기반 응답, 분석 보고)을 가리지 않도록 만들었다. 과제 안내가 정한 파일명·형식이 항상 우선한다.

## 구성
| 경로 | 내용 |
|---|---|
| `AGENTS.md` | Codex 작업 지침: 원칙 4개, 환경 규칙, 증거 규칙, 체크포인트, 담당자 질문 규칙, 문서 규칙 |
| `templates/` | PLAN · DECISIONS · HANDOFF · SUBMIT 골격 |
| `tools/preflight.py` | 환경 3분 점검(Python·패키지·명령·시간 파싱 함정·git·0.0.0.0) |
| `tools/scan.py` | 작업 폴더 첫 파악: 과제 안내 핵심 줄, 기존 코드·테스트·실행 명령, 데이터·문서 목록(과제 유형 판별용) |
| `tools/eda.py` | 데이터 첫 파악(CSV·TSV·JSON·JSONL·XLSX·로그): 결측·고유값·표기 흔들림·형식 모양·범위·중복, 질문 거리 |
| `tools/check_submit.py` | 제출 직전 점검: 필수 파일·테스트 수(0개면 exit 2, pytest/unittest/npm/go 자동 선택)·제출 설명의 세 요소·미커밋·비밀값, 권장(커밋 좌표·태그) |
| `tools/checkpoint.py` | 시작 시각 기록, 경과·남은 시간, 지금 단계(순서만, 시간 배분은 정하지 않음) |
| `.agents/skills/` | 단계별 스킬: `kickoff`(시작 파악), `interview-prep`(질문 후보), `plan-check`(PLAN 검토), `design-review`(구조안 검토만), `build-unit`(테스트 먼저 단위 구현), `unit-explain`(단위 설명), `subagent-brief`(서브에이전트 지시서), `handoff`(상태 기록), `independent-check`(독립 재계산), `review-only`(고치지 않는 리뷰), `scope-check`(요구↔변경 대조), `submit-docs`(제출 설명), superpowers 3종 |
| `WORKFLOW.md` | 작업 순서와 단계별 스킬 |
| `SOURCES.md` | 참고·차용 출처와 라이선스 |

## 사용 (작업 폴더 루트에서)
```bash
git clone --depth 1 <이 저장소 URL> ~/.kit     # 작업 폴더가 홈이면 숨김 폴더로
bash ~/.kit/setup.sh                 # AGENTS.md·템플릿·스킬 복사(기존 파일은 덮어쓰지 않음)
python3 ~/.kit/tools/checkpoint.py start --minutes <제한분>
python3 ~/.kit/tools/preflight.py
python3 ~/.kit/tools/scan.py
python3 ~/.kit/tools/eda.py <데이터 파일…>      # 데이터가 있을 때
codex                               # 첫 프롬프트: "AGENTS.md를 읽고 확인한 규칙 5줄만 요약해. 사용 가능한 스킬 이름도."
# ... 제출 전
python3 ~/.kit/tools/check_submit.py <필수 제출물...>
```

## 테스트
`python3 -m pytest -q tests` (또는 `python3 -m unittest discover -s tests`)
