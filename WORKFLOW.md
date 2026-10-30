# 작업 흐름

코딩 에이전트와 README 기반 업무 과제를 할 때의 기본 순서와, 단계별로 쓰는 스킬이다. 판단·요구 확인·최종 문장은 사람이 맡는다.

| 단계 | 사람 | 에이전트에게 |
|---|---|---|
| 0 준비 | `git clone --depth 1 <저장소> ~/.kit && bash ~/.kit/setup.sh` → `git status --short` 확인 → 하네스 적용 커밋 | — |
| 1 파악 | 과제 안내 정독 | `kickoff` 스킬 |
| 2 요구 확인 | 요청자에게 구체적인 것부터 하나씩 확인, 사례를 들어 질문. 답은 PLAN.md "확인한 조건"에 기록 | `interview-prep` 스킬(질문 후보) |
| 3 합의 | PLAN 작성, 요청자에게 이해한 내용 확인 | `plan-check` 스킬 → 커밋 |
| 4 설계 | 구조안 작성 | `design-review` 스킬 |
| 5 구현 | 단위마다 목표·근거·경계·완료 조건 정하기 | `build-unit` → `unit-explain` → DECISIONS 기록 → 커밋 |
| 5 구현(긴 작업) | 맡길 범위 정하기 | `subagent-brief` 스킬 |
| 5 중간 | 필수 산출물이 처음 갖춰지면 태그 | `handoff` 스킬 |
| 6 검증 | 비교할 핵심 결과 정하기 | `independent-check`, `review-only` 스킬 |
| 7 범위 정리 | 제거할 것 결정 → 기능 동결 | `scope-check` 스킬 |
| 8 마무리 | 판단 문장 직접 작성, 실행 화면 직접 확인 | `submit-docs` 스킬 → `check_submit.py` |
| 막힘 | 같은 오류 2회면 멈춤 | `systematic-debugging` 스킬 |

도구 스크립트가 동작하지 않으면 고치지 않고 같은 내용을 셸 명령으로 대신한다.
