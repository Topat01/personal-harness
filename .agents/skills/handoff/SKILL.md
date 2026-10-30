---
name: handoff
description: 작업 상태를 HANDOFF.md에 짧게 갱신해, 대화가 길어지거나 새 세션으로 옮길 때 맥락을 잃지 않게 한다. 작업 중간 점검 때, 대화 압축 전, 세션을 바꾸기 전, 제출 직전에 쓴다.
---

# handoff

## 절차
1. `git log --oneline -10`, `git status --short`, 마지막 테스트 결과를 확인한다.
2. `HANDOFF.md`를 아래 형식으로 덮어쓴다(30줄 이내).

```
STATE: 합의 → 골격 → E2E v0 → 검증 → 제출  (현재: )
완료: (커밋 해시와 함께)
미완:
다음 3단계:
실행: 
테스트: 
확인한 조건 요약: C1 … (PLAN.md 참조)
알려진 위험·미해결:
```
3. 새 세션에서는 "AGENTS.md, PLAN.md, HANDOFF.md를 읽고 '다음 3단계'의 첫 단계부터"로 시작한다.
