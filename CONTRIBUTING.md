# 기여 및 협업 규칙

이 문서는 해커톤 P0 구현에서 세 명이 충돌 없이 병렬 작업하기 위한 규칙이다. 제품 범위는 [`PRD.md`](PRD.md), 기술 요구사항은 [`TRD.md`](TRD.md), 구현 설계는 [`TDD.md`](TDD.md)를 기준으로 한다.

## 작업 환경과 브랜치

각 기여자는 자신의 컴퓨터에 저장소를 별도로 clone한다. `idation`은 통합 전용 브랜치이며, 누구도 직접 푸시하지 않고 PR 병합으로만 변경한다.

| 역할 | 브랜치 | 소유 경로 |
| --- | --- | --- |
| J: 런타임·에이전트 | `feature/runtime-agent` | `app/main.py`, `app/api/`, `app/agent.py`, `app/contracts/`, `AppHost/`, `Dockerfile` |
| T: 데이터·근거 | `feature/data-evidence` | `app/guidance.py`, `app/data/`, `fixtures/`, `tests/data/` |
| S: UI | `feature/ui` | `app/static/`, UI 테스트 (별도 빌드 사용 시 `web/`) |

경로는 TDD의 제안 구조와 맞춘 구현 예정 경로다. UI에 빌드가 필요하면 web/에서 작업하고 산출물만 app/static/으로 제공한다. 새 공유 경로 또는 루트 설정 파일이 필요하면 J·T·S가 먼저 소유자를 정한다.

## J·T·S 역할별 할 일

세 역할은 아래 순서에 맞춰 병렬로 작업한다. 각 담당자는 자신의 소유 경로 밖을 수정해야 하면 먼저 소유자에게 변경을 요청한다.

### J: 런타임·에이전트

1. TDD의 Guidance·Card·Source·Answer와 질문 `{scenarioId, cardId?, question}`, SSE 계약을 `app/contracts/`에 정의한다.
2. FastAPI의 `GET /api/guidance`, `POST /api/questions`, `GET /healthz`와 정적 UI 제공을 구현한다.
3. `GitHubCopilotAgent`에 `GetCropGuidance` 하나만 등록하고 실제 Copilot SDK 모델 연결·도구 호출·컨텍스트 처리를 먼저 검증한다. shell·임의 파일·URL·MCP 기능은 차단한다.
4. 실제 실행 이벤트를 SSE 진행 상태에 연결하고, 근거 검증 후에만 결과를 표시한다. 범위 밖 질문·시간 초과·취소·슬롯/세션 정리를 구현한다.
5. `Dockerfile`, `AppHost/`, Container Apps 비밀 주입·공개 접근·로그·리비전 복구를 준비한다. 단일 컨테이너를 Aspire로 실행·배포하며 추가 Azure 서비스를 점수 목적으로 넣지 않는다.

**인계 산출물:** 공유 계약, 개발용 mock SSE, 실행 방법, 환경 변수 이름, 실제 SDK 검증 기록. mock은 UI 병행 개발용이며 실제 연동 증거가 아니다. 검증은 TRD 4·5·7절에 기록한다.

### T: 데이터·근거

1. 감·청도·수확 후 점검 시나리오 `cheongdo-persimmon-postharvest` 하나와 카드 최대 3개를 준비한다. 날씨와 추가 작물은 P1이다.
2. `app/guidance.py`에서 자료 조회와 근거 ID 검증을 구현한다. 실제 사용 자료는 `app/data/guidance.json`, 테스트 예시는 `fixtures/`에 둔다.
3. `reviewed_static` 자료는 원문 제목·URL·적용 범위·검토일·이용 조건을 확인한다. 발행일을 모르면 null로 두며 검토일로 대체하지 않는다.
4. `fixture`는 가짜 원문 링크 없이 예시 ID를 사용한다. 표시 문구는 `데모 예시 데이터—실제 재배 권고 및 실시간 정보 아님`이다.
5. 미등록 근거 ID 차단, 실제 자료와 예시 구분, 빈 자료 처리, 발행일 미상 허용을 검사한다. 실제 원문 검토 결과는 PRD 4절 정책에 맞춰 데이터에 기록한다.

**인계 산출물:** 시나리오 JSON, 조회·검증 함수, 정상·빈 결과·잘못된 참조 표본과 검사 결과. 가상 데이터로 실제 농업 정보의 정확성을 입증했다고 주장하지 않는다.

### S: UI

1. 로그인 없는 `/`와 `/demo`에 고정 조건과 점검 목록 버튼, 최대 3개 카드·근거 상세를 제공한다. 작물·단계·지역 선택 UI는 만들지 않는다.
2. fixture 배너를 카드와 답변보다 먼저 표시한다. 실제 자료의 발행일 미상·검토일을 구분하며 AI 답변에는 `AI 생성 설명`을 표시한다.
3. 카드에서 `cardId`를 전달해 이유를 질문하게 하고 추천 질문 3개와 자유 질문을 지원한다.
4. POST fetch 스트림으로 `status`, `result`, `error`, `complete`를 처리한다. 네트워크 청크를 이벤트 하나로 가정하지 않는다. 검증 전 모델 텍스트나 내부 추론은 표시하지 않는다.
5. 중복 제출 방지·취소·수동 재시도·단절/오류 처리를 구현한다. AI 실패에도 카드는 유지한다. 모바일 390px, 키보드 Tab/Enter, 입력 label·포커스·상태 안내를 확인한다.

