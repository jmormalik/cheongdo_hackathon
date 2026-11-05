# 기여 및 협업 규칙

이 문서는 해커톤 P0 구현에서 세 명이 충돌 없이 병렬 작업하기 위한 규칙이다. 제품 범위는 [`PRD.md`](PRD.md), 기술 요구사항은 [`TRD.md`](TRD.md), 구현 설계는 [`TDD.md`](TDD.md)를 기준으로 한다.

## 작업 환경과 브랜치

각 기여자는 자신의 컴퓨터에 저장소를 별도로 clone한다. `idation`은 통합 전용 브랜치이며, 누구도 직접 푸시하지 않고 PR 병합으로만 변경한다.

| 역할 | 브랜치 | 소유 경로 |
| --- | --- | --- |
| J: 런타임·에이전트 | `feature/runtime-agent` | `app/api/`, `app/agent/`, `app/contracts/`, `infra/`, `Dockerfile` |
| T: 데이터·근거 | `feature/data-evidence` | `app/data/`, `fixtures/`, `tests/data/` |
| S: UI | `feature/ui` | `web/` 또는 `app/ui/`, UI 테스트 |

위 경로는 구현 시작 시 생성한다. 새 공유 경로 또는 루트 설정 파일이 필요하면 J·T·S가 먼저 소유자를 정한다.

## J·T·S 역할별 할 일

세 역할은 아래 순서에 맞춰 병렬로 작업한다. 각 담당자는 자신의 소유 경로 밖을 수정해야 하면 먼저 소유자에게 변경을 요청한다.

### J: 런타임·에이전트

1. `app/contracts/`에 안내 요청·응답, 질문 SSE 이벤트, 오류 상태의 공유 계약을 먼저 만든다.
2. FastAPI 앱의 입력 검증, `/api/guidance`, `/api/questions`, `/healthz` 골격을 만든다.
3. `GitHubCopilotAgent`에 `GetCropGuidance`, `GetLocalWeather`만 등록하고 shell·파일·URL·MCP 기능이 노출되지 않게 구성한다.
4. 모델·도구 결과가 근거 검증을 통과한 뒤에만 SSE `result`를 반환하게 만든다.
5. `Dockerfile`, `infra/`, `azd` 설정, Container Apps 비밀 주입, 비식별 실행 로그와 리비전 복구 방식을 준비한다.

**인계 산출물:** 계약 파일, mock SSE 서버, 실행 방법, 필요한 환경 변수 이름과 비밀 전달 경계. SDK·SSE 최소 동작 검증 결과는 `TRD.md`의 TQ-001·003·010 해소 근거로 기록한다.

### T: 데이터·근거

1. `GuidanceEnvelope` 계약에 맞춰 재배 안내·날씨 어댑터의 입력과 출력을 구현한다.
2. 감(청도 반시), 단감, 미나리, 복숭아, 포도용 fixture를 `fixtures/`에 추가한다.
3. fixture마다 `데모 예시 데이터—실시간 정보 아님`, 출처 상태, 기준일, 조회 시각, 적용 범위와 주의사항을 포함한다.
4. 출처 ID·URL·기준일이 없는 작업 항목을 제거하는 근거 검증 테스트를 작성한다.
5. 실제 자료·날씨 출처가 검증되기 전에는 외부 크롤링이나 최신 자료 표현을 추가하지 않는다.

**인계 산출물:** fixture 데이터, 어댑터, 성공·부분 성공·빈 결과·오래된 자료·도구 오류 표본, 데이터 계약 테스트. 실제 자료를 추가할 때는 PRD Q-001~003의 검증 기록도 함께 갱신한다.

### S: UI

1. 공유 계약의 mock 데이터를 사용해 작물·생육 단계·지역 선택과 주간 안내 화면을 만든다.
2. `dataKind=fixture`일 때 카드보다 먼저 `데모 예시 데이터—실시간 정보 아님`을 표시한다.
3. 작업 카드에 이유, 주의사항, 출처 URL, 기준일, 조회 시각과 "근거 보기"를 표시한다.
4. SSE `status`, `result`, `error`, `complete` 이벤트를 처리하고, 내부 추론·원시 모델 출력은 표시하지 않는다.
5. 일시적 오류(재시도), 입력 오류(입력 변경), 터미널 오류(지원 문의)를 구분하고, 모바일에서 핵심 흐름과 Asia/Seoul 주간 날짜를 확인한다.

**인계 산출물:** mock 기반 UI, 상태별 화면 캡처 또는 시연 방법, UI 테스트. 실제 API 연결 전에는 계약 변경을 직접 만들지 않고 런타임·에이전트 담당자에게 요청한다.

### 순환 병합과 최종 시연

- J의 PR은 T가 검토·병합하고, T의 PR은 S가 검토·병합하며, S의 PR은 J가 검토·병합한다.
- 병합하는 사람은 소유 경로·PRD/TRD/TDD 참조·검증 결과를 확인한다.
- 데이터 어댑터, UI, 실제 Agent/Copilot 연결, Azure 배포는 위 PR 순서에 맞춰 병합한다.
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
- `app/contracts/`, `infra/`, `Dockerfile`, 루트 설정 파일은 런타임·에이전트 담당자가 소유한다.
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

1. 런타임·에이전트 담당자가 API/SSE 계약과 mock 서버 골격을 병합한다.
2. 데이터·근거 담당자가 fixture와 자료 어댑터를 계약에 연결한다.
3. UI 담당자가 계약을 소비하는 화면과 상태 표시를 연결한다.
4. 실제 Copilot SDK·Agent Framework 최소 동작을 연결한다.
5. Azure Container Apps 배포와 공개 URL을 검증한다.

통합 전에는 변경 범위에 맞는 테스트와 `git diff --check`를 실행한다. P0에서는 특히 fixture 표시 문구, 출처·기준일, 오류 분류, 질문 원문 미기록, 허용 도구 외 기능 미노출을 함께 확인한다.
