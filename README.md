# personal-harness

코딩 에이전트(Codex 등)와 함께 README 기반 업무 과제를 수행할 때 쓰는 개인 작업 지침·문서 템플릿·점검 도구.
**과제 해답이나 특정 과제용 코드는 들어 있지 않다.** 도구는 진단·검증용이며 표준 라이브러리만 쓴다(Python 3.8+).
과제 유형(데이터 처리, 기존 코드 수정, 서비스·도구 구현, 문서 기반 응답, 분석 보고)을 가리지 않도록 만들었다. 과제 안내가 정한 파일명·형식이 항상 우선한다.

## 구성
| 경로 | 내용 |
|---|---|
| `AGENTS.md` | 에이전트 작업 지침: 원칙 6개, 역할, 진행 순서, **매 단계 쉬운 말 설명 규칙**, 가벼운 테스트·검증, 서비스형 결과물 점검, 환경 규칙 |
| `templates/SPEC.md` | 만들어야 하는 것: 필수 산출물·실행 환경, 규칙(H), 요구(R), 담당자에게 확인할 열린 것(Q)과 답 |
| `templates/NOTES.md` | 작업 노트 한 장: 과제 한 문장, 확인한 것, 판단 기준과 모듈 지도, 대표 흐름, 단계별 설명, 테스트·재현, 엣지케이스·AI 오류, 예상 질문 |
| `tools/preflight.py` | 환경 3분 점검(Python·패키지·명령·시간 파싱 함정·git·0.0.0.0) |
| `tools/scan.py` | 작업 폴더 첫 파악: 과제 안내 핵심 줄, 기존 코드·테스트·실행 명령, 데이터·문서 목록(과제 유형 판별용) |
| `tools/eda.py` | 데이터 첫 파악(CSV·TSV·JSON·JSONL·XLSX·로그): 결측·고유값·표기 흔들림·형식 모양·범위·중복, 질문 거리 |
| `tools/check_submit.py` | 제출 직전 점검: 필수 파일·테스트 수(0개면 exit 2, pytest/unittest/npm/go 자동 선택)·과제 지시문 README 변경 여부(처음 들어온 커밋 기준)·지시문에 언급된 산출물 파일·미커밋·비밀값, 권장(태그·README 미커밋), `--docker`로 이미지 빌드 확인(docker가 없으면 NOT_RUN 안내) |
| `.agents/skills/` | `kickoff`(시작 파악·SPEC 작성), `scaffold`(서비스 뼈대), `engine`(핵심 로직·검증 함수·지표), `final-docs`(요구 문서·예상 질문·설명 줄 점검) |
| `docs/ALGORITHMS.md` | 문제 꼴별 알려진 방법과 평가 함정(이상 감지, 원인 찾기, 경로, 커버리지, 스케줄링, 근무표, 배정, 추천, 블랙박스 최적화 등) |
| `SOURCES.md` | 참고·차용 출처와 라이선스 |

## 사용 (작업 폴더 루트에서)
```bash
git clone --depth 1 <이 저장소 URL> ~/.kit     # 숨김 폴더로(작업 폴더가 홈이어도 과제 파일과 섞이지 않게)
bash ~/.kit/setup.sh                 # AGENTS.md·템플릿·스킬 복사(기존 파일은 덮어쓰지 않음)
python3 ~/.kit/tools/preflight.py
python3 ~/.kit/tools/scan.py
python3 ~/.kit/tools/eda.py <데이터 파일…>      # 데이터가 있을 때
codex                               # 첫 요청: "kickoff 스킬 실행해"
# ... 제출 전
python3 ~/.kit/tools/check_submit.py <필수 제출물...> [--docker]
```

하네스를 다른 경로로 다시 받았다면 작업 폴더의 `AGENTS.md`·`.agents/`를 지우고 `setup.sh`를 다시 실행한다(이미 있는 파일은 건너뛰므로).

## 테스트
`python3 -m pytest -q tests` (또는 `python3 -m unittest discover -s tests`)