**인계 산출물:** mock 기반 UI와 실제 API 연결 결과, 정상·오류·취소 검증. 자료 확인 과업의 수동/앱 수행 시간과 실패를 측정해 PRD 7·9절에 기록하되, 측정하지 않은 효과는 주장하지 않는다.

### 순환 병합과 최종 시연

- J의 PR은 T가 검토·병합하고, T의 PR은 S가 검토·병합하며, S의 PR은 J가 검토·병합한다.
- 병합하는 사람은 소유 경로·PRD/TRD/TDD 참조·검증 결과를 확인한다.
- 기능 통합 순서는 아래 병합 순서를 따른다. 순환 검토 담당 규칙은 기술 의존성의 순서를 뜻하지 않는다.
- 최종 공개 URL 시연은 J·T·S가 각각 자신의 경계를 확인한 뒤 함께 진행한다.
- 충돌이 다른 사람의 소유 경로나 공유 계약에 있으면 PR 작성자와 해당 소유자가 함께 해결한다.

## 시작 방법

각 담당자는 최신 통합본에서 자신의 기능 브랜치를 생성한다.

```bash
git clone git@github.com:jmormalik/cheongdo_hackathon.git
cd cheongdo_hackathon
git fetch origin
git switch --track origin/idation
git switch -c feature/runtime-agent
git push -u origin feature/runtime-agent
```

이미 원격 브랜치가 있다면 새 브랜치를 만들지 않고 추적 브랜치로 전환한다.

```bash
git fetch origin
git switch --track origin/feature/runtime-agent
```

각 명령의 브랜치 이름은 자신의 역할에 맞게 바꾼다.

## 파일 소유권과 계약 변경

- 각 담당자는 자신의 소유 경로만 직접 수정한다.
- `app/main.py`, `app/contracts/`, `AppHost/`, `Dockerfile`, 루트 설정 파일은 런타임·에이전트 담당자가 소유한다.
- T·S가 공유 계약 또는 배포 구성을 바꿔야 하면, 먼저 이슈 또는 PR 댓글로 변경 이유·영향·필요한 필드를 J에게 제안한다.
- API·SSE 계약 변경은 구현 전에 J가 계약 파일을 갱신하고 T·S에게 알린다.
- 제품 범위, 기술 의무, 설계 결정이 바뀌면 각각 PRD, TRD, TDD를 갱신한 뒤 관련 구현 PR에 참조한다.

## 커밋과 PR

1. 하나의 PR은 하나의 경계 또는 하나의 계약 변경만 포함한다.
2. PR 대상 브랜치는 항상 `idation`이다.
3. PR 설명에는 변경 목적, PRD/TRD/TDD 참조, 실행한 검증, 미해결 사항을 적는다.
4. 비밀 값, 사용자 질문 원문, 식별 가능한 입력, 실제 `.env` 파일은 커밋하지 않는다.
5. 순환 병합 담당자가 최소 한 명의 관련 담당자 검토 또는 충돌 영향 확인 후 병합한다.

## 통합 전 동기화

PR을 병합하기 전 자신의 브랜치에 최신 `idation`을 반영한다.

```bash
git fetch origin
git rebase origin/idation
git push --force-with-lease
```

`--force-with-lease`는 자신의 기능 브랜치에만 사용한다. `idation`에는 강제 푸시하지 않는다.

리베이스 충돌이 자신의 소유 경로에 있으면 직접 해결한다. 다른 담당자의 소유 경로나 공유 계약에서 충돌하면 임의로 의미를 바꾸지 말고, 해당 소유자와 PR 검토 담당자에게 알린다.

## 병합 순서와 최소 검증

기본 병합 순서는 다음과 같다.

1. J가 최소 서버·healthz·AppHost를 먼저 구성해 Azure 공개 배포 가능 여부를 확인한다.
2. J가 같은 컨테이너에서 실제 SDK·자료 도구 하나의 실행을 검증하고 API/SSE 계약을 공유한다. 이동안 T의 자료와 S의 mock UI 작업은 병행한다.
3. T의 자료·근거 검증과 S의 UI를 공유 계약에 연결한다.
4. 실제 질문·SSE·오류·취소를 연결하고 같은 Azure 앱으로 재배포한다.
5. 새 시크릿 세션에서 핵심 동선을 3회 반복하고 실제 기술 실행 증거와 생산성 관찰 결과를 기록한다.

통합 전에는 변경에 맞는 검사와 `git diff --check`를 실행한다. fixture 표시, 출처 ID, 발행일 미상 처리, 범위 밖 질문, AI 생성 표시, 질문 원문 미기록, 허용 외 기능 차단, 시간 초과·취소의 자원 정리를 확인한다. 모델 토큰 스트리밍과 SSE 진행 상태는 구분해 보고한다.

현재 기준은 PRD v0.4·TRD v0.4·TDD v0.3이다. 역할은 담당 범위를 나타내며 실제 개인 배정이나 구현 완료를 뜻하지 않는다. 공용 지침은 agent.md를 함께 따른다.
