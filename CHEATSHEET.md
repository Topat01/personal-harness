# 순서와 한 줄 호출 (기억이 안 날 때 이 파일만 보기)

스킬은 Codex에게 "○○ 스킬로 …"라고 부른다. 판단·질문·최종 문장은 사람이 한다.

| 단계 | 사람 | Codex에게 |
|---|---|---|
| 0 준비 | `git clone --depth 1 <저장소> ~/.kit && bash ~/.kit/setup.sh` → `git status --short` 확인 → 하네스 커밋 | — |
| 1 읽기 | README 직접 정독 | `kickoff 스킬 실행해` |
| 2 묻기 | 후보 중 골라 **사소한 것부터 하나씩**, 실제 사례로. 답은 PLAN.md "확인한 조건"에 내가 적기 | `interview-prep 스킬로 질문 후보 만들어` |
| 3 합의 | PLAN 5칸 작성, 담당자에게 "이렇게 이해했는데 맞나요?" | `plan-check 스킬로 PLAN.md 봐 줘` → 커밋 |
| 4 설계 | 내 구조안 5줄 먼저 | `design-review 스킬로 이 구조안 검토해: …` |
| 5 짓기 | 목표·근거(C번호)·틀리기 쉬운 곳·완료 조건을 정해서 | `build-unit 스킬로: 목표 … / 근거 C… / 경계 … / 완료 …` → `unit-explain 스킬로 설명해` → 내 말로 DECISIONS → 커밋 |
| 5 짓기(긴 일) | 맡길 일 정하기 | `subagent-brief 스킬로 이 작업 서브에이전트에 맡겨: …` |
| 5 중간 | 제출물이 처음 다 갖춰지면 `git tag submittable-v1` | `handoff 스킬로 HANDOFF.md 갱신해` |
| 6 검증 | 비교할 핵심 결과 1~3개 정하기 | `independent-check 스킬로 …를 다시 계산해` / `review-only 스킬로 리뷰만 해` |
| 7 줄이기 | 지울 것 고르기 → 기능 동결 | `scope-check 스킬 실행해` |
| 8 쓰기 | 판단 문장은 내가 고치기, 화면 직접 확인, DECISIONS 다시 읽기 | `submit-docs 스킬로 제출 설명 초안 써` → `check_submit.py 돌려서 결과만 보고해` |
| 막힘 | 같은 오류 2회면 멈춤 | `systematic-debugging 스킬로 원인 후보와 확인 방법만` |

도구 스크립트가 안 돌면 고치지 말고: "같은 내용을 셸 명령으로 대신해".
서술형: **정**정 → **결**론(근거·버린 안) → **검**증 → **약**점(파일·함수 → 파급 → 다음).
